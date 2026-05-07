"""Test History: store and display test result trends over time."""

import json
from datetime import datetime
from pathlib import Path
from utils.logger import log


class TestHistoryEntry:
    """A single test run history entry."""

    def __init__(self, suite_name: str = "", total: int = 0, passed: int = 0,
                 failed: int = 0, skipped: int = 0, duration_ms: int = 0,
                 timestamp: str = "", details: list = None):
        self.suite_name = suite_name
        self.total = total
        self.passed = passed
        self.failed = failed
        self.skipped = skipped
        self.duration_ms = duration_ms
        self.timestamp = timestamp or datetime.now().isoformat()
        self.details = details or []

    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total * 100) if self.total > 0 else 0

    def to_dict(self):
        return {
            "suite_name": self.suite_name,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_ms": self.duration_ms,
            "pass_rate": round(self.pass_rate, 1),
            "timestamp": self.timestamp,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            suite_name=data.get("suite_name", ""),
            total=data.get("total", 0),
            passed=data.get("passed", 0),
            failed=data.get("failed", 0),
            skipped=data.get("skipped", 0),
            duration_ms=data.get("duration_ms", 0),
            timestamp=data.get("timestamp", ""),
            details=data.get("details", []),
        )


class TestHistory:
    """Manages test execution history."""

    def __init__(self, project_path: str = ""):
        self.project_path = project_path
        self.entries = []
        self._history_path = Path(project_path) / "reports" / "test_history.json" if project_path else None

    def add_entry(self, entry: TestHistoryEntry):
        """Add a new history entry."""
        self.entries.append(entry)
        self._save()
        log.info(f"[History] Da luu ket qua: {entry.suite_name} "
                 f"({entry.passed}/{entry.total} passed)")

    def add_from_report(self, report_data: dict):
        """Create a history entry from a report JSON."""
        entry = TestHistoryEntry(
            suite_name=report_data.get("suite_name", ""),
            total=report_data.get("total", 0),
            passed=report_data.get("passed", 0),
            failed=report_data.get("failed", 0),
            skipped=report_data.get("skipped", 0),
            duration_ms=report_data.get("total_duration_ms", 0),
            details=[
                {
                    "name": r.get("test_name", ""),
                    "status": r.get("status", ""),
                    "duration_ms": r.get("duration_ms", 0),
                }
                for r in report_data.get("results", [])
            ],
        )
        self.add_entry(entry)

    def get_trend(self, last_n: int = 20) -> list:
        """Get the last N entries for trend display."""
        return [e.to_dict() for e in self.entries[-last_n:]]

    def get_summary(self) -> dict:
        """Get overall summary statistics."""
        if not self.entries:
            return {
                "total_runs": 0,
                "avg_pass_rate": 0,
                "total_tests_executed": 0,
                "total_passed": 0,
                "total_failed": 0,
            }

        total_runs = len(self.entries)
        avg_pass_rate = sum(e.pass_rate for e in self.entries) / total_runs
        total_tests = sum(e.total for e in self.entries)
        total_passed = sum(e.passed for e in self.entries)
        total_failed = sum(e.failed for e in self.entries)

        return {
            "total_runs": total_runs,
            "avg_pass_rate": round(avg_pass_rate, 1),
            "total_tests_executed": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "last_run": self.entries[-1].timestamp if self.entries else "",
            "last_status": f"{self.entries[-1].passed}/{self.entries[-1].total}" if self.entries else "",
        }

    def get_failing_tests(self) -> list:
        """Get tests that have been failing recently."""
        if not self.entries:
            return []

        fail_counts = {}
        for entry in self.entries[-10:]:
            for detail in entry.details:
                if detail.get("status") == "failed":
                    name = detail.get("name", "")
                    fail_counts[name] = fail_counts.get(name, 0) + 1

        return sorted(
            [{"name": k, "fail_count": v} for k, v in fail_counts.items()],
            key=lambda x: x["fail_count"],
            reverse=True,
        )

    def load(self):
        """Load history from JSON file."""
        if not self._history_path or not self._history_path.exists():
            return
        try:
            with open(self._history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.entries = [TestHistoryEntry.from_dict(d) for d in data]
            log.info(f"[History] Da tai {len(self.entries)} entries.")
        except Exception as e:
            log.error(f"[History] Loi tai history: {e}")

    def _save(self):
        """Save history to JSON file."""
        if not self._history_path:
            return
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        data = [e.to_dict() for e in self.entries]
        with open(self._history_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def generate_trend_html(self) -> str:
        """Generate an HTML snippet showing test result trends."""
        entries = self.get_trend(20)
        if not entries:
            return "<p>Chua co du lieu lich su.</p>"

        rows = ""
        for e in reversed(entries):
            status_class = "passed" if e["pass_rate"] >= 100 else ("failed" if e["pass_rate"] < 50 else "warning")
            rows += f"""<tr class="{status_class}">
                <td>{e['timestamp'][:16]}</td>
                <td>{e['suite_name']}</td>
                <td>{e['passed']}/{e['total']}</td>
                <td>{e['pass_rate']}%</td>
                <td>{e['duration_ms']}ms</td>
            </tr>"""

        return f"""<table class="history-table">
            <tr><th>Thoi gian</th><th>Suite</th><th>Pass/Total</th><th>Ty le</th><th>Thoi gian</th></tr>
            {rows}
        </table>"""
