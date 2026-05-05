"""AI Auto-Heal Locators: when a locator fails, AI finds a replacement."""

import json
import re
import time
from utils.logger import log

try:
    from google import genai
except ImportError:
    genai = None


class AIAutoHeal:
    """Uses AI to find replacement locators when element not found."""

    FALLBACK_MODELS = [
        "gemini-2.5-flash",
        "gemini-3-flash",
        "gemini-3.1-flash-lite",
    ]

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._client = None
        self.heal_log = []  # tracks all heal attempts

    def configure(self, api_key: str):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if not genai:
            raise RuntimeError("google-genai not installed.")
        if not self.api_key:
            raise ValueError("API key chua duoc cau hinh.")
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def try_heal(self, page, step_id: str, original_selector: str,
                 locator_info: dict, page_source: str = "") -> dict:
        """Attempt to find a replacement locator using AI.

        Args:
            page: Playwright page object
            step_id: The step ID that failed
            original_selector: The selector that failed
            locator_info: The original locator info dict
            page_source: Optional pre-fetched page HTML

        Returns:
            dict with keys:
                healed: bool
                new_selector: str
                confidence: float (0-1)
                method: str (ai, heuristic, none)
        """
        log.info(f"[AutoHeal] Bat dau tu sua locator: {step_id} ({original_selector})")

        # Step 1: Try heuristic healing first (fast, no API call)
        heuristic_result = self._try_heuristic(page, original_selector, locator_info)
        if heuristic_result["healed"]:
            self._record_heal(step_id, original_selector,
                              heuristic_result["new_selector"], "heuristic")
            return heuristic_result

        # Step 2: Try AI healing
        if self.api_key:
            try:
                ai_result = self._try_ai_heal(page, step_id, original_selector,
                                               locator_info, page_source)
                if ai_result["healed"]:
                    self._record_heal(step_id, original_selector,
                                      ai_result["new_selector"], "ai")
                    return ai_result
            except Exception as e:
                log.warning(f"[AutoHeal] AI heal that bai: {e}")

        log.warning(f"[AutoHeal] Khong the tu sua locator: {step_id}")
        return {"healed": False, "new_selector": "", "confidence": 0, "method": "none"}

    def _try_heuristic(self, page, selector: str, info: dict) -> dict:
        """Try common heuristic strategies to find the element."""
        name = info.get("name", "")
        loc_type = info.get("type", "")

        strategies = []

        # Strategy 1: If ID-based selector, try by name attribute
        if selector.startswith("#"):
            element_id = selector[1:]
            strategies.extend([
                f'[name="{element_id}"]',
                f'[data-testid="{element_id}"]',
                f'[data-test="{element_id}"]',
                f'[aria-label="{name}"]' if name else None,
            ])

        # Strategy 2: Try text-based selectors
        if name:
            strategies.extend([
                f'text="{name}"',
                f'[placeholder="{name}"]',
                f'[title="{name}"]',
            ])

        # Strategy 3: If class-based, try partial match
        if "." in selector:
            parts = selector.split(".")
            for part in parts[1:]:
                if len(part) > 3:
                    strategies.append(f'[class*="{part}"]')

        for candidate in strategies:
            if candidate is None:
                continue
            try:
                element = page.query_selector(candidate)
                if element and element.is_visible():
                    log.info(f"[AutoHeal] Heuristic tim thay: {candidate}")
                    return {
                        "healed": True,
                        "new_selector": candidate,
                        "confidence": 0.7,
                        "method": "heuristic",
                    }
            except Exception:
                continue

        return {"healed": False, "new_selector": "", "confidence": 0, "method": "heuristic"}

    def _try_ai_heal(self, page, step_id: str, selector: str,
                     info: dict, page_source: str = "") -> dict:
        """Use AI to analyze the page and find a replacement selector."""
        if not page_source:
            try:
                page_source = page.content()
                if len(page_source) > 15000:
                    page_source = page_source[:15000]
            except Exception:
                page_source = ""

        prompt = f"""Toi dang tu dong hoa test va locator bi loi (element not found).
Hay phan tich HTML va de xuat selector thay the.

Locator bi loi:
- Step ID: {step_id}
- Selector goc: {selector}
- Ten: {info.get('name', '')}
- Loai: {info.get('type', '')}

HTML cua trang (rut gon):
{page_source[:10000]}

Hay tra ve JSON:
{{
    "new_selector": "selector_moi_o_day",
    "confidence": 0.8,
    "reason": "ly do chon selector nay"
}}

Chi tra ve JSON, khong giai thich them."""

        client = self._get_client()
        for model in self.FALLBACK_MODELS:
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                text = response.text.strip()
                text = re.sub(r"```json\s*", "", text)
                text = re.sub(r"```\s*$", "", text)
                data = json.loads(text)

                new_selector = data.get("new_selector", "")
                if new_selector:
                    # Verify the selector works
                    try:
                        element = page.query_selector(new_selector)
                        if element:
                            log.info(f"[AutoHeal] AI tim thay selector: {new_selector}")
                            return {
                                "healed": True,
                                "new_selector": new_selector,
                                "confidence": data.get("confidence", 0.5),
                                "method": "ai",
                            }
                    except Exception:
                        pass
            except Exception as e:
                log.debug(f"[AutoHeal] Model {model} loi: {e}")
                continue

        return {"healed": False, "new_selector": "", "confidence": 0, "method": "ai"}

    def _record_heal(self, step_id: str, old_selector: str,
                     new_selector: str, method: str):
        """Record a successful heal for reporting."""
        self.heal_log.append({
            "step_id": step_id,
            "old_selector": old_selector,
            "new_selector": new_selector,
            "method": method,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        log.info(
            f"[AutoHeal] Da tu sua: {step_id} | "
            f"{old_selector} -> {new_selector} ({method})"
        )

    def update_locator_file(self, locator_path: str, step_id: str,
                            new_selector: str) -> bool:
        """Update the locator JSON file with the healed selector."""
        try:
            from pathlib import Path
            path = Path(locator_path)
            if not path.exists():
                return False
            data = json.loads(path.read_text(encoding="utf-8"))
            if step_id in data:
                data[step_id]["selector"] = new_selector
                data[step_id]["auto_healed"] = True
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                log.info(f"[AutoHeal] Da cap nhat locator file: {step_id}")
                return True
            return False
        except Exception as e:
            log.error(f"[AutoHeal] Loi cap nhat file: {e}")
            return False

    def get_heal_report(self) -> list:
        """Get the full heal log."""
        return self.heal_log
