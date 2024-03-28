import argparse
import os
import sys

from langchain.storage import LocalFileStore
from langchain_openai import ChatOpenAI

from tools.company import extract_company_info
from tools.forms_fields import extract_fields
from tools.links import extract_news_links, get_expected_div_class
from tools.submit_form import submit_g_form
from utils.logger import logger


class AppContext:

    def __init__(self, llm, store, g_forms_url, headless=True):
        self.store = store
        self.llm = llm
        self.g_forms_url = g_forms_url
        self.headless = headless


# def aa():
#     planner = (
#             ChatPromptTemplate.from_template("Generate an argument about: {input}")
#             | ChatOpenAI()
#             | StrOutputParser()
#             | {"base_response": RunnablePassthrough()}
#     )
#
#     arguments_for = (
#             ChatPromptTemplate.from_template(
#                 "List the pros or positive aspects of {base_response}"
#             )
#             | ChatOpenAI()
#             | StrOutputParser()
#     )
#     arguments_against = (
#             ChatPromptTemplate.from_template(
#                 "List the cons or negative aspects of {base_response}"
#             )
#             | ChatOpenAI()
#             | StrOutputParser()
#     )
#
#     final_responder = (
#             ChatPromptTemplate.from_messages(
#                 [
#                     ("ai", "{original_response}"),
#                     ("human", "Pros:\n{results_1}\n\nCons:\n{results_2}"),
#                     ("system", "Generate a final response given the critique"),
#                 ]
#             )
#             | ChatOpenAI()
#             | StrOutputParser()
#     )
#
#     chain = (
#             planner
#             | {
#                 "results_1": arguments_for,
#                 "results_2": arguments_against,
#                 "original_response": itemgetter("base_response"),
#             }
#             | final_responder
#     )
#
#     result = chain.invoke({"input": "scrum"})
#     print(result)


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
    return compact(res)


def submit_form(ctx, l, wanted_fields, data):
    logger.info(f"submit form for {data.get('company_name')}")
    submit_g_form(ctx, ctx.g_forms_url)


def main(argv):
    parser = argparse.ArgumentParser(description="Langchain test file",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    args = parser.parse_args(args=argv)
    logger.info("starting")
    llm = ChatOpenAI(model="gpt-3.5-turbo-0613", temperature=0)
    store = LocalFileStore(".store")
    os.makedirs(".tmp", exist_ok=True)

    ctx = AppContext(llm=llm, store=store,
                     g_forms_url="https://docs.google.com/forms/d/e/1FAIpQLSf_mqy-Rzc3fYyAzLTEBGdsI_scg67n_yr1qK2hrYh3_BDx1A/viewform")

    wanted_fields = extract_wanted_fields(ctx)
    links = extract_links(ctx, "https://www.prnewswire.com/news-releases/news-releases-list/", 5)

    for (i, l) in enumerate(links):
        data = collect_data(ctx, l, wanted_fields, i)
        submit_form(ctx, l, wanted_fields, data)

    logger.info("done")


if __name__ == "__main__":
    main(sys.argv[1:])
