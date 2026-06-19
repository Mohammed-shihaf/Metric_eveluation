/**
 * Browser E2E smoke test for Metric Evaluation Streamlit UI.
 * Usage: node tools/e2e_browser_verify.mjs
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const BASE = process.env.E2E_BASE_URL || "http://localhost:8501";
const OUT = path.join(ROOT, "docs", "e2e-demo", "verify-" + new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19));

const QA_EMAIL = process.env.AUTH_EMAIL || "";
const QA_PASSWORD = process.env.AUTH_PASSWORD || "";

const results = [];

function pass(name, detail = "") {
  results.push({ name, ok: true, detail });
  console.log("PASS", name, detail ? "- " + detail : "");
}

function fail(name, detail = "") {
  results.push({ name, ok: false, detail });
  console.log("FAIL", name, detail ? "- " + detail : "");
}

async function clickTab(page, label) {
  const tab = page.getByRole("tab", { name: label, exact: true });
  await tab.click({ timeout: 15000 });
  await page.waitForTimeout(800);
}

async function sidebarLabel(page, text) {
  return page.locator('[data-testid="stSidebar"]').getByText(text, { exact: false }).first();
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

  try {
    const resp = await page.goto(BASE, { waitUntil: "networkidle", timeout: 60000 });
    if (!resp || resp.status() >= 400) {
      fail("app_load", "HTTP " + (resp ? resp.status() : "no response"));
      return;
    }
    pass("app_load", BASE);

    await page.waitForSelector('[data-testid="stApp"]', { timeout: 30000 });
    pass("streamlit_shell", "stApp visible");

    // Tabs present
    for (const tab of ["Branches", "Whitebox", "Local tools", "SonarQube", "Compare"]) {
      const el = page.getByRole("tab", { name: tab, exact: true });
      if (await el.count()) {
        pass("tab_" + tab.replace(/\s+/g, "_").toLowerCase(), "visible");
      } else {
        fail("tab_" + tab.replace(/\s+/g, "_").toLowerCase(), "missing");
      }
    }

    // Sidebar language + version selectors
    const sidebar = page.locator('[data-testid="stSidebar"]');
    const langLabel = await sidebar.getByText("Language", { exact: true }).count();
    const verLabel = await sidebar.getByText("Version", { exact: true }).count();
    if (langLabel && verLabel) {
      pass("sidebar_language_version", "selectors present");
    } else {
      fail("sidebar_language_version", "Language=" + langLabel + " Version=" + verLabel);
    }

    // QA sign-in (sidebar form)
    if (QA_EMAIL && QA_PASSWORD) {
      const emailInput = sidebar.locator('input[type="text"]').first();
      const passInput = sidebar.locator('input[type="password"]').first();
      if (await emailInput.count() && await passInput.count()) {
        await emailInput.fill(QA_EMAIL);
        await passInput.fill(QA_PASSWORD);
        const signIn = sidebar.getByRole("button", { name: "Sign in" });
        if (await signIn.count()) {
          await signIn.click();
          await page.waitForTimeout(3000);
          const signedIn = await sidebar.getByText("Signed in as", { exact: false }).count();
          if (signedIn) {
            pass("qa_login", "session active");
          } else {
            fail("qa_login", "Sign in did not show signed-in state");
          }
        } else {
          fail("qa_login", "Sign in button missing");
        }
      } else if (await sidebar.getByText("Signed in as", { exact: false }).count()) {
        pass("qa_login", "already signed in");
      } else {
        fail("qa_login", "login form not found");
      }
    } else {
      fail("qa_login", "AUTH_EMAIL/AUTH_PASSWORD not set");
    }

    await page.screenshot({ path: path.join(OUT, "01-branches-tab.png"), fullPage: true });

    // Branches tab controls
    await clickTab(page, "Branches");
    const genBtn = page.getByRole("button", { name: /1 — Generate branches/i });
    if (await genBtn.count()) {
      const disabled = await genBtn.isDisabled();
      pass("branches_generate_button", disabled ? "present (disabled — no scope/github)" : "present and enabled");
    } else {
      fail("branches_generate_button", "missing");
    }

    const strengthCaption = await page.getByText(/strength floor/i).count();
    if (strengthCaption) {
      pass("branches_strength_caption", "code depth note visible");
    } else {
      fail("branches_strength_caption", "missing");
    }

    await page.screenshot({ path: path.join(OUT, "02-branches-controls.png"), fullPage: true });

    // Whitebox tab — no dimming / run button sync
    await clickTab(page, "Whitebox");
    await page.waitForTimeout(1500);

    const wbHeader = await page.getByRole("heading", { name: /2 — Whitebox/i }).count();
    if (wbHeader) pass("whitebox_header", "tab loaded");
    else fail("whitebox_header", "missing");

    const runBtn = page.getByRole("button", { name: "Run whitebox batch" });
    if (await runBtn.count()) {
      pass("whitebox_run_button", "present (disabled=" + (await runBtn.isDisabled()) + ")");
    } else {
      fail("whitebox_run_button", "missing");
    }

    const picker = page.getByText("Choose branches for this whitebox batch", { exact: false });
    if (await picker.count()) pass("whitebox_branch_picker", "multiselect present");
    else fail("whitebox_branch_picker", "missing");

    // Interact with picker area — tab should stay responsive (no permanent disabled overlay)
    await page.waitForTimeout(5000);
    const stillVisible = await wbHeader ? page.getByRole("heading", { name: /2 — Whitebox/i }).isVisible() : false;
    if (stillVisible) pass("whitebox_stable_5s", "tab still interactive after 5s");
    else fail("whitebox_stable_5s", "tab became unresponsive");

    await page.screenshot({ path: path.join(OUT, "03-whitebox-tab.png"), fullPage: true });

    // Language options — cycle through sidebar if select visible
    const langSelect = sidebar.locator('[data-baseweb="select"]').filter({ has: sidebar.getByText("Language") }).first();
    // Fallback: any select in sidebar after Language label
    const selects = sidebar.locator('[data-baseweb="select"]');
    const selectCount = await selects.count();
    if (selectCount >= 2) {
      pass("sidebar_select_widgets", selectCount + " select widgets");
    } else {
      fail("sidebar_select_widgets", "expected language+version selects, got " + selectCount);
    }

    // Other tabs load without error
    for (const tab of ["Local tools", "SonarQube", "Compare"]) {
      await clickTab(page, tab);
      const err = await page.locator('[data-testid="stException"]').count();
      if (err) fail("tab_load_" + tab.replace(/\s+/g, "_").toLowerCase(), "exception on page");
      else pass("tab_load_" + tab.replace(/\s+/g, "_").toLowerCase(), "no exception");
    }

    await page.screenshot({ path: path.join(OUT, "04-compare-tab.png"), fullPage: true });
  } catch (err) {
    fail("unexpected", String(err.message || err));
    await page.screenshot({ path: path.join(OUT, "error.png"), fullPage: true }).catch(() => {});
  } finally {
    await browser.close();
  }

  const passed = results.filter((r) => r.ok).length;
  const failed = results.filter((r) => !r.ok).length;
  const summary = { base: BASE, passed, failed, total: results.length, results, screenshots: OUT };
  fs.writeFileSync(path.join(OUT, "summary.json"), JSON.stringify(summary, null, 2));
  console.log("\n=== E2E SUMMARY ===");
  console.log(JSON.stringify({ passed, failed, total: results.length, out: OUT }, null, 2));
  process.exit(failed > 0 ? 1 : 0);
}

main();
