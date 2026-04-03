import os
import asyncio
import numpy as np

from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.llm.gemini import gemini_model_complete, gemini_embed
from lightrag.llm.ollama import ollama_embed




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
            model_name="gemini-2.5-flash",
            **kwargs
        )

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        llm_model_name="gemini-2.5-flash",
        embedding_func=EmbeddingFunc(
            embedding_dim=1024,  
            max_token_size=8192,
            func=lambda texts: ollama_embed(texts, model_name='bge-m3')
        ),
    )
    await rag.initialize_storages()

    return rag

def _get_txt_files(SOURCE):
    if not os.path.exists(SOURCE):
        return False
    txts = [txt for txt in os.listdir(SOURCE) if txt.endswith(".txt")]
    return txts

def _get_pdf_files(SOURCE):
    if not os.path.exists(SOURCE):
        return False
    pdfs = [pdf for pdf in os.listdir(SOURCE) if pdf.endswith(".pdf")]
    return pdfs

import pypdf
async def upload(SOURCE,rag):
    import shutil
    PROCESSED_DIR = "./processed"
    if not os.path.exists(PROCESSED_DIR):
        os.mkdir(PROCESSED_DIR)

    #上傳.txt
    txts = _get_txt_files(SOURCE)
    if txts:
        for txt in txts:
            print(f"正在處理{txt}")
            file_path = os.path.join(SOURCE,txt)
            try:
                #####################################################
                ### LightRAG報錯不會跳exception 檔案照樣會移
                #####################################################
                with open(file_path,"r",encoding="utf-8") as f:
                    await rag.ainsert(f.read(),file_path = os.path.join(PROCESSED_DIR,txt))
                shutil.move(file_path,os.path.join(PROCESSED_DIR,txt))
                print(f"{txt}處理成功 移動至 {PROCESSED_DIR}")
            except Exception as e:
                print(f"處理檔案 {txt} 時發生錯誤: {e}")
    
    #上傳pdf
    pdfs = _get_pdf_files(SOURCE)
    if pdfs:
        for pdf in pdfs:
            print(f"正在處理{pdf}")
            file_path = os.path.join(SOURCE,pdf)
            try:
                reader = pypdf.PdfReader(file_path)
                reader
            except Exception as e:
                print(f"處理檔案 {pdf} 時發生錯誤: {e}")

            
async def main():
    rag = await initial_rag()
    await upload("./source",rag)

    # response = await rag.aquery(
    #     "新北市經濟發展局負責人是誰？", 
    #     param=QueryParam(mode="hybrid", stream=False)
    # )
    # print(response)
if __name__ == "__main__":

    asyncio.run(main())