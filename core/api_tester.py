"""API Testing Module: REST/GraphQL testing with assertions."""

import json
import time
from datetime import datetime
from utils.logger import log


class APITestCase:
    """Represents a single API test case."""

    def __init__(self, name: str, method: str, url: str, headers: dict = None,
                 body: str = "", params: dict = None, assertions: list = None):
        self.name = name
        self.method = method.upper()
        self.url = url
        self.headers = headers or {}
        self.body = body
        self.params = params or {}
        self.assertions = assertions or []

    def to_dict(self):
        return {
            "name": self.name,
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "body": self.body,
            "params": self.params,
            "assertions": self.assertions,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data.get("name", "Unnamed"),
            method=data.get("method", "GET"),
            url=data.get("url", ""),
            headers=data.get("headers", {}),
            body=data.get("body", ""),
            params=data.get("params", {}),
            assertions=data.get("assertions", []),
        )


class APITestResult:
    """Result of an API test execution."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.status = "pending"
        self.status_code = 0
        self.response_body = ""
        self.response_headers = {}
        self.response_time_ms = 0
        self.assertions_results = []
        self.error = ""

    def to_dict(self):
        return {
            "test_name": self.test_name,
            "status": self.status,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "response_body": self.response_body[:2000],
            "assertions_results": self.assertions_results,
            "error": self.error,
        }


class APITester:
    """Executes API tests using Python's urllib (no external HTTP dependency)."""

    def __init__(self):
        self.results = []
        self.base_url = ""
        self.default_headers = {"Content-Type": "application/json"}

    def set_base_url(self, url: str):
        self.base_url = url.rstrip("/")

    def run_test(self, test_case: APITestCase) -> APITestResult:
        """Execute a single API test case."""
        import urllib.request
        import urllib.error
        import urllib.parse

        result = APITestResult(test_case.name)

        full_url = test_case.url
        if not full_url.startswith("http"):
            full_url = f"{self.base_url}/{full_url.lstrip('/')}"

        if test_case.params:
            query = urllib.parse.urlencode(test_case.params)
            full_url = f"{full_url}?{query}"

        headers = {**self.default_headers, **test_case.headers}
        body_data = None
        if test_case.body and test_case.method in ("POST", "PUT", "PATCH"):
            body_data = test_case.body.encode("utf-8")

        start = time.perf_counter()
        try:
            req = urllib.request.Request(
                full_url,
                data=body_data,
                headers=headers,
                method=test_case.method,
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result.status_code = resp.status
                result.response_body = resp.read().decode("utf-8", errors="replace")
                result.response_headers = dict(resp.headers)

        except urllib.error.HTTPError as e:
            result.status_code = e.code
            result.response_body = e.read().decode("utf-8", errors="replace")
            result.response_headers = dict(e.headers)
        except Exception as e:
            result.error = str(e)
            result.status = "error"
            self.results.append(result)
            return result

        result.response_time_ms = round((time.perf_counter() - start) * 1000, 2)

        # Run assertions
        all_passed = True
        for assertion in test_case.assertions:
            a_result = self._check_assertion(assertion, result)
            result.assertions_results.append(a_result)
            if not a_result["passed"]:
                all_passed = False

        result.status = "passed" if all_passed else "failed"
        self.results.append(result)

        log.info(
            f"[API] {test_case.method} {full_url} -> {result.status_code} "
            f"({result.response_time_ms}ms) [{result.status.upper()}]"
        )
        return result

    def run_collection(self, test_cases: list) -> list:
        """Run multiple API test cases."""
        results = []
        for tc in test_cases:
            if isinstance(tc, dict):
                tc = APITestCase.from_dict(tc)
            results.append(self.run_test(tc))
        return results

    def _check_assertion(self, assertion: dict, result: APITestResult) -> dict:
        """Check a single assertion against the response.

        Assertion format:
        {
            "type": "status_code" | "body_contains" | "body_json_path" | "header" | "response_time",
            "expected": value,
            "path": "json.path" (for body_json_path)
        }
        """
        a_type = assertion.get("type", "")
        expected = assertion.get("expected")
        passed = False
        actual = None

        if a_type == "status_code":
            actual = result.status_code
            passed = actual == int(expected)

        elif a_type == "body_contains":
            actual = result.response_body
            passed = str(expected) in actual

        elif a_type == "body_json_path":
            path = assertion.get("path", "")
            try:
                data = json.loads(result.response_body)
                actual = self._resolve_json_path(data, path)
                passed = str(actual) == str(expected)
            except Exception as e:
                actual = f"Error: {e}"
                passed = False

        elif a_type == "header":
            header_name = assertion.get("path", "")
            actual = result.response_headers.get(header_name, "")
            passed = str(expected).lower() in str(actual).lower()

        elif a_type == "response_time":
            actual = result.response_time_ms
            passed = actual <= float(expected)

        return {
            "type": a_type,
            "expected": expected,
            "actual": actual if not isinstance(actual, str) or len(str(actual)) < 200 else str(actual)[:200] + "...",
            "passed": passed,
        }

    @staticmethod
    def _resolve_json_path(data, path: str):
        """Simple JSON path resolver (e.g., 'data.user.name')."""
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current

    def save_collection(self, filepath: str, test_cases: list):
        """Save API test collection to JSON."""
        data = [tc.to_dict() if hasattr(tc, "to_dict") else tc for tc in test_cases]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_collection(self, filepath: str) -> list:
        """Load API test collection from JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [APITestCase.from_dict(d) for d in data]
