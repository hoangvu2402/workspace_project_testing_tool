"""
AIGenerator: Use Google Gemini to analyze scanned locators and use cases,
then generate/modify locators, templates, test data, and setup scripts.
"""

import json
import re
import time
from utils.logger import log

try:
    from google import genai
    from google.genai import errors as genai_errors
except ImportError:
    genai = None
    genai_errors = None
    log.warning("google-genai not installed. AI features disabled.")


class AIGenerator:
    """Generates test artifacts using Google Gemini AI."""

    FALLBACK_MODELS = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
    ]
    MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 20

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._client = None

    def configure(self, api_key: str):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if not genai:
            raise RuntimeError("google-genai package is not installed. Run: pip install google-genai")
        if not self.api_key:
            raise ValueError("API key chua duoc cau hinh.")
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @staticmethod
    def _parse_retry_delay(error):
        """Extract retry delay seconds from a Gemini API error."""
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
        """Check if the error indicates daily quota is fully exhausted (not just per-minute)."""
        err_str = str(error)
        return "PerDay" in err_str and "limit: 0" in err_str

    def _call_model(self, client, model_name, prompt):
        """Call a single model with retry logic for per-minute rate limits."""
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

    def generate(self, use_case_text: str, locators: dict, template: dict,
                 page_id: str, url: str) -> dict:
        """Call Gemini to generate modified locators, template, test data, and setup script.

        Tries multiple models with automatic retry and fallback.
        """
        client = self._get_client()
        prompt = self._build_prompt(use_case_text, locators, template, page_id, url)
        log.info("Dang goi Gemini AI...")

        raw_text = None
        used_model = None

        for model_name in self.FALLBACK_MODELS:
            raw_text = self._call_model(client, model_name, prompt)
            if raw_text:
                used_model = model_name
                break
            log.info(f"Model {model_name} khong kha dung, thu model tiep theo...")

        if not raw_text:
            raise RuntimeError(
                "Tat ca cac model Gemini deu het quota.\n\n"
                "Giai phap:\n"
                "1. Doi 1-2 phut roi thu lai (quota per-minute se reset)\n"
                "2. Doi den ngay mai (quota mien phi reset moi ngay)\n"
                "3. Nang cap len Google AI Studio tra phi tai:\n"
                "   https://ai.google.dev/pricing\n"
                "4. Tao API key moi tai:\n"
                "   https://aistudio.google.com/apikey"
            )

        log.info(f"Gemini ({used_model}) tra ve {len(raw_text)} ky tu.")
        return self._parse_response(raw_text, locators, template, page_id, url)

    def _build_prompt(self, use_case_text, locators, template, page_id, url):
        locators_json = json.dumps(locators, indent=2, ensure_ascii=False)
        template_json = json.dumps(template, indent=2, ensure_ascii=False)

        return f"""Ban la chuyen gia test automation. Dua tren use case va cac locators/template da quet duoc tu trang web, hay tao ra cac file can thiet cho viec test tu dong.

=== THONG TIN ===
URL: {url}
Page ID: {page_id}

=== USE CASE ===
{use_case_text}

=== LOCATORS HIEN TAI (da quet tu trang) ===
{locators_json}

=== TEMPLATE HIEN TAI (da quet tu trang) ===
{template_json}

=== YEU CAU ===
Hay tao ra 4 phan rieng biet, moi phan nam trong block JSON:

1. **LOCATORS** - Chinh sua locators hien tai: chi giu lai cac locator lien quan den use case, loai bo cac locator khong can thiet. Dinh dang:
```json_locators
{{
  "ELEMENT_NAME": {{
    "selector": "css_selector",
    "type": "action" hoac "info"
  }}
}}
```

2. **TEMPLATE** - Chinh sua template: tao cac buoc test theo dung use case (main flow va exception flows). Moi buoc phai co id tuong ung voi locator, action (fill, fill_password, click, verify_text, verify_visible, select, check, uncheck, press, hover), va data_key de lay du lieu tu Excel. Dinh dang:
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
- Chi su dung cac selector da co trong locators hien tai hoac tao selector moi neu can.
- Cac data_key trong template phai khop voi cac cot trong test data.
- Tao du cac truong hop test: thanh cong (main flow) va that bai (exception flows).
- Tra loi BANG TIENG VIET cho phan mo ta/summary.
- Moi block JSON phai nam trong dung markdown code block voi nhan tuong ung (json_locators, json_template, json_testdata, json_setup).

5. **SUMMARY** - Tom tat nhung gi da lam:
```summary
Mo ta ngan gon bang tieng Viet ve nhung thay doi.
```
"""

    def _parse_response(self, raw_text, original_locators, original_template, page_id, url):
        """Parse the structured response from Gemini."""
        result = {
            "locators": original_locators,
            "template": original_template,
            "test_data": [],
            "setup_script": None,
            "summary": "",
        }

        # Parse json_locators
        locators_block = self._extract_block(raw_text, "json_locators")
        if locators_block:
            try:
                result["locators"] = json.loads(locators_block)
            except json.JSONDecodeError:
                log.warning("Khong the parse locators tu AI response.")

        # Parse json_template
        template_block = self._extract_block(raw_text, "json_template")
        if template_block:
            try:
                result["template"] = json.loads(template_block)
            except json.JSONDecodeError:
                log.warning("Khong the parse template tu AI response.")

        # Parse json_testdata
        testdata_block = self._extract_block(raw_text, "json_testdata")
        if testdata_block:
            try:
                result["test_data"] = json.loads(testdata_block)
            except json.JSONDecodeError:
                log.warning("Khong the parse test data tu AI response.")

        # Parse json_setup
        setup_block = self._extract_block(raw_text, "json_setup")
        if setup_block:
            try:
                parsed = json.loads(setup_block)
                if parsed and parsed != "null":
                    result["setup_script"] = parsed
            except json.JSONDecodeError:
                log.warning("Khong the parse setup script tu AI response.")

        # Parse summary
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
