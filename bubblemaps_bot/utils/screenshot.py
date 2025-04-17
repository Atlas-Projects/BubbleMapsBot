import asyncio
import base64
import logging

import aiohttp
from playwright.async_api import Browser, async_playwright
from telegram.ext import Application

from bubblemaps_bot import SCREENSHOT_CACHE_ENABLED, VALKEY_ENABLED, VALKEY_TTL
from bubblemaps_bot.utils.valkey import get_cache, set_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_VIEWPORT = {"width": 1200, "height": 800}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

IFRAME_URL_TEMPLATE = "https://app.bubblemaps.io/{chain}/token/{token}"
MAP_AVAILABILITY_API = "https://api-legacy.bubblemaps.io/map-availability"

# Persistent browser and concurrency limit
browser: Browser = None
semaphore = asyncio.Semaphore(5)  # limit concurrent screenshot tasks


async def init_browser():
    global browser, playwright
    if not browser:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
            ],
        )


async def close_browser(_: Application):
    global browser, playwright
    if browser:
        try:
            await browser.close()
            await playwright.stop()  # Stop the playwright instance
            browser = None  # Reset browser variable
        except Exception as e:
            print(f"Error while closing the browser: {e}")
    else:
        print("Browser is already closed or not initialized.")


def build_iframe_url(chain: str, token: str) -> str:
    return IFRAME_URL_TEMPLATE.format(chain=chain, token=token)


async def check_map_availability(chain: str, token: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                MAP_AVAILABILITY_API, params={"chain": chain, "token": token}
            ) as resp:
                data = await resp.json()
                if data.get("status") == "OK":
                    return data.get("availability", False)
                else:
                    logger.warning(f"[AVAILABILITY] KO: {data.get('message')}")
                    return False
    except Exception as e:
        logger.error(f"[AVAILABILITY CHECK ERROR] {e}")
        return False


async def capture_bubblemap(chain: str, token: str, delay: int = 10) -> bytes:
    valkey_key = f"bubblemap:screenshot:{chain}:{token}"

    if VALKEY_ENABLED and SCREENSHOT_CACHE_ENABLED:
        cached = await get_cache(valkey_key)
        if cached and "image" in cached:
            logger.info(f"[CACHE HIT] {valkey_key}")
            return base64.b64decode(cached["image"])
        else:
            logger.info(f"[CACHE MISS] {valkey_key}")

    # ✅ Check availability before screenshot
    is_available = await check_map_availability(chain, token)
    if not is_available:
        raise Exception(
            f"[UNAVAILABLE] BubbleMap not available for {chain}:{token}, skipping screenshot."
        )

    url = f"https://app.bubblemaps.io/{chain}/token/{token}"

    try:
        # Limit concurrent executions
        async with semaphore:
            context = await browser.new_context(
                viewport=DEFAULT_VIEWPORT,
                user_agent=DEFAULT_USER_AGENT,
                java_script_enabled=True,
            )
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(5)

                try:
                    await page.evaluate(
                        """
                        () => {
                            const elements = Array.from(document.querySelectorAll("*"));
                            for (const el of elements) {
                                if (el.innerText && el.innerText.trim() === 'CLOSE') {
                                    el.click();
                                }
                            }
                        }
                        """
                    )
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.warning(f"Failed to close popup: {e}")

                await page.evaluate(
                    """
                    () => {
                        const banner = document.querySelector('div.fundraising-banner.--desktop');
                        if (banner) banner.remove();

                        const header = document.querySelector('header.mdc-top-app-bar.mdc-top-app-bar--fixed');
                        if (header) header.style.display = 'flex';
                    }
                    """
                )

                svg_element = await page.query_selector("#svg")
                if not svg_element:
                    raise Exception("SVG element with id='svg' not found")

                await svg_element.evaluate(
                    """
                    (svg) => {
                        svg.style.visibility = 'visible';
                        svg.style.opacity = '1';
                    }
                    """
                )

                await asyncio.sleep(delay)

                bounding_box = await svg_element.bounding_box()
                if not bounding_box:
                    raise Exception("SVG bounding box not available")

                screenshot = await svg_element.screenshot(type="png")

                if VALKEY_ENABLED and SCREENSHOT_CACHE_ENABLED:
                    await set_cache(
                        valkey_key,
                        {"image": base64.b64encode(screenshot).decode("utf-8")},
                        ttl=VALKEY_TTL,
                    )
                    logger.info(f"Cached screenshot under {valkey_key}")

                return screenshot

            finally:
                await page.close()
                await context.close()

    except Exception as e:
        logger.error(f"SVG capture failed: {e}")
        raise


async def capture_multiple_bubblemaps(tasks):
    # Prepare all tasks for concurrent execution
    return await asyncio.gather(*tasks)
