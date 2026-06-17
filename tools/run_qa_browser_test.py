"""Quick QA login + tab smoke test for Streamlit UI."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.sa_qa import load_env

load_env(str(ROOT / ".env.local"))

BASE = os.environ.get("E2E_BASE_URL", "http://localhost:8501")
QA_EMAIL = os.environ.get("AUTH_EMAIL", "Shihaf+16@Testable.Cloud")
QA_PASSWORD = os.environ.get("AUTH_PASSWORD", "Welcome1234!")
OUT = ROOT / "docs" / "e2e-demo" / ("verify-qa-%s" % datetime.now().strftime("%Y%m%d-%H%M%S"))


def main():
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    results = []

    def record(name, ok, detail=""):
        results.append({"name": name, "ok": ok, "detail": detail})
        print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        try:
            page.goto(BASE, wait_until="networkidle", timeout=60000)
            page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
            record("app_load", True, BASE)

            sidebar = page.locator('[data-testid="stSidebar"]')
            record("account_header", sidebar.get_by_text("Account", exact=True).count() > 0)
            record("selection_header", sidebar.get_by_text("Selection", exact=True).count() > 0)

            if sidebar.get_by_text("Signed in as", exact=False).count():
                record("qa_login", True, "already signed in")
            else:
                email = sidebar.get_by_label("QA email")
                pw = sidebar.get_by_label("QA password")
                record("login_fields", email.count() > 0 and pw.count() > 0)
                if email.count() and pw.count():
                    email.fill(QA_EMAIL)
                    pw.fill(QA_PASSWORD)
                    sidebar.get_by_role("button", name="Sign in").click()
                    page.wait_for_timeout(6000)
                    record("qa_login", sidebar.get_by_text("Signed in as", exact=False).count() > 0)
                else:
                    record("qa_login", False, "no login fields")

            page.screenshot(path=str(OUT / "01-after-login.png"), full_page=True)

            for tab in ["Branches", "Whitebox", "Local tools", "SonarQube", "Compare"]:
                page.get_by_text(tab, exact=True).first.click()
                page.wait_for_timeout(2000)
                exc = page.locator('[data-testid="stException"]').count()
                record("tab_%s" % tab.replace(" ", "_").lower(), exc == 0, "exceptions=%d" % exc)
                page.screenshot(
                    path=str(OUT / ("02-%s.png" % tab.replace(" ", "-").lower())),
                    full_page=True,
                )

            record("in_scope_metric", sidebar.get_by_text("In scope", exact=False).count() > 0)
        except Exception as exc:
            record("unexpected", False, str(exc))
            page.screenshot(path=str(OUT / "error.png"), full_page=True)
        finally:
            browser.close()

    passed = sum(1 for r in results if r["ok"])
    failed = sum(1 for r in results if not r["ok"])
    summary = {"base": BASE, "passed": passed, "failed": failed, "results": results, "out": str(OUT)}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n=== QA BROWSER TEST ===")
    print(json.dumps({"passed": passed, "failed": failed, "out": str(OUT)}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
