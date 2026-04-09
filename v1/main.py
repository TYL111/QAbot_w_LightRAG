import os
import asyncio
import numpy as np

from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.llm.gemini import gemini_model_complete, gemini_embed
from lightrag.llm.ollama import ollama_embed

import json



os.environ["GEMINI_API_KEY"] = "YOUR-API"

# 初始化rag
async def initial_rag():
    WORKING_DIR = "./dicken"
    if not os.path.exists(WORKING_DIR):
        os.mkdir(WORKING_DIR)

    # 配置Gemini生成模型
    async def llm_model_func(
        prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
    ) -> str:
        return await gemini_model_complete(
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=os.getenv("GEMINI_API_KEY"),
            model_name="gemini-2.5-flash-lite",
            **kwargs
        )

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        llm_model_name="gemini-2.5-flash-lite",
        embedding_func=EmbeddingFunc(
            embedding_dim=1024,  
            max_token_size=8192,
            func=lambda texts: ollama_embed(texts, model_name='bge-m3')
        ),
    )
    await rag.initialize_storages()

    return rag




import pypdf


async def upload(SOURCE,rag):


    def _get_txt_files():
        if not os.path.exists(SOURCE):
            return False
        txts = [txt for txt in os.listdir(SOURCE) if txt.endswith(".txt")]
        return txts

    def _get_pdf_files():
        if not os.path.exists(SOURCE):
            return False
        pdfs = [pdf for pdf in os.listdir(SOURCE) if pdf.endswith(".pdf")]
        return pdfs

    def _load_or_create_history():
        if not os.path.exists(os.path.join(SOURCE,"upload_history.json")):
            init_data = {"processed_files":[]}
            return init_data
        else:
            with open(os.path.join(SOURCE,"upload_history.json"),"r") as f:
                return json.load(f)
    upload_history = _load_or_create_history()

    #上傳.txt
    txts = _get_txt_files()
    if txts:
        for txt in txts:
            print(f"正在處理{txt}")
            if txt in upload_history["processed_files"]:
                print(f"已處理過 {txt}")
                continue # 跳過處理過
            file_path = os.path.join(SOURCE,txt)
            try:
                with open(file_path,"r",encoding="utf-8") as f:
                    result = await rag.ainsert(f.read(),file_paths = [file_path])
                upload_history["processed_files"].append(txt)
                print(f"{txt}處理成功")
                if not result:
                    raise Exception(f"INSERT ERROR")
            except Exception as e:
                print(f"{txt} {e}")


    # 儲存history
    with open(os.path.join(SOURCE,"upload_history.json"),"w",encoding="utf-8") as f:
        json.dump(upload_history,f)


    #上傳pdf
    # pdfs = _get_pdf_files(SOURCE)
    # if pdfs:
    #     for pdf in pdfs:
    #         print(f"正在處理{pdf}")
    #         file_path = os.path.join(SOURCE,pdf)
    #         try:
    #             reader = pypdf.PdfReader(file_path)
    #             reader
    #         except Exception as e:
    #             print(f"處理檔案 {pdf} 時發生錯誤: {e}")

async def ask_q(q,rag):
    response = await rag.aquery(
        q, 
        param=QueryParam(mode="hybrid", stream=False)
    )
    print(response)
            
async def main():
    rag = await initial_rag()
    await upload("./source",rag)
    # await ask_q("新北市經濟發展局負責人是誰？",rag)


if __name__ == "__main__":

    asyncio.run(main())
