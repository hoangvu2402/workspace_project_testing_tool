"""Natural Language Test: write tests in Vietnamese, AI converts to template."""

import json
import re
from utils.logger import log

try:
    from google import genai
except ImportError:
    genai = None


class AINaturalLanguage:
    """Converts natural language test descriptions (Vietnamese/English) into
    automation templates, locators, and test data."""

    FALLBACK_MODELS = [
        "gemini-2.5-flash",
        "gemini-3-flash",
        "gemini-3.1-flash-lite",
    ]

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._client = None

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

    def convert_to_template(self, natural_text: str, url: str = "",
                            page_id: str = "", existing_locators: dict = None) -> dict:
        """Convert natural language test description to a test template.

        Args:
            natural_text: Test description in Vietnamese or English
            url: Target page URL
            page_id: Page identifier
            existing_locators: Optional dict of existing locators for the page

        Returns:
            dict with keys: template, locators, test_data, setup_script
        """
        client = self._get_client()

        locators_context = ""
        if existing_locators:
            locators_context = f"""
Locators da co cho trang nay:
{json.dumps(existing_locators, indent=2, ensure_ascii=False)[:3000]}

Hay su dung cac locator co san khi phu hop. Chi tao locator moi khi can thiet.
"""

        prompt = f"""Toi muon tao test tu dong tu mo ta bang ngon ngu tu nhien.
Hay chuyen doi mo ta sau thanh cac file test automation.

Mo ta test:
{natural_text}

URL trang test: {url}
Page ID: {page_id}
{locators_context}

Hay tra ve JSON voi cau truc sau:
{{
    "template": {{
        "page_id": "{page_id}",
        "url": "{url}",
        "steps": [
            {{
                "id": "TEN_ELEMENT",
                "action": "click|fill|verify_text|verify_visible|wait|navigate|...",
                "data_key": "ten_cot_du_lieu",
                "value": "gia_tri_mac_dinh"
            }}
        ]
    }},
    "locators": {{
        "TEN_ELEMENT": {{
            "name": "Mo ta",
            "type": "action|info",
            "selector": "css_selector"
        }}
    }},
    "test_data": [
        {{
            "cot1": "gia_tri_1",
            "expected_result": "success|fail"
        }}
    ],
    "explanation": "Giai thich buoc nao lam gi"
}}

Luu y:
- Dung CSS selector chuan cho locators
- action phai la mot trong: click, fill, fill_password, verify_text, verify_visible,
  verify_url, wait, navigate, hover, press, select, check, uncheck, type
- data_key la ten cot trong file Excel du lieu test
- Tao it nhat 3 bo du lieu test (happy path + negative cases)
- Chi tra ve JSON, khong giai thich them."""

        for model in self.FALLBACK_MODELS:
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                text = response.text.strip()
                text = re.sub(r"```json\s*", "", text)
                text = re.sub(r"```\s*$", "", text)
                result = json.loads(text)
                log.info(f"[NaturalLang] Da chuyen doi thanh cong voi {model}")
                return result
            except Exception as e:
                log.debug(f"[NaturalLang] Model {model}: {e}")
                continue

        raise RuntimeError("Khong the chuyen doi. Tat ca model deu that bai.")

    def parse_scenario_list(self, text: str) -> list:
        """Parse a list of test scenarios from natural language.

        Input like:
            1. Dang nhap thanh cong voi user hop le
            2. Dang nhap that bai voi mat khau sai
            3. Dang nhap voi tai khoan bi khoa

        Returns list of scenario strings.
        """
        lines = text.strip().split("\n")
        scenarios = []
        for line in lines:
            line = line.strip()
            line = re.sub(r"^[\d]+[\.\)\-]\s*", "", line)
            if line:
                scenarios.append(line)
        return scenarios

    def batch_convert(self, scenarios: list, url: str = "",
                      page_id: str = "", existing_locators: dict = None) -> list:
        """Convert multiple natural language scenarios to templates."""
        results = []
        for scenario in scenarios:
            try:
                result = self.convert_to_template(
                    scenario, url, page_id, existing_locators
                )
                result["scenario"] = scenario
                results.append(result)
            except Exception as e:
                results.append({
                    "scenario": scenario,
                    "error": str(e),
                })
        return results

    def suggest_improvements(self, natural_text: str) -> dict:
        """Suggest improvements for a natural language test description."""
        client = self._get_client()

        prompt = f"""Phan tich mo ta test sau va de xuat cai thien:

{natural_text}

Hay tra ve JSON:
{{
    "quality_score": 0-10,
    "missing_elements": ["nhung gi con thieu"],
    "suggestions": ["de xuat cai thien"],
    "improved_text": "mo ta da duoc cai thien"
}}

Chi tra ve JSON."""

        for model in self.FALLBACK_MODELS:
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                text = response.text.strip()
                text = re.sub(r"```json\s*", "", text)
                text = re.sub(r"```\s*$", "", text)
                return json.loads(text)
            except Exception:
                continue

        return {"quality_score": 0, "suggestions": ["Khong the phan tich."]}
