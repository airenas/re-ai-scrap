from collections import Counter

from bs4 import BeautifulSoup
from langchain.chains.openai_functions import create_extraction_chain
from langchain_community.document_transformers.beautiful_soup_transformer import BeautifulSoupTransformer
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_scrap.utils.logger import logger
from ai_scrap.utils.storage import get_store, set_store
from egs.langchain.utils.cached_loader import CachedLoader
from ai_scrap.utils.tmp_file_saver import save_tmp_docs

schema = {
    "properties": {
        "news_article_title": {"type": "string"},
        "news_url": {"type": "string"},
    },
    "required": ["news_article_title", "news_url"],
}


def extract(llm, content: str, schema: dict):
    logger.info(f"calling llm")
    return create_extraction_chain(schema=schema, llm=llm).invoke(input={"input": content})


def unique_divs(divs):
    res, was = [], set()
    for d in divs:
        if d not in was:
            res.append(d)
            was.update(d.descendants)
    return res


def extract_news_links(ctx, urls, limit, cls):
    logger.info(f"loading pages {urls}")
    loader = CachedLoader(urls=[urls], dir=".cache")
    docs = loader.load()
    save_tmp_docs(docs, "l_docs.txt")
    logger.info(f"loaded")

    soup = BeautifulSoup(docs[0].page_content, 'html.parser')
    texts = ""

    divs = soup.find_all(class_=cls)
    divs = unique_divs(divs)
    for line in divs:
        texts += str(line)

    bs_transformer = BeautifulSoupTransformer()
    docs = bs_transformer.transform_documents(
        [Document(page_content=texts)], unwanted_tags=["img", "script", "style"]
    )
    save_tmp_docs(docs, "l_docs_transformed.txt")
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=ctx.context, chunk_overlap=0
    )
    docs = splitter.split_documents(docs)
    save_tmp_docs(docs, "l_splits.txt")
    logger.info(f"split result into {len(docs)} chunks")
    res = []
    for d in docs:
        e_res = get_store(ctx.store, d.page_content)
        if e_res is None:
            extracted_content = extract(schema=schema, content=d.page_content, llm=ctx.llm)
            e_res = extracted_content.get('text', [])
            set_store(ctx.store, d.page_content, e_res)
        logger.info(f"extracted {len(e_res)} articles")
        for t in e_res:
            res.append(t)
            if len(res) >= limit:
                break
        if len(res) >= limit:
            break
    logger.info(f"extracted articles {len(res)}\n=========================================\n{res}\n")
    return res


def get_most_expected_div_name(counter, llm_res):
    if len(counter) == 0:
        return ""
    res = counter.most_common(1)[0][0]
    res_len = 0
    for class_name, _ in counter.most_common():
        if class_name in llm_res and len(class_name) > res_len:
            res, res_len = class_name, len(class_name)
    return res


def get_expected_div_class(ctx, urls):
    logger.info(f"loading pages {urls}")
    loader = CachedLoader(urls=[urls], dir=".cache")
    docs = loader.load()
    save_tmp_docs(docs, "l_docs.txt")
    logger.info(f"loaded")

    soup = BeautifulSoup(docs[0].page_content, 'html.parser')
    divs = soup.select('div[class]')
    counter = Counter()
    for div in divs:
        classes = div['class']
        for c in classes:
            counter.update([c])
    logger.info(f"Most common elements: {counter.most_common(20)}")

    res = ""
    if len(counter) > 0:
        llm_res = get_store(ctx.store, f"{counter.most_common(20)}")
        if llm_res is None:
            prompt = PromptTemplate.from_template(
                "I want to extract news articles from a page. Here is a list of tuples (<div class name>: <count>): {classes}\n"
                "What is the most probable class name for an article based on counter and class name?.\n"
                "Return just one class name without explanation"
            )
            runnable = prompt | ctx.llm | StrOutputParser()
            llm_res = runnable.invoke({"classes": counter.most_common(20)})
            set_store(ctx.store, f"{counter.most_common(20)}", llm_res)
        logger.info(f"llm_res {llm_res}")
        res = get_most_expected_div_name(counter, llm_res)
        logger.info(f"most expected class '{res}'")

    return res
