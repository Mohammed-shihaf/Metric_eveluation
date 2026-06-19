"""Browser flow test: 2 techniques + all metrics, verify Stage 1 / Whitebox UI."""
from __future__ import print_function

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.pipeline_selection import selection_summary, technique_options
from lib.registry import load_registry
from lib.sa_qa import load_env

load_env(str(ROOT / ".env.local"))

BASE = os.environ.get("E2E_BASE_URL", "http://localhost:8501")
TECHNIQUES = [t.strip() for t in os.environ.get("E2E_TECHNIQUES", "SA,SX").split(",") if t.strip()]
OUT = ROOT / "docs" / "e2e-demo" / ("flow-2tech-%s" % datetime.now().strftime("%Y%m%d-%H%M%S"))

REGISTRY = load_registry()
EXPECTED_SCOPE = selection_summary(
    ",".join(TECHNIQUES),
    "all",
    ["Bug", "BugFX", "CC", "TCC"],
    "2.6",
    REGISTRY,
)["branch_count"]
TECH_LABELS = {code: label for code, label in technique_options(REGISTRY)}


def main():
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    results = []

    def record(name, ok, detail=""):
        results.append({"name": name, "ok": ok, "detail": detail})
        print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        try:
            page.goto(BASE, wait_until="networkidle", timeout=90000)
            page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
            page.wait_for_selector('[data-testid="stSidebarContent"]', timeout=30000)
            page.wait_for_timeout(4000)
            record("app_load", True, BASE)

            sidebar = page.locator('[data-testid="stSidebarContent"]')
            record("sidebar_visible", sidebar.is_visible())

            # --- Selection: 2 techniques + all metrics ---
            all_tech_cb = sidebar.get_by_role("checkbox", name="All techniques (412)")
            if all_tech_cb.count() and all_tech_cb.is_checked():
                all_tech_cb.uncheck()
                page.wait_for_timeout(1500)

            def select_from_multiselect(index, option_code):
                ms = sidebar.locator('[data-testid="stMultiSelect"]').nth(index)
                if not ms.count():
                    return False
                if option_code in (ms.inner_text() or ""):
                    return True
                ms.scroll_into_view_if_needed()
                ms.click()
                page.wait_for_timeout(600)
                opt = page.locator('[role="listbox"] [role="option"]').filter(
                    has_text=option_code
                ).first
                if not opt.count():
                    opt = page.locator('[role="option"]').filter(has_text=option_code).first
                if not opt.count():
                    page.keyboard.press("Escape")
                    return False
                opt.scroll_into_view_if_needed()
                opt.click()
                page.wait_for_timeout(2000)
                page.keyboard.press("Escape")
                page.wait_for_timeout(1000)
                return option_code in (ms.inner_text() or "")

            # Techniques multiselect is the first multiselect in sidebar
            for code in TECHNIQUES:
                label = TECH_LABELS.get(code, code)
                ok = select_from_multiselect(0, code)
                record("select_technique_%s" % code, ok, label if ok else "option not found")

            all_metrics_cb = sidebar.get_by_role("checkbox", name="All metrics")
            if all_metrics_cb.count():
                if not all_metrics_cb.is_checked():
                    try:
                        all_metrics_cb.check(force=True, timeout=5000)
                    except Exception:
                        all_metrics_cb.evaluate("el => el.click()")
                page.wait_for_timeout(3000)
                record("all_metrics_checked", all_metrics_cb.is_checked())
            else:
                record("all_metrics_checked", False, "checkbox missing")

            in_scope_val = -1
            for metric in sidebar.locator('[data-testid="stMetric"]').all():
                label_el = metric.locator('[data-testid="stMetricLabel"]')
                if label_el.count() and "In scope" in label_el.inner_text():
                    val_el = metric.locator('[data-testid="stMetricValue"]')
                    if val_el.count():
                        raw = val_el.inner_text().strip().replace(",", "")
                        if raw.isdigit():
                            in_scope_val = int(raw)
                    break
            record(
                "in_scope_count",
                in_scope_val == EXPECTED_SCOPE,
                "ui=%s expected=%s" % (in_scope_val, EXPECTED_SCOPE),
            )

            page.screenshot(path=str(OUT / "01-selection.png"), full_page=True)

            # --- Branches tab ---
            page.get_by_role("tab", name="Branches", exact=True).click()
            page.wait_for_timeout(2500)
            exc = page.locator('[data-testid="stException"]').count()
            record("branches_no_exception", exc == 0, "exceptions=%d" % exc)

            for btn_name in (
                "1 — Generate branches",
                "2 — Validate branches",
                "3 — Push to GitHub",
            ):
                btn = page.get_by_role("button", name=btn_name)
                record(
                    "branches_%s" % btn_name.split("—", 1)[-1].strip().replace(" ", "_").lower(),
                    btn.count() > 0,
                    "disabled=%s" % (btn.is_disabled() if btn.count() else "?"),
                )

            record(
                "branches_pipeline_progress",
                page.get_by_text("Pipeline progress", exact=False).count() > 0,
            )
            gen_metric = page.get_by_text("1 — Generate", exact=False).count() > 0
            record("branches_step_metrics", gen_metric)

            page.screenshot(path=str(OUT / "02-branches.png"), full_page=True)

            # --- Whitebox tab ---
            page.get_by_role("tab", name="Whitebox", exact=True).click()
            page.wait_for_timeout(2500)
            exc = page.locator('[data-testid="stException"]').count()
            record("whitebox_no_exception", exc == 0, "exceptions=%d" % exc)
            record(
                "whitebox_header",
                page.get_by_role("heading", name=re.compile(r"2 — Whitebox")).count() > 0,
            )
            record(
                "whitebox_branch_picker",
                page.get_by_text("Choose branches for this whitebox batch").count() > 0,
            )

            picker = page.locator('[data-testid="stMultiSelect"]').filter(
                has=page.get_by_text("Choose branches for this whitebox batch")
            )
            if not picker.count():
                picker = page.locator('[data-testid="stMain"]').locator('[data-testid="stMultiSelect"]').last
            if picker.count():
                picker_text = picker.inner_text() or ""
                tag_count = picker.locator('[data-baseweb="tag"]').count()
                branch_count = tag_count if tag_count else len(
                    [line for line in picker_text.split("\n") if "_2.6" in line]
                )
                if branch_count == 0:
                    picker.click()
                    page.wait_for_timeout(800)
                    branch_count = page.locator('[role="option"]').count()
                    page.keyboard.press("Escape")
                record(
                    "whitebox_picker_options",
                    branch_count >= min(EXPECTED_SCOPE, 1),
                    "branches=%d expected>=%d" % (branch_count, min(EXPECTED_SCOPE, 1)),
                )
            else:
                record("whitebox_picker_options", False, "picker not found")

            run_btn = page.get_by_role("button", name="Run whitebox batch")
            record(
                "whitebox_run_button",
                run_btn.count() > 0,
                "disabled=%s" % (run_btn.is_disabled() if run_btn.count() else "?"),
            )

            page.screenshot(path=str(OUT / "03-whitebox.png"), full_page=True)

            # --- Other tabs smoke ---
            for tab in ["Local tools", "SonarQube", "Compare"]:
                page.get_by_role("tab", name=tab, exact=True).click()
                page.wait_for_timeout(2000)
                exc = page.locator('[data-testid="stException"]').count()
                record(
                    "tab_%s" % tab.replace(" ", "_").lower(),
                    exc == 0,
                    "exceptions=%d" % exc,
                )

            page.screenshot(path=str(OUT / "04-compare.png"), full_page=True)

        except Exception as exc:
            record("unexpected", False, str(exc))
            page.screenshot(path=str(OUT / "error.png"), full_page=True)
        finally:
            browser.close()

    passed = sum(1 for r in results if r["ok"])
    failed = sum(1 for r in results if not r["ok"])
    summary = {
        "base": BASE,
        "techniques": TECHNIQUES,
        "expected_in_scope": EXPECTED_SCOPE,
        "passed": passed,
        "failed": failed,
        "results": results,
        "out": str(OUT),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n=== FLOW BROWSER TEST (2 techniques + all metrics) ===")
    print(json.dumps({"passed": passed, "failed": failed, "out": str(OUT)}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
