"""HTML Report Generator: creates rich test reports with screenshots, stats, timing."""

import json
import os
from datetime import datetime
from pathlib import Path
from utils.logger import log


class TestResult:
    """Represents a single test case result."""

    def __init__(self, test_name: str, page_id: str = ""):
        self.test_name = test_name
        self.page_id = page_id
        self.status = "pending"  # pending, passed, failed, skipped
        self.start_time = None
        self.end_time = None
        self.duration_ms = 0
        self.steps = []  # list of StepResult
        self.error_message = ""
        self.screenshot_path = ""

    def start(self):
        self.start_time = datetime.now()
        self.status = "running"

    def finish(self, passed: bool, error: str = "", screenshot: str = ""):
        self.end_time = datetime.now()
        self.status = "passed" if passed else "failed"
        self.error_message = error
        self.screenshot_path = screenshot
        if self.start_time:
            self.duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)

    def to_dict(self):
        return {
            "test_name": self.test_name,
            "page_id": self.page_id,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "screenshot_path": self.screenshot_path,
            "steps": [s.to_dict() for s in self.steps],
            "start_time": self.start_time.isoformat() if self.start_time else "",
            "end_time": self.end_time.isoformat() if self.end_time else "",
        }


class StepResult:
    """Represents a single step result within a test."""

    def __init__(self, step_id: str, action: str):
        self.step_id = step_id
        self.action = action
        self.status = "passed"
        self.duration_ms = 0
        self.error_message = ""
        self.screenshot_path = ""

    def to_dict(self):
        return {
            "step_id": self.step_id,
            "action": self.action,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "screenshot_path": self.screenshot_path,
        }


class ReportGenerator:
    """Generates HTML test reports."""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.html_dir = self.reports_dir / "html"

    def generate_html(self, results: list, suite_name: str = "Test Suite",
                      start_time: datetime = None, end_time: datetime = None) -> str:
        """Generate an HTML report from test results.

        Args:
            results: List of TestResult objects.
            suite_name: Name of the test suite.
            start_time: Suite start time.
            end_time: Suite end time.

        Returns:
            Path to the generated HTML file.
        """
        self.html_dir.mkdir(parents=True, exist_ok=True)

        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        total_duration = sum(r.duration_ms for r in results)

        pass_rate = (passed / total * 100) if total > 0 else 0

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.html"
        filepath = self.html_dir / filename

        # Also save JSON data
        json_path = self.html_dir / f"report_{timestamp}.json"
        json_data = {
            "suite_name": suite_name,
            "timestamp": timestamp,
            "start_time": start_time.isoformat() if start_time else "",
            "end_time": end_time.isoformat() if end_time else "",
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": pass_rate,
            "total_duration_ms": total_duration,
            "results": [r.to_dict() for r in results],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        html = self._build_html(json_data, results)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        log.info(f"Da tao bao cao HTML: {filepath}")
        return str(filepath)

    def _build_html(self, data: dict, results: list) -> str:
        rows = ""
        for r in results:
            status_class = r.status
            status_icon = {"passed": "&#10004;", "failed": "&#10008;", "skipped": "&#9679;"}.get(r.status, "?")
            screenshot_html = ""
            if r.screenshot_path and os.path.exists(r.screenshot_path):
                screenshot_html = f'<a href="file:///{r.screenshot_path}" target="_blank">Xem</a>'

            error_html = ""
            if r.error_message:
                escaped = r.error_message.replace("<", "&lt;").replace(">", "&gt;")
                error_html = f'<div class="error-msg">{escaped}</div>'

            steps_html = ""
            if r.steps:
                step_rows = ""
                for s in r.steps:
                    s_dict = s.to_dict() if hasattr(s, "to_dict") else s
                    s_class = s_dict.get("status", "passed")
                    step_rows += f"""<tr class="{s_class}">
                        <td>{s_dict.get('step_id','')}</td>
                        <td>{s_dict.get('action','')}</td>
                        <td>{s_dict.get('status','')}</td>
                        <td>{s_dict.get('duration_ms',0)}ms</td>
                    </tr>"""
                steps_html = f"""<details><summary>Chi tiet buoc ({len(r.steps)} buoc)</summary>
                    <table class="steps-table"><tr><th>Step</th><th>Action</th><th>Status</th><th>Time</th></tr>
                    {step_rows}</table></details>"""

            rows += f"""<tr class="{status_class}">
                <td>{status_icon} {r.test_name}</td>
                <td>{r.page_id}</td>
                <td class="status-{status_class}">{r.status.upper()}</td>
                <td>{r.duration_ms}ms</td>
                <td>{screenshot_html}</td>
            </tr>
            <tr><td colspan="5">{error_html}{steps_html}</td></tr>"""

        return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>Bao cao Test - {data['suite_name']}</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f5f5f5; }}
.header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
           padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
.header h1 {{ margin: 0 0 10px 0; }}
.stats {{ display: flex; gap: 20px; margin: 20px 0; }}
.stat-card {{ background: white; padding: 20px; border-radius: 8px; flex: 1;
              box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
.stat-card h3 {{ margin: 0; font-size: 28px; }}
.stat-card p {{ margin: 5px 0 0; color: #666; }}
.stat-passed h3 {{ color: #27ae60; }}
.stat-failed h3 {{ color: #e74c3c; }}
.stat-total h3 {{ color: #3498db; }}
.stat-time h3 {{ color: #f39c12; }}
table {{ width: 100%; border-collapse: collapse; background: white;
         box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }}
th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
tr.passed {{ background: #eafaf1; }}
tr.failed {{ background: #fdedec; }}
.status-passed {{ color: #27ae60; font-weight: bold; }}
.status-failed {{ color: #e74c3c; font-weight: bold; }}
.error-msg {{ background: #fdf2f2; color: #c0392b; padding: 8px; border-radius: 4px;
              margin: 5px 0; font-size: 13px; font-family: monospace; white-space: pre-wrap; }}
.steps-table {{ width: 100%; margin-top: 5px; font-size: 12px; }}
.steps-table th {{ background: #7f8c8d; padding: 6px; }}
.steps-table td {{ padding: 4px 6px; }}
details {{ margin: 5px 0; }}
.progress-bar {{ height: 20px; background: #ecf0f1; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
.progress-fill {{ height: 100%; background: #27ae60; transition: width 0.3s; }}
</style>
</head>
<body>
<div class="header">
    <h1>Bao cao Ket qua Test</h1>
    <p>{data['suite_name']} | {data.get('start_time','')}</p>
</div>

<div class="stats">
    <div class="stat-card stat-total"><h3>{data['total']}</h3><p>Tong so test</p></div>
    <div class="stat-card stat-passed"><h3>{data['passed']}</h3><p>Thanh cong</p></div>
    <div class="stat-card stat-failed"><h3>{data['failed']}</h3><p>That bai</p></div>
    <div class="stat-card stat-time"><h3>{data['total_duration_ms']}ms</h3><p>Tong thoi gian</p></div>
</div>

<div class="progress-bar">
    <div class="progress-fill" style="width: {data['pass_rate']:.1f}%"></div>
</div>
<p style="text-align:center; color: #666;">Ty le thanh cong: {data['pass_rate']:.1f}%</p>

<table>
<tr><th>Test Case</th><th>Page</th><th>Trang thai</th><th>Thoi gian</th><th>Screenshot</th></tr>
{rows}
</table>

<p style="color: #999; text-align: center; margin-top: 20px;">
    Tao boi Automation Control Center | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</p>
</body>
</html>"""
