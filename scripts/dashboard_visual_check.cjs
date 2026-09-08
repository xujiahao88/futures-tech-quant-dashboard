const { chromium } = require("playwright");

const url = process.env.DASHBOARD_URL || "http://127.0.0.1:8501";
const password = process.env.DASHBOARD_PASSWORD || "";
const output = process.env.DASHBOARD_SCREENSHOT || "reports/dashboard_preview_final.png";
const viewport = {
  width: Number(process.env.DASHBOARD_VIEWPORT_WIDTH || 1600),
  height: Number(process.env.DASHBOARD_VIEWPORT_HEIGHT || 1000),
};

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.EDGE_PATH ||
      "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  });
  const page = await browser.newPage({ viewport });
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
  await page.locator(".hero h1").waitFor({ state: "visible", timeout: 15000 }).catch(() => null);
  await page.waitForTimeout(3500);

  const bodyText = await page.locator("body").innerText();
  const exceptionCount = await page.locator('[data-testid="stException"]').count();
  const undefinedCount = (bodyText.match(/undefined/g) || []).length;
  const deployButtonCount = await page.getByText("Deploy", { exact: true }).count();
  const heroCount = await page.locator(".hero h1").count();
  const heroVisible = heroCount ? await page.locator(".hero h1").first().isVisible() : false;
  const documentSize = await page.evaluate(() => ({
    width: document.documentElement.scrollWidth,
    height: document.documentElement.scrollHeight,
  }));
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
    viewport,
    exceptionCount,
    undefinedCount,
    deployButtonCount,
    consoleErrorCount: consoleErrors.length,
    bodyTextLength: bodyText.length,
    heroCount,
    heroVisible,
    documentSize,
    sidebarSelectStyle,
  }));
  if (exceptionCount || undefinedCount || consoleErrors.length || !heroVisible) process.exit(1);
})();
