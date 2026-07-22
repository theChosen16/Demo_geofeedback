#!/usr/bin/env python3
"""
GeoFeedback - Agentic Railway CI/CD Bridge
Orchestrates test executions and log diagnostic extraction using Railway CLI.
Acts as the intelligence bridge between GitHub Actions, Railway Workspace, and the AI Agent.
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

REPORTS_DIR = Path(__file__).resolve().parents[2] / ".agents" / "ui_reports"
REPORT_FILE = REPORTS_DIR / "railway_ci_report.json"


def run_cmd(command: str, cwd: Optional[str] = None) -> tuple[int, str, str]:
    """Helper to execute shell command and capture stdout/stderr safely."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd or str(Path(__file__).resolve().parents[2]),
        )
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except Exception as ex:
        return 1, "", str(ex)


def check_railway_status() -> Dict[str, Any]:
    """Inspect Railway project services and health via Railway CLI."""
    code, stdout, stderr = run_cmd("railway status")
    healthy = code == 0
    services = []
    
    if healthy:
        for line in stdout.splitlines():
            line_str = line.strip()
            if line_str.startswith("- ") or "status:" in line_str:
                services.append(line_str)
                
    return {
        "cli_available": True,
        "connected": healthy,
        "raw_status": stdout if healthy else stderr,
        "services_summary": services,
    }


def fetch_service_logs(service_name: str, build_logs: bool = False) -> str:
    """Fetch real-time build or runtime logs for a given Railway service."""
    cmd = f"railway logs --service {service_name}"
    if build_logs:
        cmd += " --build"
    code, stdout, stderr = run_cmd(cmd)
    return stdout if code == 0 else stderr


def execute_agentic_tests(test_type: str = "all") -> Dict[str, Any]:
    """
    Execute tests inside the Railway cloud context via `railway run`
    or fallback to local execution if CLI is unauthenticated.
    """
    results = {}
    
    # 1. Check Python Unit Tests
    if test_type in ("all", "unit"):
        print("[Railway CI Agent] Running Backend Observability & Unit Tests...")
        code, out, err = run_cmd("python -m unittest discover -s tests -p 'test_*.py' -v")
        results["unit_tests"] = {
            "passed": code == 0,
            "exit_code": code,
            "stdout": out[-1000:],
            "stderr": err[-1000:],
        }
        
    # 2. Check UI/UX Agent Review
    if test_type in ("all", "ui"):
        print("[Railway CI Agent] Running UI/UX Heuristic Design Review...")
        code, out, err = run_cmd("python scripts/qa/ui_ux_design_review_agent.py")
        results["ui_ux_review"] = {
            "passed": code == 0,
            "exit_code": code,
            "stdout": out[-1000:],
            "stderr": err[-1000:],
        }

    return results


def save_report(data: Dict[str, Any]) -> None:
    """Save report JSON to .agents/ui_reports/ for AI Agent inspection."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[Railway CI Agent] Report written to: {REPORT_FILE}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        
    parser = argparse.ArgumentParser(description="GeoFeedback Railway Agentic CI Bridge")
    parser.add_argument("--check-status", action="store_true", help="Check Railway project health")
    parser.add_argument("--run-tests", type=str, nargs="?", const="all", help="Run tests in Railway context")
    parser.add_argument("--fetch-logs", type=str, help="Fetch logs for a specific Railway service")
    
    args = parser.parse_args()
    
    report = {
        "timestamp": str(os.popen("date /t || date").read().strip()),
        "railway_status": check_railway_status(),
        "test_results": {},
    }
    
    if args.check_status:
        print("=== Railway Environment Status ===")
        print(report["railway_status"]["raw_status"])
        
    if args.fetch_logs:
        print(f"=== Fetching Logs for Service: {args.fetch_logs} ===")
        logs = fetch_service_logs(args.fetch_logs)
        print(logs[:2000])
        report["service_logs"] = {args.fetch_logs: logs[:5000]}
        
    if args.run_tests:
        test_res = execute_agentic_tests(args.run_tests)
        report["test_results"] = test_res
        
    save_report(report)


if __name__ == "__main__":
    main()
