const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const url = process.argv[2];
const pageLoadTimeout = 10000; // 10 seconds for page load
const extraWaitTime = 5000; // 5 seconds extra wait after page load

(async () => {
    let browser; // Declare browser outside of the try-catch block

    try {
        browser = await puppeteer.launch({
            headless: false, // Set to false to see the browser
            args: ['--no-sandbox', '--disable-setuid-sandbox'], // Added for better stability in different environments
        });

        const page = await browser.newPage();

        await page.setViewport({
            width: 1200,
            height: 1200,
            deviceScaleFactor: 1,
        });

        await page.goto(url, {
            waitUntil: "networkidle0",
            timeout: pageLoadTimeout,
        });

        // Wait for additional time if needed, then take the screenshot
        await page.waitForTimeout(extraWaitTime);

        await page.screenshot({
            path: "screenshot.jpg",
            fullPage: true,
        });

        console.log("Screenshot saved as 'screenshot.jpg'");
    } catch (error) {
        console.error("An error occurred:", error);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
})();
