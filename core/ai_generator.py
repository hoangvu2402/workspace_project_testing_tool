"""
AIGenerator: Use Google Gemini to analyze scanned locators and use cases,
then generate/modify locators, templates, test data, and setup scripts.

Techniques applied:
- Filtering truoc AI: pre-filter irrelevant locators before sending
- Semantic chunking: break use case into logical sections
- Multi-stage pipeline: separate AI calls for each artifact type
- Adaptive processing: adjust strategy based on page complexity
- RAG (Retrieval): use existing project artifacts as reference context
"""

import json
import re
import time
from pathlib import Path
from utils.logger import log

try:
    from google import genai
    from google.genai import errors as genai_errors
except ImportError:
    genai = None
    genai_errors = None
    log.warning("google-genai not installed. AI features disabled.")


# ---------------------------------------------------------------------------
# Pre-AI Filtering helpers
# ---------------------------------------------------------------------------

_GENERIC_SELECTORS = {"body", "div", "section", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6"}

def _is_actionable_locator(name: str, info: dict) -> bool:
    """Return True if the locator is likely relevant for test automation."""
    selector = info.get("selector", "")
    loc_type = info.get("type", "")

    # Always keep action-type locators (inputs, buttons, links)
    if loc_type == "action":
        return True

    # Keep info-type if they have a specific selector (id, data-test, name attr)
    if selector.startswith("#") or "[data-test" in selector or "[name=" in selector:
        return True

    # Drop purely generic info selectors (bare tags, generic class chains)
    base_tag = selector.split(">")[-1].strip().split(".")[0].strip()
    if base_tag.lower() in _GENERIC_SELECTORS and loc_type == "info":
        return False

    return True


def filter_locators(locators: dict) -> dict:
    """Remove irrelevant/generic locators to reduce token count for AI."""
    filtered = {k: v for k, v in locators.items() if _is_actionable_locator(k, v)}
    removed = len(locators) - len(filtered)
    if removed:
        log.info(f"[Filter] Loai bo {removed}/{len(locators)} locator khong lien quan.")
    return filtered


# ---------------------------------------------------------------------------
# Semantic Chunking helpers
# ---------------------------------------------------------------------------

def chunk_use_case(text: str) -> dict:
    """Split a use case into logical sections for focused prompts.

    Returns dict with keys: full, main_flow, exception_flows, preconditions,
    postconditions.  Values are the raw text of that section (empty string if
    not found).
    """
    sections = {
        "full": text.strip(),
        "main_flow": "",
        "exception_flows": "",
        "preconditions": "",
        "postconditions": "",
    }

    # Try to find common section headers (Vietnamese & English)
    patterns = {
        "main_flow": r"(?:Main\s*Flow|Luong\s*chinh|Buoc\s*thuc\s*hien)\s*\n(.*?)(?=Exception|Ngoai\s*le|EF\d|Postcondition|Dieu\s*kien\s*sau|Exit|$)",
        "exception_flows": r"(?:Exception\s*Flow|Ngoai\s*le|EF\s*\d)(.*?)(?=Postcondition|Dieu\s*kien\s*sau|Exit|$)",
        "preconditions": r"(?:Precondition|Dieu\s*kien\s*truoc)(.*?)(?=Main|Luong|Buoc|Step|$)",
        "postconditions": r"(?:Postcondition|Dieu\s*kien\s*sau|Exit)(.*?)$",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sections[key] = match.group(1).strip() if match.group(1) else match.group(0).strip()

    return sections


# ---------------------------------------------------------------------------
# RAG helpers
# ---------------------------------------------------------------------------

def gather_rag_context(project_path: str, url: str) -> str:
    """Collect existing project artifacts as reference examples for AI.

    Looks for templates and locators in the same site folder.
    """
    if not project_path:
        return ""

    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc.replace(".", "_") if parsed.netloc else ""
    if not domain:
        return ""

    p = Path(project_path)
    examples = []

    # Existing templates for this site
    tpl_dir = p / "templates" / domain
    if tpl_dir.exists():
        for f in sorted(tpl_dir.glob("*_workflow.json"))[:3]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                examples.append(
                    f"--- Template vi du: {f.name} ---\n"
                    + json.dumps(data, indent=2, ensure_ascii=False)[:1500]
                )
            except Exception:
                pass

    # Existing locators for this site
    loc_dir = p / "locators" / domain
    if loc_dir.exists():
        for f in sorted(loc_dir.glob("*.json"))[:3]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                examples.append(
                    f"--- Locator vi du: {f.name} ---\n"
                    + json.dumps(data, indent=2, ensure_ascii=False)[:1500]
                )
            except Exception:
                pass

    if not examples:
        return ""

    return (
        "\n=== DU LIEU THAM KHAO TU DU AN (RAG) ===\n"
        "Hay tham khao cac file co san trong du an de tao ra ket qua phu hop ve "
        "format, naming convention, va phong cach:\n\n"
        + "\n\n".join(examples)
        + "\n"
    )


# ---------------------------------------------------------------------------
# Main AIGenerator class
# ---------------------------------------------------------------------------

class AIGenerator:
    """Generates test artifacts using Google Gemini AI with advanced techniques.

    Tich hop:
    - VectorDB & Semantic Search cho RAG context
    - AIConfig cho prompt tuy chinh theo nguoi dung
    """

    FALLBACK_MODELS = [
        "gemini-2.5-flash",
        "gemini-3-flash",
        "gemini-3.1-flash-lite",
    ]
    MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 20

    # Adaptive thresholds
    SMALL_PAGE_THRESHOLD = 15
    LARGE_PAGE_THRESHOLD = 40

    def __init__(self, api_key: str = "", vector_db=None, ai_config=None):
        self.api_key = api_key
        self._client = None
        self.vector_db = vector_db    # VectorDB instance (optional)
        self.ai_config = ai_config    # AIConfig instance (optional)

    def configure(self, api_key: str, vector_db=None, ai_config=None):
        self.api_key = api_key
        self._client = None
        if vector_db is not None:
            self.vector_db = vector_db
        if ai_config is not None:
            self.ai_config = ai_config

    def _get_client(self):
        if not genai:
            raise RuntimeError("google-genai package is not installed. Run: pip install google-genai")
        if not self.api_key:
            raise ValueError("API key chua duoc cau hinh.")
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    # ------------------------------------------------------------------
    # Retry / fallback helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_retry_delay(error):
        err_str = str(error)
        match = re.search(r"retry\s+in\s+([\d.]+)\s*s", err_str, re.IGNORECASE)
        if match:
            return float(match.group(1))
        match = re.search(r"retryDelay.*?'(\d+)s'", err_str)
        if match:
            return float(match.group(1))
        return None

    @staticmethod
    def _is_daily_quota_exhausted(error):
        err_str = str(error)
        return "PerDay" in err_str and "limit: 0" in err_str

    def _call_model(self, client, model_name, prompt):
        """Call a single model with retry logic."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                log.info(f"Goi model {model_name} (lan {attempt})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                err_str = str(e)
                is_rate_limit = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
                is_not_found = "404" in err_str or "NOT_FOUND" in err_str

                if is_not_found:
                    log.warning(f"Model {model_name}: khong ton tai. Chuyen sang model khac...")
                    return None

                if not is_rate_limit:
                    raise

                if self._is_daily_quota_exhausted(e):
                    log.warning(f"Model {model_name}: het quota ngay. Chuyen sang model khac...")
                    return None

                delay = self._parse_retry_delay(e) or self.DEFAULT_RETRY_DELAY
                if attempt < self.MAX_RETRIES:
                    log.info(f"Rate limit, thu lai sau {delay:.0f}s... (lan {attempt}/{self.MAX_RETRIES})")
                    time.sleep(delay + 2)
                else:
                    log.warning(f"Model {model_name}: het so lan thu lai.")
                    return None
        return None

    def _call_with_fallback(self, client, prompt):
        """Try all fallback models and return (text, model_name) or raise."""
        # Su dung model priority tu ai_config neu co
        models = self.FALLBACK_MODELS
        if self.ai_config:
            custom_models = self.ai_config.get_model_priority()
            if custom_models:
                models = custom_models
        for model_name in models:
            raw = self._call_model(client, model_name, prompt)
            if raw:
                return raw, model_name
            log.info(f"Model {model_name} khong kha dung, thu model tiep theo...")

        raise RuntimeError(
            "Tat ca cac model Gemini deu khong kha dung "
            f"({', '.join(models)}).\n\n"
            "Nguyen nhan co the:\n"
            "- Het quota (free tier gioi han so luong request/ngay)\n"
            "- Model khong ton tai voi API version hien tai\n\n"
            "Giai phap:\n"
            "1. Doi 1-2 phut roi thu lai (quota per-minute se reset)\n"
            "2. Doi den ngay mai (quota mien phi reset moi ngay)\n"
            "3. Nang cap len Google AI Studio tra phi tai:\n"
            "   https://ai.google.dev/pricing\n"
            "4. Tao API key moi tai:\n"
            "   https://aistudio.google.com/apikey"
        )

    # ------------------------------------------------------------------
    # Adaptive strategy selection
    # ------------------------------------------------------------------

    def _select_strategy(self, locator_count: int) -> str:
        """Choose processing strategy based on page complexity."""
        if locator_count <= self.SMALL_PAGE_THRESHOLD:
            return "single_pass"
        elif locator_count <= self.LARGE_PAGE_THRESHOLD:
            return "filtered"
        else:
            return "multi_stage"

    # ------------------------------------------------------------------
    # Public generate method
    # ------------------------------------------------------------------

    def generate(self, use_case_text: str, locators: dict, template: dict,
                 page_id: str, url: str, project_path: str = "") -> dict:
        """Generate test artifacts using advanced AI pipeline.

        Pipeline:
        1. Pre-filter locators (remove irrelevant elements)
        2. Chunk use case into semantic sections
        3. Gather RAG context from existing project files
        4. Adaptively choose single-pass or multi-stage strategy
        5. Call Gemini with fallback across multiple models
        """
        client = self._get_client()

        # --- Stage 0: Index use case vao Vector DB ---
        if self.vector_db and self.vector_db.is_initialized:
            import hashlib
            uc_id = f"uc_{hashlib.md5(use_case_text[:200].encode()).hexdigest()[:12]}"
            self.vector_db.add_use_case(uc_id, use_case_text, {
                "page_id": page_id, "url": url,
            })

        # --- Stage 1: Pre-AI Filtering ---
        original_count = len(locators)
        filtered_locators = filter_locators(locators)
        log.info(f"[Pipeline] Locators: {original_count} -> {len(filtered_locators)} sau khi loc")

        # --- Stage 2: Semantic Chunking ---
        use_case_chunks = chunk_use_case(use_case_text)
        log.info(f"[Pipeline] Use case chunks: main_flow={'co' if use_case_chunks['main_flow'] else 'khong'}, "
                 f"exception_flows={'co' if use_case_chunks['exception_flows'] else 'khong'}")

        # --- Stage 3: RAG Context (Vector DB Semantic Search + keyword fallback) ---
        rag_context = ""
        use_vector_rag = (
            self.vector_db
            and self.vector_db.is_initialized
            and (not self.ai_config or self.ai_config.is_feature_enabled("vector_db_enabled"))
        )
        if use_vector_rag:
            rag_context = self.vector_db.build_rag_context(
                query=use_case_text, url=url
            )
            if rag_context:
                log.info("[Pipeline] RAG context tu Vector DB (Semantic Search).")
        if not rag_context:
            rag_context = gather_rag_context(project_path, url)
            if rag_context:
                log.info("[Pipeline] RAG context tu keyword-based fallback.")

        # --- Stage 4: Adaptive Strategy ---
        strategy = self._select_strategy(len(filtered_locators))
        log.info(f"[Pipeline] Strategy: {strategy} ({len(filtered_locators)} locators)")

        if strategy == "multi_stage":
            return self._generate_multi_stage(
                client, use_case_chunks, filtered_locators, template,
                page_id, url, rag_context, locators
            )
        else:
            return self._generate_single_pass(
                client, use_case_chunks, filtered_locators, template,
                page_id, url, rag_context, locators
            )

    # ------------------------------------------------------------------
    # Single-pass generation
    # ------------------------------------------------------------------

    def _generate_single_pass(self, client, use_case_chunks, locators, template,
                              page_id, url, rag_context, original_locators):
        """All artifacts in one AI call (for small/medium pages)."""
        prompt = self._build_full_prompt(
            use_case_chunks["full"], locators, template, page_id, url, rag_context
        )
        log.info("[Pipeline] Single-pass: goi AI cho tat ca artifacts...")

        raw_text, model = self._call_with_fallback(client, prompt)
        log.info(f"[Pipeline] {model} tra ve {len(raw_text)} ky tu.")

        return self._parse_response(raw_text, original_locators, template, page_id, url)

    # ------------------------------------------------------------------
    # Multi-stage generation (for large pages)
    # ------------------------------------------------------------------

    def _generate_multi_stage(self, client, use_case_chunks, locators, template,
                              page_id, url, rag_context, original_locators):
        """Split generation into stages for better quality on large pages.

        Stage 1: Locators + Template (using main flow)
        Stage 2: Test Data (using exception flows + data keys from stage 1)
        Stage 3: Setup Script (if needed)
        """
        result = {
            "locators": original_locators,
            "template": template,
            "test_data": [],
            "setup_script": None,
            "summary": "",
        }

        # --- Stage 1: Locators + Template ---
        log.info("[Pipeline] Stage 1/3: Locators + Template...")
        prompt_1 = self._build_stage1_prompt(
            use_case_chunks["full"], locators, template, page_id, url, rag_context
        )
        raw_1, model_1 = self._call_with_fallback(client, prompt_1)
        log.info(f"[Pipeline] Stage 1 ({model_1}): {len(raw_1)} ky tu.")

        loc_block = self._extract_block(raw_1, "json_locators")
        if loc_block:
            try:
                result["locators"] = json.loads(loc_block)
            except json.JSONDecodeError:
                log.warning("Stage 1: khong parse duoc locators.")

        tpl_block = self._extract_block(raw_1, "json_template")
        if tpl_block:
            try:
                result["template"] = json.loads(tpl_block)
            except json.JSONDecodeError:
                log.warning("Stage 1: khong parse duoc template.")

        # --- Stage 2: Test Data ---
        log.info("[Pipeline] Stage 2/3: Test Data...")
        data_keys = [s.get("data_key", "") for s in result["template"].get("steps", []) if s.get("data_key")]
        prompt_2 = self._build_stage2_prompt(
            use_case_chunks, data_keys, page_id, url
        )
        raw_2, model_2 = self._call_with_fallback(client, prompt_2)
        log.info(f"[Pipeline] Stage 2 ({model_2}): {len(raw_2)} ky tu.")

        td_block = self._extract_block(raw_2, "json_testdata")
        if td_block:
            try:
                result["test_data"] = json.loads(td_block)
            except json.JSONDecodeError:
                log.warning("Stage 2: khong parse duoc test data.")

        # --- Stage 3: Setup Script ---
        log.info("[Pipeline] Stage 3/3: Setup Script...")
        prompt_3 = self._build_stage3_prompt(use_case_chunks, page_id, url)
        raw_3, model_3 = self._call_with_fallback(client, prompt_3)
        log.info(f"[Pipeline] Stage 3 ({model_3}): {len(raw_3)} ky tu.")

        ss_block = self._extract_block(raw_3, "json_setup")
        if ss_block:
            try:
                parsed = json.loads(ss_block)
                if parsed and parsed != "null":
                    result["setup_script"] = parsed
            except json.JSONDecodeError:
                log.warning("Stage 3: khong parse duoc setup script.")

        summary_block = self._extract_block(raw_3, "summary")
        if not summary_block:
            summary_block = self._extract_block(raw_1, "summary")
        result["summary"] = (summary_block or "AI da tao xong cac file (multi-stage pipeline).").strip()

        return result

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_full_prompt(self, use_case_text, locators, template, page_id, url,
                           rag_context=""):
        """Full prompt for single-pass generation."""
        locators_json = json.dumps(locators, indent=2, ensure_ascii=False)
        template_json = json.dumps(template, indent=2, ensure_ascii=False)

        # Lay system prompt va objectives tu ai_config neu co
        system_intro = "Ban la chuyen gia test automation."
        objectives_text = ""
        custom_gen_prompt = ""
        if self.ai_config:
            custom_sys = self.ai_config.get_prompt("system_prompt")
            if custom_sys:
                system_intro = custom_sys
            objectives_text = self.ai_config.get_objectives_text()
            custom_gen_prompt = self.ai_config.get_prompt("generate_locators")

        objectives_section = ""
        if objectives_text:
            objectives_section = f"\n=== {objectives_text} ===\n"

        custom_section = ""
        if custom_gen_prompt:
            custom_section = f"\n=== HUONG DAN TUY CHINH ===\n{custom_gen_prompt}\n"

        return f"""{system_intro} Dua tren use case va cac locators/template da quet duoc tu trang web, hay tao ra cac file can thiet cho viec test tu dong.
{objectives_section}{custom_section}

=== THONG TIN ===
URL: {url}
Page ID: {page_id}

=== USE CASE ===
{use_case_text}

=== LOCATORS DA LOC (chi giu lai cac locator lien quan) ===
{locators_json}

=== TEMPLATE HIEN TAI ===
{template_json}
{rag_context}
=== YEU CAU ===
Hay tao ra 4 phan rieng biet, moi phan nam trong block JSON:

1. **LOCATORS** - Chinh sua locators: chi giu lai cac locator thuc su can thiet cho use case, bo cac locator thua. Dinh dang:
```json_locators
{{
  "ELEMENT_NAME": {{
    "selector": "css_selector",
    "type": "action" hoac "info"
  }}
}}
```

2. **TEMPLATE** - Tao template test: cac buoc test theo dung use case (main flow va exception flows). Moi buoc phai co id tuong ung voi locator, action (fill, fill_password, click, verify_text, verify_visible, select, check, uncheck, press, hover), va data_key de lay du lieu tu Excel. Dinh dang:
```json_template
{{
  "page_id": "{page_id}",
  "url": "{url}",
  "steps": [
    {{"id": "ELEMENT_NAME", "action": "fill", "data_key": "column_name"}}
  ]
}}
```

3. **TEST DATA** - Tao du lieu test dang JSON array, moi dong la 1 test case bao gom ca main flow va exception flows. Header la cac data_key trong template. Them cot "expected_result" voi gia tri "success" hoac "fail". Dinh dang:
```json_testdata
[
  {{"column1": "value1", "column2": "value2", "expected_result": "success"}},
  {{"column1": "", "column2": "value2", "expected_result": "fail"}}
]
```

4. **SETUP SCRIPT** - Tao setup script JSON de chuan bi trang truoc khi test (vi du: navigate den trang, dong popup, login truoc, v.v.). Neu khong can setup thi tra ve null. Dinh dang:
```json_setup
{{
  "name": "Ten setup",
  "description": "Mo ta",
  "steps": [
    {{"action": "navigate", "value": "{url}"}},
    {{"action": "click", "selector": "#some-button"}}
  ]
}}
```

Luu y:
- Chi su dung cac selector da co trong locators hoac tao selector moi neu can.
- Cac data_key trong template phai khop voi cac cot trong test data.
- Tao du cac truong hop test: thanh cong (main flow) va that bai (exception flows).
- Tra loi BANG TIENG VIET cho phan mo ta/summary.
- Moi block JSON phai nam trong dung markdown code block voi nhan tuong ung.

5. **SUMMARY** - Tom tat nhung gi da lam:
```summary
Mo ta ngan gon bang tieng Viet ve nhung thay doi.
```
"""

    def _build_stage1_prompt(self, use_case_text, locators, template, page_id, url,
                             rag_context=""):
        """Stage 1: Focus on locators + template only."""
        locators_json = json.dumps(locators, indent=2, ensure_ascii=False)
        template_json = json.dumps(template, indent=2, ensure_ascii=False)

        return f"""Ban la chuyen gia test automation. Chi tap trung vao viec tao LOCATORS va TEMPLATE.

=== THONG TIN ===
URL: {url}
Page ID: {page_id}

=== USE CASE ===
{use_case_text}

=== LOCATORS DA LOC ===
{locators_json}

=== TEMPLATE HIEN TAI ===
{template_json}
{rag_context}
=== YEU CAU ===
Chi tao 2 phan:

1. **LOCATORS** - Loc locators: chi giu lai cac locator can thiet cho use case. Dinh dang:
```json_locators
{{
  "ELEMENT_NAME": {{
    "selector": "css_selector",
    "type": "action" hoac "info"
  }}
}}
```

2. **TEMPLATE** - Tao template test voi cac buoc test day du (main flow + exception flows). Moi buoc co id, action (fill, fill_password, click, verify_text, verify_visible, select, check, uncheck, press, hover), va data_key. Dinh dang:
```json_template
{{
  "page_id": "{page_id}",
  "url": "{url}",
  "steps": [
    {{"id": "ELEMENT_NAME", "action": "fill", "data_key": "column_name"}}
  ]
}}
```

Luu y: data_key se la ten cot trong file Excel test data.

```summary
Tom tat ngan gon.
```
"""

    def _build_stage2_prompt(self, use_case_chunks, data_keys, page_id, url):
        """Stage 2: Focus on test data generation."""
        uc_text = use_case_chunks["full"]
        ef_text = use_case_chunks.get("exception_flows", "")

        keys_str = ", ".join(data_keys) if data_keys else "username, password, expected_result"

        extra = ""
        if ef_text:
            extra = f"\n=== EXCEPTION FLOWS (chu y tao du lieu test cho cac truong hop nay) ===\n{ef_text}\n"

        return f"""Ban la chuyen gia test data. Hay tao du lieu test cho use case sau.

=== USE CASE ===
{uc_text}
{extra}
=== CAC COT DU LIEU CAN TAO ===
{keys_str}

=== YEU CAU ===
Tao du lieu test dang JSON array. Moi dong la 1 test case.
- Bao gom ca main flow (expected_result = "success") va exception flows (expected_result = "fail").
- Tao it nhat 5-8 test cases da dang (happy path, boundary, error cases).
- Dung tieng Viet cho gia tri mo ta neu phu hop.

```json_testdata
[
  {{"column1": "value1", "column2": "value2", "expected_result": "success"}},
  {{"column1": "", "column2": "value2", "expected_result": "fail"}}
]
```
"""

    def _build_stage3_prompt(self, use_case_chunks, page_id, url):
        """Stage 3: Focus on setup script."""
        preconditions = use_case_chunks.get("preconditions", "")
        uc_text = use_case_chunks["full"]

        return f"""Ban la chuyen gia test automation. Hay xac dinh xem use case nay co can setup script (buoc chuan bi truoc khi test) hay khong.

=== THONG TIN ===
URL: {url}
Page ID: {page_id}

=== USE CASE ===
{uc_text}

=== PRECONDITIONS ===
{preconditions if preconditions else "(Khong co precondition cu the)"}

=== YEU CAU ===
Neu can setup (vi du: navigate den trang, login truoc, dong popup, v.v.), tao setup script JSON:
```json_setup
{{
  "name": "Ten setup",
  "description": "Mo ta",
  "steps": [
    {{"action": "navigate", "value": "{url}"}},
    {{"action": "click", "selector": "#some-button"}}
  ]
}}
```

Neu KHONG can setup thi tra ve:
```json_setup
null
```

```summary
Tom tat ngan gon.
```
"""

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(self, raw_text, original_locators, original_template, page_id, url):
        """Parse the structured response from Gemini."""
        result = {
            "locators": original_locators,
            "template": original_template,
            "test_data": [],
            "setup_script": None,
            "summary": "",
        }

        locators_block = self._extract_block(raw_text, "json_locators")
        if locators_block:
            try:
                result["locators"] = json.loads(locators_block)
            except json.JSONDecodeError:
                log.warning("Khong the parse locators tu AI response.")

        template_block = self._extract_block(raw_text, "json_template")
        if template_block:
            try:
                result["template"] = json.loads(template_block)
            except json.JSONDecodeError:
                log.warning("Khong the parse template tu AI response.")

        testdata_block = self._extract_block(raw_text, "json_testdata")
        if testdata_block:
            try:
                result["test_data"] = json.loads(testdata_block)
            except json.JSONDecodeError:
                log.warning("Khong the parse test data tu AI response.")

        setup_block = self._extract_block(raw_text, "json_setup")
        if setup_block:
            try:
                parsed = json.loads(setup_block)
                if parsed and parsed != "null":
                    result["setup_script"] = parsed
            except json.JSONDecodeError:
                log.warning("Khong the parse setup script tu AI response.")

        summary_block = self._extract_block(raw_text, "summary")
        if summary_block:
            result["summary"] = summary_block.strip()
        else:
            result["summary"] = "AI da tao xong cac file."

        return result

    @staticmethod
    def _extract_block(text, label):
        """Extract content between ```label and ``` markers."""
        pattern = rf"```{re.escape(label)}\s*\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
