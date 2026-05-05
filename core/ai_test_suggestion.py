"""AI Test Case Suggestion: analyze git diff and suggest which tests to run."""

import json
import re
import subprocess
from pathlib import Path
from utils.logger import log

try:
    from google import genai
except ImportError:
    genai = None


class AITestSuggestion:
    """Suggests which test cases need to be re-run based on code changes."""

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

    def get_git_diff(self, project_path: str, base_branch: str = "main") -> str:
        """Get git diff for the current changes."""
        try:
            result = subprocess.run(
                ["git", "diff", base_branch, "--name-only"],
                capture_output=True, text=True,
                cwd=project_path, timeout=10,
            )
            changed_files = result.stdout.strip()

            result2 = subprocess.run(
                ["git", "diff", base_branch, "--stat"],
                capture_output=True, text=True,
                cwd=project_path, timeout=10,
            )
            diff_stat = result2.stdout.strip()

            result3 = subprocess.run(
                ["git", "diff", base_branch],
                capture_output=True, text=True,
                cwd=project_path, timeout=30,
            )
            full_diff = result3.stdout.strip()
            if len(full_diff) > 10000:
                full_diff = full_diff[:10000] + "\n... (truncated)"

            return f"Changed files:\n{changed_files}\n\nStat:\n{diff_stat}\n\nDiff:\n{full_diff}"
        except Exception as e:
            log.error(f"[TestSuggest] Loi lay git diff: {e}")
            return ""

    def get_uncommitted_changes(self, project_path: str) -> str:
        """Get uncommitted changes (staged + unstaged)."""
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD"],
                capture_output=True, text=True,
                cwd=project_path, timeout=30,
            )
            diff = result.stdout.strip()
            if len(diff) > 10000:
                diff = diff[:10000] + "\n... (truncated)"
            return diff
        except Exception as e:
            log.error(f"[TestSuggest] Loi: {e}")
            return ""

    def analyze_changes(self, project_path: str, diff_text: str = "") -> dict:
        """Analyze code changes and identify affected areas.

        Returns dict with:
            affected_pages: list of page IDs that may be affected
            affected_locators: list of locator files that changed
            affected_templates: list of template files that changed
            risk_level: low, medium, high
            suggestions: list of suggestion strings
        """
        if not diff_text:
            diff_text = self.get_uncommitted_changes(project_path)

        if not diff_text:
            return {
                "affected_pages": [],
                "affected_locators": [],
                "affected_templates": [],
                "risk_level": "low",
                "suggestions": ["Khong co thay doi nao duoc phat hien."],
            }

        # Parse changed files
        affected_pages = set()
        affected_locators = []
        affected_templates = []
        risk_level = "low"

        for line in diff_text.split("\n"):
            if line.startswith("locators/"):
                affected_locators.append(line)
                page_id = Path(line).stem
                affected_pages.add(page_id)
                risk_level = "high"
            elif line.startswith("templates/"):
                affected_templates.append(line)
                page_id = Path(line).stem.replace("_workflow", "").replace("e2e_", "")
                affected_pages.add(page_id)
                risk_level = "high"
            elif line.startswith("core/") or line.startswith("pages/"):
                risk_level = "high"
            elif line.startswith("config/"):
                risk_level = "medium" if risk_level == "low" else risk_level

        result = {
            "affected_pages": list(affected_pages),
            "affected_locators": affected_locators,
            "affected_templates": affected_templates,
            "risk_level": risk_level,
            "suggestions": [],
        }

        if affected_locators:
            result["suggestions"].append(
                f"Locators da thay doi cho {', '.join(affected_pages)}. "
                "Can chay lai test cho cac trang nay."
            )
        if affected_templates:
            result["suggestions"].append(
                "Template workflow da thay doi. Can chay lai test tuong ung."
            )
        if risk_level == "high":
            result["suggestions"].append(
                "Thay doi co risk cao. Nen chay tat ca test."
            )
        if not result["suggestions"]:
            result["suggestions"].append("Thay doi nho. Khong can chay lai test.")

        return result

    def suggest_with_ai(self, project_path: str, diff_text: str = "") -> dict:
        """Use AI to provide detailed test suggestions based on code changes."""
        if not diff_text:
            diff_text = self.get_uncommitted_changes(project_path)

        if not diff_text:
            return {"suggestions": [], "explanation": "Khong co thay doi."}

        # Gather existing test context
        p = Path(project_path)
        templates = []
        tpl_dir = p / "templates"
        if tpl_dir.exists():
            for site_dir in tpl_dir.iterdir():
                if site_dir.is_dir():
                    for f in site_dir.glob("*_workflow.json"):
                        templates.append(str(f.relative_to(p)))

        locator_files = []
        loc_dir = p / "locators"
        if loc_dir.exists():
            for site_dir in loc_dir.iterdir():
                if site_dir.is_dir():
                    for f in site_dir.glob("*.json"):
                        locator_files.append(str(f.relative_to(p)))

        prompt = f"""Phan tich thay doi code va de xuat test case can chay lai.

Code diff:
{diff_text[:8000]}

Templates hien co:
{json.dumps(templates, indent=2)}

Locator files:
{json.dumps(locator_files, indent=2)}

Hay tra ve JSON:
{{
    "suggestions": [
        {{
            "template": "ten_template",
            "priority": "high/medium/low",
            "reason": "ly do can chay lai"
        }}
    ],
    "explanation": "tom tat phan tich",
    "risk_level": "high/medium/low",
    "new_tests_needed": ["mo ta test case moi can tao"]
}}

Chi tra ve JSON."""

        client = self._get_client()
        for model in self.FALLBACK_MODELS:
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                text = response.text.strip()
                text = re.sub(r"```json\s*", "", text)
                text = re.sub(r"```\s*$", "", text)
                return json.loads(text)
            except Exception as e:
                log.debug(f"[TestSuggest] Model {model}: {e}")
                continue

        # Fallback to rule-based analysis
        return self.analyze_changes(project_path, diff_text)
