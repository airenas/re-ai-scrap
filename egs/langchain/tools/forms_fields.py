from langchain.chains.openai_functions import create_extraction_chain
from langchain_community.document_transformers.beautiful_soup_transformer import BeautifulSoupTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_scrap.utils.logger import logger
from ai_scrap.utils.storage import get_store, set_store
from ai_scrap.utils.tmp_file_saver import save_tmp_docs
from egs.langchain.utils.cached_loader import CachedLoader

schema = {
    "properties": {
        "input_name": {"type": "string"},
    },
    "required": ["input_name"],
}


def extract(llm, content: str, schema: dict):
    logger.info(f"calling llm")
    return create_extraction_chain(schema=schema, llm=llm).invoke(input={"input": content})


def field_names(res):
    return [f.get("input_name", "") for f in res if f.get("input_name")]


def extract_fields(ctx, urls):
    logger.info(f"loading pages {urls}")
    loader = CachedLoader(urls=[urls], dir=".cache")
    docs = loader.load()
    save_tmp_docs(docs, "g_docs.txt")
    logger.info(f"loaded")

    bs_transformer = BeautifulSoupTransformer()
    docs_transformed = bs_transformer.transform_documents(
        docs, unwanted_tags=["img", "script", "style", "meta"]
    )
    save_tmp_docs(docs_transformed, "g_docs_transformed.txt")
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=ctx.context, chunk_overlap=0
    )
    splits = splitter.split_documents(docs_transformed)
    save_tmp_docs(splits, "g_splits.txt")
    logger.info(f"split result into {len(splits)} chunks")
    res = []
    for s in splits:
        e_res = get_store(ctx.store, s.page_content)
        if e_res is None:
            extracted_content = extract(schema=schema, content=s.page_content, llm=ctx.llm)
            e_res = extracted_content.get('text', [])
            set_store(ctx.store, s.page_content, e_res)
        logger.info(f"extracted {len(e_res)} articles")
        for t in e_res:
            res.append(t)
        if len(res) >= 10:
            break
    logger.info(f"extracted fields {len(res)}\n=========================================\n{res}\n")
    return field_names(res)
