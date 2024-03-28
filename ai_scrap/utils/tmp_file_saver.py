def save_tmp_docs(docs, f_name):
    with open(f".tmp/{f_name}", 'w') as f:
        for (i, d) in enumerate(docs):
            if i > 0:
                f.write("\n==============================\n\n")
            f.write(d.page_content)
