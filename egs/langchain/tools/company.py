from bs4 import BeautifulSoup
from langchain.chains.openai_functions import create_extraction_chain
from langchain_community.document_transformers.beautiful_soup_transformer import BeautifulSoupTransformer
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_scrap.utils.logger import logger
from ai_scrap.utils.storage import set_store, get_store
from ai_scrap.utils.tmp_file_saver import save_tmp_docs
from egs.langchain.utils.cached_loader import CachedLoader


def extract(llm, content: str, schema: dict):
    logger.info(f"calling llm")
    return create_extraction_chain(schema=schema, llm=llm).invoke(input={"input": content})


def to_field(fi):
    return fi.lower().replace(" ", "_")


def make_schema(fields):
    schema = {
        "properties": {
            "company_name": {"type": "string"},
        },
        "required": ["company_name"],
    }
    for fi in fields:
        f = to_field(fi)
        schema.get("properties")[f] = {"type": "string"}
    return schema


def extract_company_info(ctx, url, fields, i):
    schema = make_schema(fields)
    logger.info(f"loading page {url}")
    loader = CachedLoader(urls=[url], dir=".cache")
    docs = loader.load()
    save_tmp_docs(docs, f"c{i}_docs.txt")
    logger.info(f"loaded")

    soup = BeautifulSoup(docs[0].page_content, 'html.parser')
    texts = ""
    for line in soup.find_all(class_="news-release"):
        texts += str(line)

    bs_transformer = BeautifulSoupTransformer()
    docs = bs_transformer.transform_documents(
        [Document(page_content=texts)], unwanted_tags=["img", "script", "style"]
    )
    save_tmp_docs(docs, f"c{i}_docs_transformed.txt")
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=3000, chunk_overlap=0
    )
    docs = splitter.split_documents(docs)
    save_tmp_docs(docs, f"c{i}_splits.txt")
    logger.info(f"split result into {len(docs)} chunks")
    res = []
    for s in docs:
        e_res = get_store(ctx.store, s.page_content)
        if e_res is None:
            extracted_content = extract(schema=schema, content=s.page_content, llm=ctx.llm)
            e_res = extracted_content.get('text', [])
            set_store(ctx.store, s.page_content, e_res)
        logger.info(f"extracted {len(e_res)} info")
        if isinstance(e_res, list):
            for r in e_res:
                res.append(r)
        else:
            res.append(e_res)
    logger.info(f"extracted fields {len(res)}\n=========================================\n{res}\n")
    return res
