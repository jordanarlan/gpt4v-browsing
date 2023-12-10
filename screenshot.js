const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const url = process.argv[2];
const timeout = 8000;

(async () => {
    const browser = await puppeteer.launch({
        headless: false, // or false if you want to see the browser
    });

    const page = await browser.newPage();

    await page.setViewport({
        width: 1200,
        height: 1200,
        deviceScaleFactor: 1,
    });

    await page.goto(url, {
        waitUntil: "networkidle0",
        timeout: timeout,
    });

    // Wait for additional time if needed, then take the screenshot
    await page.waitForTimeout(timeout - 2000);

    await page.screenshot({
        path: "screenshot.jpg",
        fullPage: true,
    });

    await browser.close();
})();
