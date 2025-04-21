import asyncio
import base64
from typing import List, Tuple

import aiohttp
from playwright.async_api import Browser, async_playwright

import bubblemaps_bot.utils.bubblemaps_metadata
from bubblemaps_bot import (
    IFRAME_TEMPLATE_URL,
    MAP_AVAILABILITY_URL,
    SCREENSHOT_CACHE_ENABLED,
    VALKEY_ENABLED,
    VALKEY_TTL,
    logger,
)
from bubblemaps_bot.db.screenshot import get_token_screenshot, upsert_token_screenshot
from bubblemaps_bot.utils.bubblemaps_metadata import fetch_token_metadata_update_date
from bubblemaps_bot.utils.valkey import get_cache, set_cache


DEFAULT_VIEWPORT = {"width": 1200, "height": 800}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)


# Persistent browser and concurrency limit
browser: Browser = None
semaphore = asyncio.Semaphore(5)  # limit concurrent screenshot tasks
locks = {}


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


def build_iframe_url(chain: str, token: str) -> str:
    return IFRAME_TEMPLATE_URL.format(chain=chain, token=token)


async def check_map_availability(chain: str, token: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                MAP_AVAILABILITY_URL, params={"chain": chain, "token": token}
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
    lock_key = f"{chain}:{token}"

    logger.debug(
        f"[META MODULE] Using fetch_token_metadata_update_date from {bubblemaps_bot.utils.bubblemaps_metadata.__file__}"
    )

    if lock_key not in locks:
        locks[lock_key] = asyncio.Lock()
    async with locks[lock_key]:
        latest_update = await fetch_token_metadata_update_date(chain, token)
        if not latest_update:
            raise Exception(f"[NO UPDATE INFO] No update date for {chain}:{token}")

        latest_update = latest_update.replace(microsecond=0, tzinfo=None)
        logger.debug(f"[UPDATE DATE] {chain}:{token} - latest_update: {latest_update}")

        if VALKEY_ENABLED and SCREENSHOT_CACHE_ENABLED:
            cached = await get_cache(valkey_key)
            logger.debug(f"[CACHE CHECK] {chain}:{token} - raw cache data: {cached}")
            if cached:
                cached_update_date = cached.get("update_date")
                logger.debug(
                    f"[CACHE CHECK] {chain}:{token} - cached_update_date: {cached_update_date}, expected: {latest_update.isoformat()}"
                )
                if cached_update_date == latest_update.isoformat():
                    logger.info(f"[CACHE HIT] {valkey_key}")
                    return base64.b64decode(cached["image"])
                else:
                    logger.info(
                        f"[CACHE MISS] {valkey_key} - cached_update_date does not match"
                    )
            else:
                logger.info(f"[CACHE MISS] {valkey_key} - no cache entry")

        existing = await get_token_screenshot(chain, token)
        if existing:
            db_update_date = existing.update_date.replace(microsecond=0, tzinfo=None)
            logger.debug(
                f"[DB CHECK] {chain}:{token} - db_update_date: {db_update_date}"
            )
            if db_update_date == latest_update:
                logger.info(f"[DB HIT] Up-to-date screenshot for {chain}:{token}")
                if VALKEY_ENABLED and SCREENSHOT_CACHE_ENABLED:
                    cache_data = {
                        "image": base64.b64encode(existing.image_data).decode("utf-8"),
                        "update_date": latest_update.isoformat(),
                    }
                    logger.debug(f"[CACHE SET] {valkey_key} - TTL: {VALKEY_TTL}")
                    await set_cache(valkey_key, cache_data, ttl=VALKEY_TTL)
                    logger.info(f"Repopulated cache for {valkey_key}")
                return existing.image_data
        else:
            logger.debug(
                f"[DB CHECK] No screenshot found in database for {chain}:{token}"
            )

        is_available = await check_map_availability(chain, token)
        if not is_available:
            raise Exception(
                f"[UNAVAILABLE] BubbleMap not available for {chain}:{token}, skipping screenshot."
            )

        url = IFRAME_TEMPLATE_URL.format(chain=chain, token=token)

        global browser
        if not browser or not browser.is_connected():
            await init_browser()

        try:
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
                        cache_data = {
                            "image": base64.b64encode(screenshot).decode("utf-8"),
                            "update_date": latest_update.isoformat(),
                        }
                        logger.debug(f"[CACHE SET] {valkey_key} - TTL: {VALKEY_TTL}")
                        await set_cache(valkey_key, cache_data, ttl=VALKEY_TTL)
                        logger.info(f"Cached screenshot under {valkey_key}")

                    await upsert_token_screenshot(
                        chain, token, latest_update, screenshot
                    )
                    logger.info(f"Saved screenshot to database for {chain}:{token}")

                    return screenshot

                finally:
                    await page.close()
                    await context.close()

        except Exception as e:
            logger.error(f"SVG capture failed: {e}")
            raise


async def capture_multiple_bubblemaps(tasks: List[Tuple[str, str]]) -> List[bytes]:
    async def capture_task(chain: str, token: str) -> bytes:
        try:
            return await capture_bubblemap(chain, token)
        except Exception as e:
            logger.error(f"Failed to capture screenshot for {chain}:{token}: {e}")
            return None

    task_list = [capture_task(chain, token) for chain, token in tasks]
    results = await asyncio.gather(*task_list, return_exceptions=True)
    return [r for r in results if r is not None]
