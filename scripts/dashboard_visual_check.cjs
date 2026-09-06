const { chromium } = require("playwright");

const url = process.env.DASHBOARD_URL || "http://127.0.0.1:8501";
const password = process.env.DASHBOARD_PASSWORD || "";
const output = process.env.DASHBOARD_SCREENSHOT || "reports/dashboard_preview_final.png";

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.EDGE_PATH ||
      "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const consoleErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
  if (password) {
    const passwordInput = page.locator('input[type="password"]');
    try {
      await passwordInput.waitFor({ state: "visible", timeout: 15000 });
      await passwordInput.fill(password);
      await page.getByRole("button", { name: /进入看板/ }).click();
      await passwordInput.waitFor({ state: "detached", timeout: 30000 });
    } catch (error) {
      if (await passwordInput.count()) throw error;
    }
  }
  await page.locator('[data-testid="stAppViewContainer"]').waitFor({ timeout: 60000 });
  await page.waitForTimeout(3500);

  const bodyText = await page.locator("body").innerText();
  const exceptionCount = await page.locator('[data-testid="stException"]').count();
  const undefinedCount = (bodyText.match(/undefined/g) || []).length;
  const deployButtonCount = await page.getByText("Deploy", { exact: true }).count();
  const sidebarSelect = page.locator('[data-testid="stSidebar"] [role="combobox"]');
  const sidebarSelectStyle = await sidebarSelect.count() ? await sidebarSelect.first().evaluate((el) => {
    const style = getComputedStyle(el);
    return { color: style.color, backgroundColor: style.backgroundColor, opacity: style.opacity };
  }) : null;
  await page.screenshot({ path: output, fullPage: true });
  await browser.close();

  console.log(JSON.stringify({
    url,
    output,
    exceptionCount,
    undefinedCount,
    deployButtonCount,
    consoleErrorCount: consoleErrors.length,
    sidebarSelectStyle,
  }));
  if (exceptionCount || undefinedCount || consoleErrors.length) process.exit(1);
})();
