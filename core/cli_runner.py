"""CLI Runner: command-line interface for CI/CD integration with JUnit XML output."""

import argparse
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def create_junit_xml(results: list, suite_name: str = "AutomationTestSuite",
                     output_path: str = "reports/junit_results.xml") -> str:
    """Create JUnit XML report from test results.

    Args:
        results: List of dicts with keys: name, status, duration_s, error_message
        suite_name: Name for the test suite
        output_path: Where to save the XML

    Returns:
        Path to the generated XML file.
    """
    total = len(results)
    failures = sum(1 for r in results if r.get("status") == "failed")
    errors = sum(1 for r in results if r.get("status") == "error")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    total_time = sum(r.get("duration_s", 0) for r in results)

    testsuite = ET.Element("testsuite", {
        "name": suite_name,
        "tests": str(total),
        "failures": str(failures),
        "errors": str(errors),
        "skipped": str(skipped),
        "time": f"{total_time:.3f}",
        "timestamp": datetime.now().isoformat(),
    })

    for r in results:
        testcase = ET.SubElement(testsuite, "testcase", {
            "name": r.get("name", "unknown"),
            "classname": r.get("classname", suite_name),
            "time": f"{r.get('duration_s', 0):.3f}",
        })

        if r.get("status") == "failed":
            failure = ET.SubElement(testcase, "failure", {
                "message": r.get("error_message", "Test failed"),
                "type": "AssertionError",
            })
            failure.text = r.get("error_message", "")

        elif r.get("status") == "error":
            error = ET.SubElement(testcase, "error", {
                "message": r.get("error_message", "Error occurred"),
                "type": "Exception",
            })
            error.text = r.get("error_message", "")

        elif r.get("status") == "skipped":
            ET.SubElement(testcase, "skipped", {
                "message": r.get("error_message", "Skipped"),
            })

        if r.get("stdout"):
            stdout = ET.SubElement(testcase, "system-out")
            stdout.text = r["stdout"]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(testsuite)
    tree.write(output_path, xml_declaration=True, encoding="unicode")
    return output_path


def parse_pytest_output(output: str) -> list:
    """Parse pytest output to extract test results."""
    results = []
    for line in output.split("\n"):
        line = line.strip()
        if "PASSED" in line or "FAILED" in line or "ERROR" in line:
            parts = line.split("::")
            name = parts[-1].split(" ")[0] if parts else line
            name = name.strip()

            if "PASSED" in line:
                status = "passed"
            elif "FAILED" in line:
                status = "failed"
            else:
                status = "error"

            results.append({
                "name": name,
                "classname": parts[0] if len(parts) > 1 else "tests",
                "status": status,
                "duration_s": 0,
                "error_message": line if status != "passed" else "",
            })

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Automation Test CLI - CI/CD Integration"
    )
    parser.add_argument("--project", "-p", required=True, help="Project directory path")
    parser.add_argument("--template", "-t", help="Template file (relative to templates/)")
    parser.add_argument("--data", "-d", help="Test data file (relative to test_data/)")
    parser.add_argument("--sheet", "-s", default="Sheet1", help="Excel sheet name")
    parser.add_argument("--page-id", help="Page ID")
    parser.add_argument("--url", "-u", help="Base URL")
    parser.add_argument("--browser", "-b", default="chromium", choices=["chromium", "firefox", "webkit"])
    parser.add_argument("--mode", "-m", default="single", choices=["single", "e2e"])
    parser.add_argument("--setup-script", help="Setup script name")
    parser.add_argument("--headless", action="store_true", default=True, help="Run headless (default)")
    parser.add_argument("--no-headless", action="store_true", help="Run with browser visible")
    parser.add_argument("--junit-xml", default="reports/junit_results.xml", help="JUnit XML output path")
    parser.add_argument("--json-report", default="reports/cli_report.json", help="JSON report output path")
    parser.add_argument("--parallel", "-n", type=int, default=1, help="Number of parallel workers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    project_path = os.path.abspath(args.project)
    if not os.path.isdir(project_path):
        print(f"Error: Project directory not found: {project_path}")
        sys.exit(1)

    test_file = "tests/test_e2e.py" if args.mode == "e2e" else "tests/test_main.py"
    cmd = [sys.executable, "-m", "pytest", test_file, "-v", "-s"]

    if args.parallel > 1:
        cmd.extend(["-n", str(args.parallel)])

    cmd.append(f"--junitxml={args.junit_xml}")

    env = os.environ.copy()
    env["PYTHONPATH"] = project_path
    if args.url:
        env["BASE_URL"] = args.url
    if args.data:
        env["SELECTED_TEST_DATA"] = Path(args.data).name
    env["SHEET_NAME"] = args.sheet
    if args.page_id:
        env["PAGE_ID"] = args.page_id
    env["BROWSER"] = args.browser
    env["HEADLESS"] = "true" if not args.no_headless else "false"
    env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})

    if args.setup_script:
        setup_path = os.path.join(project_path, "scripts", "setup", args.setup_script)
        env["SETUP_SCRIPT"] = setup_path

    if args.mode == "e2e" and args.template:
        env["E2E_WORKFLOW"] = os.path.join(project_path, "templates", args.template)

    print(f"{'='*60}")
    print(f"  Automation Test CLI")
    print(f"  Project: {project_path}")
    print(f"  Mode: {args.mode}")
    print(f"  Browser: {args.browser}")
    print(f"  Template: {args.template or 'default'}")
    print(f"{'='*60}")

    start_time = time.time()

    process = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        cwd=project_path,
    )

    duration = time.time() - start_time

    if args.verbose:
        print(process.stdout)
        if process.stderr:
            print(process.stderr)

    results = parse_pytest_output(process.stdout)

    report = {
        "timestamp": datetime.now().isoformat(),
        "project": project_path,
        "mode": args.mode,
        "template": args.template,
        "browser": args.browser,
        "exit_code": process.returncode,
        "duration_s": round(duration, 2),
        "total": len(results),
        "passed": sum(1 for r in results if r["status"] == "passed"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "results": results,
    }

    Path(args.json_report).parent.mkdir(parents=True, exist_ok=True)
    with open(args.json_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  Results: {report['passed']}/{report['total']} passed")
    print(f"  Duration: {duration:.1f}s")
    print(f"  JUnit XML: {args.junit_xml}")
    print(f"  JSON Report: {args.json_report}")
    print(f"{'='*60}")

    sys.exit(process.returncode)


if __name__ == "__main__":
    main()
