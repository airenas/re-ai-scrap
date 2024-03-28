from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from ai_scrap.utils.logger import logger
from ai_scrap.utils.storage import set_store, get_store
from ai_scrap.utils.timer import Timer
from egs.langchain.tools.company import to_field


def fill_missing_from_llm(ctx, data, fields, i):
    llm_res = get_store(ctx.store, f"{data}")
    if llm_res is None:
        logger.info(f"calling llm")
        prompt = PromptTemplate.from_template(
            "Could you fill missing info about the company {company} into json fields:\n{data}\n\n"
            "Respond with json structure. Add no comments, just a valid json output."
        )
        runnable = prompt | ctx.llm | JsonOutputParser()
        cleaned = {to_field(k): "" for k in fields}
        with Timer("llm"):
            llm_res = runnable.invoke({"data": cleaned, "company": data.get("company_name")})
        set_store(ctx.store, f"{data}", llm_res)
    logger.info(f"was  =========================================\n{data}\n")
    logger.info(f"new  =========================================\n{llm_res}\n")
    return combine(ctx, data, llm_res)


def fix_combined(llm_res):
    res = {}
    for k, v in llm_res.items():
        if isinstance(v, list):
            if len(v) > 0:
                v = v[0]
        res[k] = v
    return res


def combine(ctx, data, new_data):
    llm_res = get_store(ctx.store, f"com-{data}")
    if llm_res is None:
        logger.info(f"calling llm")
        prompt = PromptTemplate.from_template(
            "Could you combine information from:\n{new}\ninto:\n{data}\n adding missing or more correct fields."
            "Use just information that is provided."
            "Respond with json structure. Add no comments, just a valid json output."
        )
        runnable = prompt | ctx.llm | JsonOutputParser()
        llm_res = runnable.invoke({"data": data, "new": new_data})
        set_store(ctx.store, f"com-{data}", llm_res)
    logger.info(f"was       =========================================\n{data}\n")
    logger.info(f"combined  =========================================\n{llm_res}\n")
    return fix_combined(llm_res)
