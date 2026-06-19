"""Browser E2E smoke test for Streamlit UI (Playwright)."""
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
OUT = ROOT / "docs" / "e2e-demo" / ("verify-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
QA_EMAIL = os.environ.get("AUTH_EMAIL", "")
QA_PASSWORD = os.environ.get("AUTH_PASSWORD", "")

results = []


def record(name, ok, detail=""):
    results.append({"name": name, "ok": ok, "detail": detail})
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))


def main():
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        try:
            resp = page.goto(BASE, wait_until="networkidle", timeout=60000)
            if not resp or resp.status >= 400:
                record("app_load", False, "HTTP %s" % (resp.status if resp else "?"))
                return 1
            record("app_load", True, BASE)

            page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
            record("streamlit_shell", True)

            for tab in ["Branches", "Whitebox", "Local tools", "SonarQube", "Compare"]:
                el = page.get_by_role("tab", name=tab, exact=True)
                record("tab_%s" % tab.replace(" ", "_").lower(), el.count() > 0)

            sidebar = page.locator('[data-testid="stSidebar"]')
            has_lang = sidebar.get_by_text("Language", exact=True).count() > 0
            has_ver = sidebar.get_by_text("Version", exact=True).count() > 0
            has_runtime = sidebar.get_by_text("Runtime version", exact=True).count() > 0
            record("sidebar_language_version", has_lang and has_ver and has_runtime)
            record("sidebar_github_section", sidebar.get_by_text("GitHub", exact=True).count() > 0)
            record("sidebar_testable_qa_section", sidebar.get_by_text("Testable QA", exact=True).count() > 0)

            if sidebar.get_by_text("Signed in as", exact=False).count():
                record("qa_login", True, "already signed in")
            elif QA_EMAIL and QA_PASSWORD:
                email_in = sidebar.locator('input[type="text"]').first
                pass_in = sidebar.locator('input[type="password"]').first
                if email_in.count() and pass_in.count():
                    email_in.fill(QA_EMAIL)
                    pass_in.fill(QA_PASSWORD)
                    sign_in = sidebar.get_by_role("button", name="Sign in")
                    if sign_in.count():
                        sign_in.click()
                        page.wait_for_timeout(4000)
                        record("qa_login", sidebar.get_by_text("Signed in as", exact=False).count() > 0)
                    else:
                        record("qa_login", False, "no sign in button")
                else:
                    record("qa_login", False, "no login fields")
            else:
                record("qa_login", False, "no credentials")

            page.screenshot(path=str(OUT / "01-initial.png"), full_page=True)

            page.get_by_role("tab", name="Branches", exact=True).click()
            page.wait_for_timeout(1000)
            gen = page.get_by_role("button", name="1 — Generate branches")
            record("branches_generate_button", gen.count() > 0, "disabled=%s" % (gen.is_disabled() if gen.count() else "?"))
            record("branches_strength_caption", page.get_by_text("strength floor", exact=False).count() > 0)
            disconnect = sidebar.get_by_role("button", name="Disconnect")
            if disconnect.count():
                record("sidebar_github_disconnect", True)
            elif sidebar.get_by_text("Connected as", exact=False).count():
                record("sidebar_github_disconnect", False, "connected but no Disconnect button")
            else:
                switch = sidebar.get_by_role("link", name="Switch GitHub account")
                if not switch.count():
                    switch = sidebar.get_by_role("button", name="Switch GitHub account")
                connect = sidebar.get_by_role("link", name="Connect GitHub")
                if not connect.count():
                    connect = sidebar.get_by_role("button", name="Connect GitHub")
                record(
                    "sidebar_github_switch",
                    switch.count() > 0,
                    "switch link visible when not connected",
                )
                record(
                    "sidebar_github_connect",
                    connect.count() > 0 or sidebar.get_by_text("Sign in to Testable first").count() > 0,
                    "connect visible or QA gate",
                )
            page.screenshot(path=str(OUT / "02-branches.png"), full_page=True)

            page.get_by_role("tab", name="Whitebox", exact=True).click()
            page.wait_for_timeout(1500)
            record("whitebox_header", page.get_by_role("heading", name="2 — Whitebox").count() > 0)
            run_btn = page.get_by_role("button", name="Run whitebox batch")
            record("whitebox_run_button", run_btn.count() > 0, "disabled=%s" % (run_btn.is_disabled() if run_btn.count() else "?"))
            record("whitebox_branch_picker", page.get_by_text("Choose branches for this whitebox batch").count() > 0)

            page.wait_for_timeout(5000)
            record(
                "whitebox_stable_5s",
                page.get_by_role("heading", name="2 — Whitebox").is_visible(),
            )
            page.screenshot(path=str(OUT / "03-whitebox.png"), full_page=True)

            n_select = sidebar.locator('[data-baseweb="select"]').count()
            record("sidebar_select_widgets", n_select >= 2, "count=%d" % n_select)

            for tab in ["Local tools", "SonarQube", "Compare"]:
                page.get_by_role("tab", name=tab, exact=True).click()
                page.wait_for_timeout(800)
                record(
                    "tab_load_%s" % tab.replace(" ", "_").lower(),
                    page.locator('[data-testid="stException"]').count() == 0,
                )

            page.screenshot(path=str(OUT / "04-final.png"), full_page=True)
        except Exception as exc:
            record("unexpected", False, str(exc))
            page.screenshot(path=str(OUT / "error.png"), full_page=True)
        finally:
            browser.close()

    passed = sum(1 for r in results if r["ok"])
    failed = sum(1 for r in results if not r["ok"])
    summary = {"base": BASE, "passed": passed, "failed": failed, "results": results, "screenshots": str(OUT)}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n=== BROWSER E2E ===")
    print(json.dumps({"passed": passed, "failed": failed, "out": str(OUT)}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
