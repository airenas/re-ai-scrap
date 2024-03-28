import time

from playwright.sync_api import sync_playwright

from ai_scrap.utils.logger import logger


def submit_g_form(ctx, param):
    with sync_playwright() as p:
        with p.chromium.launch(headless=ctx.headless) as browser:
            context = browser.new_context(locale="en-US")
            page = context.new_page()
            page.goto(param)
            input_elements = page.query_selector_all('input[type],textarea')
            logger.info(f"opened page")
            # Set value to each input element
            logger.info(f"elements {len(input_elements)}")
            ic = 0
            for (i, input_element) in enumerate(input_elements):
                t_a = input_element.get_attribute('type')
                logger.info(f"element {input_element}: {t_a}")
                if t_a == "text":
                    logger.info(f"Element {i} is active")
                    input_element.fill(f"input {ic}")
                    ic += 1
            logger.info(f"submit?")
            submit_button = page.query_selector('span:has-text("Pateikti")')
            if submit_button:
                if ctx.submit_forms:
                    submit_button.click()
                    logger.info(f"click")
                else:
                    logger.info(f"skip click")

            else:
                logger.warn(f"not submit found")

            logger.info(f"sleep")
            time.sleep(3)
            browser.close()
