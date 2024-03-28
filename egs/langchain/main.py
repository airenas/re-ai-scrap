import argparse
import os
import sys

from langchain.storage import LocalFileStore
from langchain_openai import ChatOpenAI

from ai_scrap.utils.logger import logger
from egs.langchain.tools.company import extract_company_info
from egs.langchain.tools.fill_from_llm import fill_missing_from_llm
from egs.langchain.tools.forms_fields import extract_fields
from egs.langchain.tools.links import get_expected_div_class, extract_news_links
from egs.langchain.tools.submit_form import submit_g_form


class AppContext:

    def __init__(self, llm, store, g_forms_url, context, headless=True, submit_forms=False):
        self.store = store
        self.llm = llm
        self.g_forms_url = g_forms_url
        self.headless = headless
        self.submit_forms = submit_forms
        self.context = context


def extract_links(ctx, url, limit):
    logger.info("extract_links")
    cls = get_expected_div_class(ctx, url)
    return extract_news_links(ctx, url, limit, cls)


def extract_wanted_fields(ctx):
    logger.info(f"extract_wanted_fields from {ctx.g_forms_url}")
    return extract_fields(ctx, ctx.g_forms_url)


def compact(in_data):
    res = None
    for r in in_data:
        if not res or len(r) > len(res):
            res = r
    return res


def collect_data(ctx, l, wanted_fields, i):
    logger.info(f"collect_data for {l.get('news_url')}")
    res = extract_company_info(ctx, l.get('news_url'), wanted_fields, i)
    res = compact(res)
    res = fill_missing_from_llm(ctx, res, wanted_fields, i)
    return res


def submit_form(ctx, l, wanted_fields, data):
    logger.info(f"submit form for {data.get('company_name')}")
    submit_g_form(ctx, data)


def main(argv):
    parser = argparse.ArgumentParser(description="Langchain test file",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--submit-forms", action="store_true", default=False, help="Submit form")
    parser.add_argument("--headless", action="store_true", default=False, help="Use headless browser")
    parser.add_argument("--limit", default=10, type=int, help="Companies to select")
    parser.add_argument("--model", default="gpt-3.5-turbo-0613", type=str, help="LLM Model")
    parser.add_argument("--context", default=3000, type=int, help="LLM context size")
    args = parser.parse_args(args=argv)
    logger.info(f"submit_forms: {args.submit_forms}")
    logger.info(f"headless  : {args.headless}")
    logger.info(f"limit     : {args.limit}")
    logger.info(f"model     : {args.model}")
    logger.info(f"context   : {args.context}")

    os.makedirs(".tmp", exist_ok=True)  # for temp results

    llm = ChatOpenAI(model=args.model, temperature=0)
    store = LocalFileStore(".store")
    ctx = AppContext(llm=llm, store=store,
                     g_forms_url="https://docs.google.com/forms/d/e/1FAIpQLSf_mqy-Rzc3fYyAzLTEBGdsI_scg67n_yr1qK2hrYh3_BDx1A/viewform",
                     headless=args.headless,
                     submit_forms=args.submit_forms,
                     context=args.context)

    logger.info("starting")
    wanted_fields = extract_wanted_fields(ctx)
    links = extract_links(ctx, "https://www.prnewswire.com/news-releases/news-releases-list/", args.limit)

    for (i, l) in enumerate(links):
        data = collect_data(ctx, l, wanted_fields, i)
        submit_form(ctx, l, wanted_fields, data)

    logger.info("done")


if __name__ == "__main__":
    main(sys.argv[1:])
