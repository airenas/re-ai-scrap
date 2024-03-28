import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from ai_scrap.utils.logger import logger


def selector_for(el):
    classes = el.get("class")
    str_cl = ".".join(classes)
    descr = el.get("aria-describedby")
    str_descr = ""
    if len(descr) > 0:
        str_descr = f'[aria-describedby="{descr}"]'
    str_cl = ".".join(classes)
    return f"{el.name}{str_descr}.{str_cl}"


def matches_nearest(el, key, other_keys):
    parent = el.find_parent()
    while parent is not None:
        text = parent.get_text(strip=True)
        text = text.lower().replace(" ", "_")
        if key in text:  ## parent has text
            for k in other_keys:
                if k in text:
                    return False  # matches others to
            return True
        parent = parent.find_parent()
    return False


def get_selector(soup, key, all_keys):
    elements = soup.find_all(['input', 'textarea'])
    filtered = []
    for el in elements:
        if "type" in el.attrs:
            if el.attrs["type"] == "text":
                filtered.append(el)
        elif el.name == "textarea":
            filtered.append(el)
    other_keys = set()
    for k in all_keys:
        if k != key:
            other_keys.add(k)
    for el in filtered:
        if matches_nearest(el, key, other_keys):
            return selector_for(el)
    return ""


def submit_g_form(ctx, params):
    with sync_playwright() as p:
        with p.chromium.launch(headless=ctx.headless) as browser:
            context = browser.new_context(locale="en-US", geolocation={'latitude': 40.71, 'longitude': -74.006})
            page = context.new_page()
            page.goto(ctx.g_forms_url)
            logger.info(f"opened page")
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            for (k, value) in params.items():
                if value:
                    selector = get_selector(soup, k, params.keys())
                    if selector:
                        el = page.query_selector(selector)
                        if el:
                            el.scroll_into_view_if_needed()
                        page.fill(selector, value)
                        if not ctx.headless:
                            time.sleep(1)
                    else:
                        logger.warn(f"can't fill {k} - no input found")
            logger.info(f"submit")
            el = page.query_selector('span:has-text("Submit"),span:has-text("Pateikti")')
            if el:
                if el:
                    el.scroll_into_view_if_needed()
                if ctx.submit_forms:
                    el.click()
                    logger.info(f"click")
                else:
                    logger.info(f"skip click")

            else:
                logger.warn(f"not submit found")

            if not ctx.headless:
                logger.info(f"sleep")
                time.sleep(3)
            browser.close()
