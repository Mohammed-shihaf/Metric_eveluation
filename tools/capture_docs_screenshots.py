"""Capture UI screenshots for project documentation (Playwright)."""
from __future__ import print_function

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "Testabel_Assurance_Studio_Docs" / "images"
BASE = os.environ.get("E2E_BASE_URL", "http://localhost:8501")

CAPTURES = [
    ("01-overview-branches.png", "Branches", 1500),
    ("02-whitebox.png", "Whitebox", 1500),
    ("03-local-tools.png", "Local tools", 1200),
    ("04-sonarqube.png", "SonarQube", 1200),
    ("05-compare.png", "Compare", 1500),
]


def main():
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            resp = page.goto(BASE, wait_until="networkidle", timeout=90000)
            if not resp or resp.status >= 400:
                print("FAIL app_load HTTP %s" % (resp.status if resp else "?"))
                return 1
            page.wait_for_selector('[data-testid="stApp"]', timeout=45000)
            page.screenshot(path=str(OUT / "00-landing-sidebar.png"), full_page=True)
            print("OK 00-landing-sidebar.png")

            for filename, tab, wait_ms in CAPTURES:
                page.get_by_role("tab", name=tab, exact=True).click()
                page.wait_for_timeout(wait_ms)
                page.screenshot(path=str(OUT / filename), full_page=True)
                print("OK %s" % filename)

            sidebar = page.locator('[data-testid="stSidebar"]')
            if sidebar.get_by_text("Language", exact=True).count():
                page.screenshot(path=str(OUT / "06-sidebar-filters.png"), full_page=False)
                print("OK 06-sidebar-filters.png")
        except Exception as exc:
            page.screenshot(path=str(OUT / "error.png"), full_page=True)
            print("FAIL %s" % exc)
            return 1
        finally:
            browser.close()
    print("Screenshots saved to %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
