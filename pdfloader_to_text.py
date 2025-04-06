from langchain_community.document_loaders import PyPDFLoader

def pdfloader_to_text(path):
    loader = PyPDFLoader(
        file_path = path,
        #password = "my-pasword",
        extract_images = False,
        # headers = None
        # extraction_mode = "plain",
        # extraction_kwargs = None,
    )
    docs = []
    docs_lazy = loader.lazy_load()

    # async variant:
    # docs_lazy = await loader.alazy_load()

    for doc in docs_lazy:
        docs.append(doc)
    ret_str=""""""
    for d in docs:
        ret_str+=d.page_content+"\n"
    return ret_str