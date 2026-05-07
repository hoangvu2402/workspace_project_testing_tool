"""
AIConfig: Quan ly cau hinh AI tuy chinh theo nguoi dung.

Cho phep nguoi dung:
- Chinh sua prompt templates (system prompt, generation prompt, v.v.)
- Thay doi muc tieu/objectives cua AI
- Dieu chinh tham so model (temperature, max_tokens, top_p)
- Chon model uu tien
- Luu/load profiles cau hinh
- Bat/tat cac ky thuat AI (semantic search, RAG, multi-stage, v.v.)
"""

import json
from pathlib import Path
from utils.logger import log


# ---------------------------------------------------------------------------
# Default prompt templates
# ---------------------------------------------------------------------------

DEFAULT_PROMPTS = {
    "system_prompt": (
        "Ban la chuyen gia test automation voi nhieu nam kinh nghiem. "
        "Ban hieu ro Playwright, CSS selectors, va cac best practices trong testing. "
        "Luon tra ve ket qua chinh xac, day du, va co cau truc JSON chuan."
    ),

    "generate_locators": (
        "Phan tich va loc cac locator: chi giu lai nhung locator thuc su can thiet "
        "cho use case. Loai bo cac locator thua, khong lien quan. "
        "Dam bao moi locator co selector chinh xac va type phu hop."
    ),

    "generate_template": (
        "Tao template test voi cac buoc (steps) day du cho main flow va exception flows. "
        "Moi buoc phai co: id (ten element), action (fill, click, verify_text, v.v.), "
        "va data_key (ten cot du lieu). Dam bao thu tu cac buoc logic va day du."
    ),

    "generate_test_data": (
        "Tao du lieu test da dang bao gom: happy path (thanh cong), "
        "boundary values (gia tri bien), negative cases (du lieu sai), "
        "va cac truong hop exception flow. Moi test case co cot expected_result."
    ),

    "generate_setup_script": (
        "Xac dinh setup can thiet truoc khi chay test: navigate, login, "
        "dong popup, v.v. Neu khong can setup thi tra ve null."
    ),

    "auto_heal": (
        "Phan tich HTML cua trang va de xuat selector thay the cho locator bi loi. "
        "Uu tien: data-testid > id > name > aria-label > css class. "
        "Dam bao selector moi la duy nhat va on dinh."
    ),

    "natural_language": (
        "Chuyen doi mo ta test tu ngon ngu tu nhien thanh template automation. "
        "Tao locators, template steps, va test data tu mo ta nguoi dung."
    ),

    "test_suggestion": (
        "Phan tich code changes va de xuat test case can chay lai. "
        "Xem xet cac file thay doi va anh huong den cac page/template nao."
    ),
}


DEFAULT_OBJECTIVES = {
    "accuracy": "Dam bao do chinh xac cao nhat cho locators va test steps",
    "coverage": "Tao nhieu test case bao phu ca happy path va error cases",
    "stability": "Uu tien selectors on dinh (id, data-testid) hon class/xpath",
    "readability": "Dat ten element va data_key de doc, de hieu",
    "reusability": "Tao template co the tai su dung cho nhieu bo du lieu",
}


DEFAULT_MODEL_PARAMS = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "model_priority": [
        "gemini-2.5-flash",
        "gemini-3-flash",
        "gemini-3.1-flash-lite",
    ],
}


DEFAULT_FEATURES = {
    "semantic_search": True,
    "rag_enabled": True,
    "multi_stage_pipeline": True,
    "pre_filter_locators": True,
    "semantic_chunking": True,
    "adaptive_processing": True,
    "auto_heal_enabled": True,
    "vector_db_enabled": True,
}


# ---------------------------------------------------------------------------
# AIConfig class
# ---------------------------------------------------------------------------

