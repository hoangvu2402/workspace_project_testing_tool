"""
VectorDB: Vector Database & Semantic Search cho Automation Control Center.

Cung cap:
- Luu tru embeddings cua locators, templates, test cases, use cases
- Tim kiem ngu nghia (semantic search) thay vi tim kiem van ban thong thuong
- Tich hop voi AI pipeline de cai thien RAG (Retrieval Augmented Generation)
- Tu dong index du lieu khi project thay doi

Ho tro backends:
- ChromaDB (mac dinh, nhe, khong can server)
- Fallback: in-memory cosine similarity (khi ChromaDB khong kha dung)
"""

import json
import hashlib
import math
from pathlib import Path
from utils.logger import log

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    log.info("[VectorDB] chromadb chua duoc cai dat. Su dung in-memory backend.")

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    log.info("[VectorDB] sentence-transformers chua cai. Su dung hash-based embedding.")


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

class EmbeddingEngine:
    """Tao embeddings tu text. Ho tro sentence-transformers va hash fallback."""

    _model = None
    _model_name = ""

    @classmethod
    def get_model(cls, model_name: str = "all-MiniLM-L6-v2"):
        if HAS_SENTENCE_TRANSFORMERS:
            if cls._model is None or cls._model_name != model_name:
                log.info(f"[VectorDB] Loading embedding model: {model_name}...")
                cls._model = SentenceTransformer(model_name)
                cls._model_name = model_name
            return cls._model
        return None

    @classmethod
    def embed(cls, texts: list, model_name: str = "all-MiniLM-L6-v2") -> list:
        """Tao embeddings cho danh sach text.

        Returns: list of embedding vectors (list of floats).
        """
        if not texts:
            return []

        model = cls.get_model(model_name)
        if model is not None:
            embeddings = model.encode(texts, show_progress_bar=False)
            return [emb.tolist() for emb in embeddings]

        # Fallback: hash-based pseudo-embeddings (384 dims)
        return [cls._hash_embed(t) for t in texts]

    @classmethod
    def embed_single(cls, text: str, model_name: str = "all-MiniLM-L6-v2") -> list:
        results = cls.embed([text], model_name)
        return results[0] if results else []

    @classmethod
    def _hash_embed(cls, text: str, dims: int = 384) -> list:
        """Pseudo-embedding dua tren hash. Khong co semantic meaning thuc su
        nhung dam bao text giong nhau => vector giong nhau."""
        h = hashlib.sha512(text.lower().encode("utf-8")).hexdigest()
        # repeat hash to fill dims
        extended = (h * (dims // len(h) + 1))[:dims * 2]
        vec = []
        for i in range(0, dims * 2, 2):
            val = int(extended[i:i+2], 16) / 255.0 - 0.5
            vec.append(val)
        # normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


# ---------------------------------------------------------------------------
# Cosine similarity (for in-memory fallback)
# ---------------------------------------------------------------------------

def cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# In-memory Vector Store (fallback khi khong co ChromaDB)
# ---------------------------------------------------------------------------

class InMemoryVectorStore:
    """Vector store don gian dung list. Fallback khi ChromaDB khong kha dung."""

    def __init__(self, name: str = "default"):
        self.name = name
        self._docs = []       # list of {"id": str, "text": str, "embedding": list, "metadata": dict}

    def add(self, doc_id: str, text: str, embedding: list, metadata: dict = None):
        # Remove existing doc with same id
        self._docs = [d for d in self._docs if d["id"] != doc_id]
        self._docs.append({
            "id": doc_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {},
        })

    def search(self, query_embedding: list, top_k: int = 5) -> list:
        """Tra ve top_k documents gan nhat theo cosine similarity.

        Returns: list of {"id": str, "text": str, "score": float, "metadata": dict}
        """
        if not self._docs:
            return []

        scored = []
        for doc in self._docs:
            score = cosine_similarity(query_embedding, doc["embedding"])
            scored.append({
                "id": doc["id"],
                "text": doc["text"],
                "score": score,
                "metadata": doc["metadata"],
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def delete(self, doc_id: str):
        self._docs = [d for d in self._docs if d["id"] != doc_id]

    def clear(self):
        self._docs = []

    def count(self) -> int:
        return len(self._docs)


# ---------------------------------------------------------------------------
# VectorDB main class
# ---------------------------------------------------------------------------

class VectorDB:
    """Vector Database Manager.

    Ho tro:
    - ChromaDB (persistent, semantic search tot)
    - InMemoryVectorStore (fallback, khong can cai them)

    Collections:
    - locators: embeddings cua cac locator elements
    - templates: embeddings cua cac workflow templates
    - test_data: embeddings cua test data records
    - use_cases: embeddings cua use case descriptions
    """

    COLLECTIONS = ["locators", "templates", "test_data", "use_cases"]

    def __init__(self, project_path: str = "", embedding_model: str = "all-MiniLM-L6-v2"):
        self.project_path = project_path
        self.embedding_model = embedding_model
        self._stores = {}        # collection_name -> store
        self._chroma_client = None
        self._use_chroma = HAS_CHROMADB
        self._initialized = False

    def initialize(self, project_path: str = ""):
        """Khoi tao vector database va index du lieu tu project."""
        if project_path:
            self.project_path = project_path

        if not self.project_path:
            log.warning("[VectorDB] Khong co project_path. Skip initialization.")
            return

        log.info(f"[VectorDB] Khoi tao voi backend: {'ChromaDB' if self._use_chroma else 'InMemory'}...")

        if self._use_chroma:
            self._init_chroma()
        else:
            self._init_memory()

        # Index existing project data
        self._index_project_data()
        self._initialized = True
        log.info(f"[VectorDB] Khoi tao thanh cong. Collections: {list(self._stores.keys())}")

    def _init_chroma(self):
        """Khoi tao ChromaDB persistent client."""
        try:
            db_path = str(Path(self.project_path) / ".vector_db")
            self._chroma_client = chromadb.PersistentClient(path=db_path)
            for name in self.COLLECTIONS:
                collection = self._chroma_client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                )
                self._stores[name] = collection
            log.info(f"[VectorDB] ChromaDB khoi tao tai: {db_path}")
        except Exception as e:
            log.warning(f"[VectorDB] ChromaDB loi: {e}. Chuyen sang InMemory.")
            self._use_chroma = False
            self._init_memory()

    def _init_memory(self):
        """Khoi tao InMemory stores."""
        for name in self.COLLECTIONS:
            self._stores[name] = InMemoryVectorStore(name)

    # ------------------------------------------------------------------
    # Index project data
    # ------------------------------------------------------------------

    def _index_project_data(self):
        """Index tat ca locators, templates, test data tu project."""
        p = Path(self.project_path)

        # Index locators
        locators_indexed = self._index_locators(p / "locators")
        log.info(f"[VectorDB] Da index {locators_indexed} locator entries.")

        # Index templates
        templates_indexed = self._index_templates(p / "templates")
        log.info(f"[VectorDB] Da index {templates_indexed} template entries.")

    def _index_locators(self, locators_dir: Path) -> int:
        """Index cac locator files vao vector store."""
        count = 0
        if not locators_dir.exists():
            return 0

        for site_dir in locators_dir.iterdir():
            if not site_dir.is_dir():
                continue
            for loc_file in site_dir.glob("*.json"):
                try:
                    data = json.loads(loc_file.read_text(encoding="utf-8"))
                    for element_name, info in data.items():
                        text = self._locator_to_text(element_name, info, loc_file.stem)
                        doc_id = f"loc_{site_dir.name}_{loc_file.stem}_{element_name}"
                        self._add_document("locators", doc_id, text, {
                            "site": site_dir.name,
                            "page_id": loc_file.stem,
                            "element_name": element_name,
                            "selector": info.get("selector", ""),
                            "type": info.get("type", ""),
                        })
                        count += 1
                except Exception as e:
                    log.debug(f"[VectorDB] Loi index locator {loc_file}: {e}")
        return count

    def _index_templates(self, templates_dir: Path) -> int:
        """Index cac template workflow files vao vector store."""
        count = 0
        if not templates_dir.exists():
            return 0

        for site_dir in templates_dir.iterdir():
            if not site_dir.is_dir():
                continue
            for tpl_file in site_dir.glob("*.json"):
                try:
                    data = json.loads(tpl_file.read_text(encoding="utf-8"))
                    text = self._template_to_text(data, tpl_file.stem)
                    doc_id = f"tpl_{site_dir.name}_{tpl_file.stem}"
                    self._add_document("templates", doc_id, text, {
                        "site": site_dir.name,
                        "file_name": tpl_file.stem,
                        "page_id": data.get("page_id", ""),
                        "url": data.get("url", ""),
                        "step_count": len(data.get("steps", [])),
                    })
                    count += 1
                except Exception as e:
                    log.debug(f"[VectorDB] Loi index template {tpl_file}: {e}")
        return count

    # ------------------------------------------------------------------
    # Text conversion (for embedding)
    # ------------------------------------------------------------------

    @staticmethod
    def _locator_to_text(name: str, info: dict, page_id: str) -> str:
        """Chuyen locator thanh text de tao embedding."""
        parts = [
            f"Element: {name}",
            f"Page: {page_id}",
            f"Selector: {info.get('selector', '')}",
            f"Type: {info.get('type', '')}",
        ]
        if info.get("name"):
            parts.append(f"Label: {info['name']}")
        return " | ".join(parts)

    @staticmethod
    def _template_to_text(data: dict, file_name: str) -> str:
        """Chuyen template thanh text de tao embedding."""
        parts = [
            f"Template: {file_name}",
            f"Page: {data.get('page_id', '')}",
            f"URL: {data.get('url', '')}",
        ]
        steps = data.get("steps", [])
        step_descs = []
        for s in steps[:10]:
            desc = f"{s.get('action', '')} {s.get('id', '')}"
            if s.get("data_key"):
                desc += f" (data: {s['data_key']})"
            step_descs.append(desc)
        if step_descs:
            parts.append(f"Steps: {', '.join(step_descs)}")
        return " | ".join(parts)

    # ------------------------------------------------------------------
    # Document operations (abstract over backends)
    # ------------------------------------------------------------------

    def _add_document(self, collection: str, doc_id: str, text: str, metadata: dict = None):
        """Them document vao collection."""
        store = self._stores.get(collection)
        if store is None:
            return

        if self._use_chroma:
            try:
                embedding = EmbeddingEngine.embed_single(text, self.embedding_model)
                store.upsert(
                    ids=[doc_id],
                    documents=[text],
                    embeddings=[embedding],
                    metadatas=[metadata or {}],
                )
            except Exception as e:
                log.debug(f"[VectorDB] Loi add ChromaDB doc: {e}")
        else:
            embedding = EmbeddingEngine.embed_single(text, self.embedding_model)
            store.add(doc_id, text, embedding, metadata)

    def add_use_case(self, use_case_id: str, text: str, metadata: dict = None):
        """Them use case vao vector DB de tim kiem sau."""
        self._add_document("use_cases", use_case_id, text, metadata or {})
        log.info(f"[VectorDB] Da them use case: {use_case_id}")

    def add_locator(self, site: str, page_id: str, element_name: str, info: dict):
        """Them mot locator vao vector DB."""
        text = self._locator_to_text(element_name, info, page_id)
        doc_id = f"loc_{site}_{page_id}_{element_name}"
        self._add_document("locators", doc_id, text, {
            "site": site,
            "page_id": page_id,
            "element_name": element_name,
            "selector": info.get("selector", ""),
            "type": info.get("type", ""),
        })

    def add_template(self, site: str, file_name: str, data: dict):
        """Them mot template vao vector DB."""
        text = self._template_to_text(data, file_name)
        doc_id = f"tpl_{site}_{file_name}"
        self._add_document("templates", doc_id, text, {
            "site": site,
            "file_name": file_name,
            "page_id": data.get("page_id", ""),
            "url": data.get("url", ""),
        })

    # ------------------------------------------------------------------
    # Semantic Search
    # ------------------------------------------------------------------

    def search(self, query: str, collection: str = "locators",
               top_k: int = 10, min_score: float = 0.3) -> list:
        """Tim kiem ngu nghia trong collection.

        Args:
            query: Text truy van (vd: "nut dang nhap", "form dang ky")
            collection: Ten collection (locators, templates, test_data, use_cases)
            top_k: So ket qua toi da
            min_score: Diem tuong dong toi thieu (0-1)

        Returns:
            list of {"id": str, "text": str, "score": float, "metadata": dict}
        """
        store = self._stores.get(collection)
        if store is None:
            return []

        query_embedding = EmbeddingEngine.embed_single(query, self.embedding_model)

        if self._use_chroma:
            return self._search_chroma(store, query_embedding, top_k, min_score)
        else:
            results = store.search(query_embedding, top_k)
            return [r for r in results if r["score"] >= min_score]

    def _search_chroma(self, collection, query_embedding: list,
                       top_k: int, min_score: float) -> list:
        """Tim kiem trong ChromaDB collection."""
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            output = []
            if results and results["ids"]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # ChromaDB tra ve distance (1 - cosine), chuyen sang score
                    distance = results["distances"][0][i] if results["distances"] else 0
                    score = 1.0 - distance
                    if score >= min_score:
                        output.append({
                            "id": doc_id,
                            "text": results["documents"][0][i] if results["documents"] else "",
                            "score": round(score, 4),
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        })
            return output
        except Exception as e:
            log.warning(f"[VectorDB] Loi search ChromaDB: {e}")
            return []

    def search_similar_locators(self, query: str, top_k: int = 10) -> list:
        """Tim cac locator tuong tu voi query."""
        return self.search(query, "locators", top_k)

    def search_similar_templates(self, query: str, top_k: int = 5) -> list:
        """Tim cac template tuong tu voi query."""
        return self.search(query, "templates", top_k)

    def search_similar_use_cases(self, query: str, top_k: int = 5) -> list:
        """Tim cac use case tuong tu."""
        return self.search(query, "use_cases", top_k)

    # ------------------------------------------------------------------
    # RAG context builder (thay the gather_rag_context cu)
    # ------------------------------------------------------------------

    def build_rag_context(self, query: str, url: str = "",
                          max_locators: int = 10, max_templates: int = 3) -> str:
        """Xay dung RAG context bang semantic search thay vi keyword matching.

        Tra ve text context de chen vao AI prompt.
        """
        if not self._initialized:
            return ""

        context_parts = []

        # Tim locators lien quan
        loc_results = self.search_similar_locators(query, max_locators)
        if loc_results:
            loc_texts = []
            for r in loc_results:
                meta = r.get("metadata", {})
                loc_texts.append(
                    f"  - {meta.get('element_name', r['id'])}: "
                    f"selector={meta.get('selector', 'N/A')}, "
                    f"type={meta.get('type', 'N/A')}, "
                    f"page={meta.get('page_id', 'N/A')} "
                    f"(score: {r['score']:.2f})"
                )
            context_parts.append(
                "=== LOCATORS LIEN QUAN (Semantic Search) ===\n"
                + "\n".join(loc_texts)
            )

        # Tim templates lien quan
        tpl_results = self.search_similar_templates(query, max_templates)
        if tpl_results:
            tpl_texts = []
            for r in tpl_results:
                meta = r.get("metadata", {})
                tpl_texts.append(
                    f"  - {meta.get('file_name', r['id'])}: "
                    f"page={meta.get('page_id', 'N/A')}, "
                    f"steps={meta.get('step_count', '?')} "
                    f"(score: {r['score']:.2f})"
                )
            context_parts.append(
                "=== TEMPLATES LIEN QUAN (Semantic Search) ===\n"
                + "\n".join(tpl_texts)
            )

        # Tim use cases lien quan
        uc_results = self.search_similar_use_cases(query, 3)
        if uc_results:
            uc_texts = [f"  - {r['text'][:200]} (score: {r['score']:.2f})"
                        for r in uc_results]
            context_parts.append(
                "=== USE CASES TUONG TU ===\n" + "\n".join(uc_texts)
            )

        if not context_parts:
            return ""

        return (
            "\n=== RAG CONTEXT (Vector Database Semantic Search) ===\n"
            "Du lieu duoc truy xuat tu vector database dua tren do tuong dong ngu nghia:\n\n"
            + "\n\n".join(context_parts)
            + "\n"
        )

    # ------------------------------------------------------------------
    # Stats & management
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Tra ve thong ke ve vector database."""
        stats = {
            "backend": "ChromaDB" if self._use_chroma else "InMemory",
            "embedding_model": self.embedding_model if HAS_SENTENCE_TRANSFORMERS else "hash-based",
            "initialized": self._initialized,
            "collections": {},
        }
        for name, store in self._stores.items():
            if self._use_chroma:
                try:
                    stats["collections"][name] = store.count()
                except Exception:
                    stats["collections"][name] = 0
            else:
                stats["collections"][name] = store.count()
        return stats

    def reindex(self):
        """Xoa va index lai tat ca du lieu."""
        log.info("[VectorDB] Bat dau reindex...")
        for name in self.COLLECTIONS:
            if self._use_chroma and self._chroma_client:
                try:
                    self._chroma_client.delete_collection(name)
                    self._stores[name] = self._chroma_client.get_or_create_collection(
                        name=name,
                        metadata={"hnsw:space": "cosine"},
                    )
                except Exception:
                    pass
            else:
                if name in self._stores:
                    self._stores[name].clear()

        self._index_project_data()
        log.info("[VectorDB] Reindex hoan tat.")

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def has_semantic_search(self) -> bool:
        """True neu co sentence-transformers (semantic search thuc su)."""
        return HAS_SENTENCE_TRANSFORMERS