class AIConfig:
    """Quan ly cau hinh AI tuy chinh theo nguoi dung.

    Luu tru cau hinh tai: config/ai_config.json
    """

    CONFIG_FILE = "config/ai_config.json"

    def __init__(self, project_path: str = ""):
        self.project_path = project_path
        self._config = self._default_config()
        self._load()

    def _default_config(self) -> dict:
        return {
            "prompts": dict(DEFAULT_PROMPTS),
            "objectives": dict(DEFAULT_OBJECTIVES),
            "model_params": dict(DEFAULT_MODEL_PARAMS),
            "features": dict(DEFAULT_FEATURES),
            "profiles": {},
            "active_profile": "default",
        }

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _config_path(self) -> Path:
        if self.project_path:
            return Path(self.project_path) / self.CONFIG_FILE
        return Path(self.CONFIG_FILE)

    def _load(self):
        """Load cau hinh tu file. Neu khong co thi dung default."""
        path = self._config_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                # Merge with defaults (giu lai cac key moi)
                for section in ["prompts", "objectives", "model_params", "features"]:
                    defaults = self._default_config().get(section, {})
                    saved = data.get(section, {})
                    merged = {**defaults, **saved}
                    self._config[section] = merged
                self._config["profiles"] = data.get("profiles", {})
                self._config["active_profile"] = data.get("active_profile", "default")
                log.info(f"[AIConfig] Da load cau hinh tu {path}")
            except Exception as e:
                log.warning(f"[AIConfig] Loi load config: {e}. Dung default.")
        else:
            log.info("[AIConfig] Chua co file config. Dung default.")

    def save(self):
        """Luu cau hinh ra file."""
        path = self._config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            log.info(f"[AIConfig] Da luu cau hinh tai {path}")
        except Exception as e:
            log.error(f"[AIConfig] Loi luu config: {e}")

    # ------------------------------------------------------------------
    # Prompt management
    # ------------------------------------------------------------------

    def get_prompt(self, key: str) -> str:
        """Lay prompt template theo key."""
        return self._config["prompts"].get(key, DEFAULT_PROMPTS.get(key, ""))

    def set_prompt(self, key: str, value: str):
        """Dat prompt template."""
        self._config["prompts"][key] = value

    def get_all_prompts(self) -> dict:
        return dict(self._config["prompts"])

    def reset_prompt(self, key: str):
        """Reset prompt ve mac dinh."""
        if key in DEFAULT_PROMPTS:
            self._config["prompts"][key] = DEFAULT_PROMPTS[key]

    def reset_all_prompts(self):
        """Reset tat ca prompts ve mac dinh."""
        self._config["prompts"] = dict(DEFAULT_PROMPTS)

    # ------------------------------------------------------------------
    # Objectives
    # ------------------------------------------------------------------

    def get_objectives(self) -> dict:
        return dict(self._config["objectives"])

    def set_objective(self, key: str, value: str):
        self._config["objectives"][key] = value

    def remove_objective(self, key: str):
        self._config["objectives"].pop(key, None)

    def get_objectives_text(self) -> str:
        """Tra ve objectives duoi dang text de chen vao prompt."""
        objs = self._config["objectives"]
        if not objs:
            return ""
        lines = [f"- {k}: {v}" for k, v in objs.items()]
        return "MUC TIEU AI:\n" + "\n".join(lines)

    # ------------------------------------------------------------------
    # Model parameters
    # ------------------------------------------------------------------

    def get_model_params(self) -> dict:
        return dict(self._config["model_params"])

    def set_model_param(self, key: str, value):
        self._config["model_params"][key] = value

    def get_temperature(self) -> float:
        return self._config["model_params"].get("temperature", 0.7)

    def get_top_p(self) -> float:
        return self._config["model_params"].get("top_p", 0.95)

    def get_max_tokens(self) -> int:
        return self._config["model_params"].get("max_output_tokens", 8192)

    def get_model_priority(self) -> list:
        return self._config["model_params"].get("model_priority", DEFAULT_MODEL_PARAMS["model_priority"])

    def set_model_priority(self, models: list):
        self._config["model_params"]["model_priority"] = models

    # ------------------------------------------------------------------
    # Features toggle
    # ------------------------------------------------------------------

    def get_features(self) -> dict:
        return dict(self._config["features"])

    def is_feature_enabled(self, feature: str) -> bool:
        return self._config["features"].get(feature, False)

    def set_feature(self, feature: str, enabled: bool):
        self._config["features"][feature] = enabled

    # ------------------------------------------------------------------
    # Profiles
    # ------------------------------------------------------------------

    def save_profile(self, name: str):
        """Luu cau hinh hien tai thanh profile."""
        self._config["profiles"][name] = {
            "prompts": dict(self._config["prompts"]),
            "objectives": dict(self._config["objectives"]),
            "model_params": dict(self._config["model_params"]),
            "features": dict(self._config["features"]),
        }
        self._config["active_profile"] = name
        log.info(f"[AIConfig] Da luu profile: {name}")

    def load_profile(self, name: str) -> bool:
        """Load profile da luu."""
        if name not in self._config["profiles"]:
            if name == "default":
                self._config["prompts"] = dict(DEFAULT_PROMPTS)
                self._config["objectives"] = dict(DEFAULT_OBJECTIVES)
                self._config["model_params"] = dict(DEFAULT_MODEL_PARAMS)
                self._config["features"] = dict(DEFAULT_FEATURES)
                self._config["active_profile"] = "default"
                return True
            log.warning(f"[AIConfig] Profile '{name}' khong ton tai.")
            return False

        profile = self._config["profiles"][name]
        self._config["prompts"] = dict(profile.get("prompts", DEFAULT_PROMPTS))
        self._config["objectives"] = dict(profile.get("objectives", DEFAULT_OBJECTIVES))
        self._config["model_params"] = dict(profile.get("model_params", DEFAULT_MODEL_PARAMS))
        self._config["features"] = dict(profile.get("features", DEFAULT_FEATURES))
        self._config["active_profile"] = name
        log.info(f"[AIConfig] Da load profile: {name}")
        return True

    def delete_profile(self, name: str):
        """Xoa profile."""
        self._config["profiles"].pop(name, None)
        if self._config["active_profile"] == name:
            self._config["active_profile"] = "default"

    def list_profiles(self) -> list:
        """Tra ve danh sach profiles."""
        profiles = ["default"] + list(self._config["profiles"].keys())
        return list(dict.fromkeys(profiles))  # deduplicate, preserve order

    def get_active_profile(self) -> str:
        return self._config["active_profile"]

    # ------------------------------------------------------------------
    # Build enhanced prompt
    # ------------------------------------------------------------------

    def build_system_instruction(self) -> str:
        """Xay dung system instruction day du tu cau hinh hien tai."""
        parts = [self.get_prompt("system_prompt")]

        # Add objectives
        obj_text = self.get_objectives_text()
        if obj_text:
            parts.append(obj_text)

        return "\n\n".join(parts)

    def enhance_prompt(self, base_prompt: str, prompt_key: str = "") -> str:
        """Bo sung prompt voi objectives va custom instructions.

        Args:
            base_prompt: Prompt goc
            prompt_key: Key cua custom prompt de them vao (vd: 'generate_template')

        Returns:
            Prompt da duoc bo sung
        """
        parts = []

        # System instruction
        system = self.build_system_instruction()
        if system:
            parts.append(f"=== HUONG DAN HE THONG ===\n{system}")

        # Custom prompt for this specific task
        if prompt_key:
            custom = self.get_prompt(prompt_key)
            if custom:
                parts.append(f"=== HUONG DAN CU THE ===\n{custom}")

        # Base prompt
        parts.append(base_prompt)

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Export / Import
    # ------------------------------------------------------------------

    def export_config(self) -> str:
        """Xuat cau hinh dang JSON string."""
        return json.dumps(self._config, indent=2, ensure_ascii=False)

    def import_config(self, json_str: str) -> bool:
        """Nhap cau hinh tu JSON string."""
        try:
            data = json.loads(json_str)
            for section in ["prompts", "objectives", "model_params", "features"]:
                if section in data:
                    self._config[section] = data[section]
            if "profiles" in data:
                self._config["profiles"] = data["profiles"]
            log.info("[AIConfig] Da import cau hinh thanh cong.")
            return True
        except Exception as e:
            log.error(f"[AIConfig] Loi import config: {e}")
            return False

    # ------------------------------------------------------------------
    # Prompt key descriptions (for UI)
    # ------------------------------------------------------------------

    @staticmethod
    def get_prompt_descriptions() -> dict:
        """Tra ve mo ta cua tung prompt key (cho UI hien thi)."""
        return {
            "system_prompt": "Prompt he thong - Dinh nghia vai tro va phong cach AI",
            "generate_locators": "Prompt loc locators - Huong dan AI loc va chon locators",
            "generate_template": "Prompt tao template - Huong dan AI tao test steps",
            "generate_test_data": "Prompt tao du lieu test - Huong dan AI tao test data",
            "generate_setup_script": "Prompt tao setup script - Huong dan AI tao setup",
            "auto_heal": "Prompt tu sua locator - Huong dan AI tim selector thay the",
            "natural_language": "Prompt xu ly ngon ngu tu nhien - Chuyen doi mo ta thanh template",
            "test_suggestion": "Prompt goi y test - Huong dan AI phan tich code changes",
        }
