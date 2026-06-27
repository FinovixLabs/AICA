from pathlib import Path
import os
from langchain_openai import ChatOpenAI
#for setting up keyword search
from langchain_community.retrievers import BM25Retriever
#for ensemble retriever setup 
from langchain_classic.retrievers import EnsembleRetriever
#for creating document list
from langchain_core.documents import Document
from langchain_classic.retrievers import (
    MultiQueryRetriever,
    ContextualCompressionRetriever,
    EnsembleRetriever,
    ParentDocumentRetriever
)
# DOCUMENT COMPRESSOR
from langchain_classic.retrievers.document_compressors import (
    LLMChainExtractor
)
# PROMPTS
from langchain_core.prompts import ChatPromptTemplate
# OUTPUT PARSERS
from langchain_core.output_parsers import StrOutputParser
# RUNNABLES
from langchain_core.runnables import RunnablePassthrough
# ENV
from dotenv import load_dotenv
load_dotenv()
# LOGGING
import logging
# Supabase client
from supabase import create_client

from typing import Any,cast
# LangChain Supabase vector store
from langchain_community.vectorstores import SupabaseVectorStore
from ingest import EmbeddingService
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# at server startup
# initialize the client
class RetrieverEngine:
    def __init__(self,collection_name):
        self.collection_name=collection_name
        # supabase client
        self.supabase = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"]
        )
        # get the collection's UUID first
        coll = self.supabase.table("langchain_pg_collection")\
            .select("uuid").eq("name", collection_name).execute()
        coll_rows = cast(list[dict[str, Any]], coll.data)

        collection_id = coll_rows[0]["uuid"]
        
        # filter chunks by it
        response = self.supabase.table("langchain_pg_embedding")\
            .select("document, cmetadata")\
            .eq("collection_id", collection_id)\
            .execute()
        
        rows= cast(list[dict[str, Any]] , response.data)
        self.chunks = [
            Document(
                page_content=row["document"] or "",
                metadata=row["cmetadata"] or {}
            )
            for row in rows
        ]

        # vector retriever
        self.vectorstore = EmbeddingService(collection_name=collection_name).get_vectorstore()   

    def llm(self):
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def similarity_search_retriever(self):
        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )

    def keyword_search_retriever(self):
        bm25 = BM25Retriever.from_documents(self.chunks)   # ← self.chunks, not response
        bm25.k = 3
        return bm25
    
    def ensemble_retriever_setup(self):
        #SETUP ENSEMBLE RETRIEVER
        bm25_retriever = self.keyword_search_retriever()
        vector_retriever = self.similarity_search_retriever()
        return EnsembleRetriever(
            retrievers=[bm25_retriever,vector_retriever],
            weights=[0.5,0.5]
        )
        
    def multiquery_retriever_setup(self):
        ensemble = self.ensemble_retriever_setup()
        return MultiQueryRetriever.from_llm(
            retriever=ensemble,
            llm=self.llm()
        )
        
    def compressor_retriever_setup(self):
        compressor=LLMChainExtractor.from_llm(self.llm())
        return ContextualCompressionRetriever(
         base_retriever=self.multiquery_retriever_setup(),
         base_compressor=compressor
        )
        
        
class SearchEngine:
    def __init__(self, collection_name):
        self.tools = RetrieverEngine(collection_name=collection_name)
        self.retriever = self.tools.multiquery_retriever_setup()  # built ONCE

    def search(self, query: str):
        return self.retriever.invoke(query)   # query comes in here, per-call
    
# build once
if __name__ == "__main__" :
    filing_engine = SearchEngine(collection_name="gst")
    results = filing_engine.search("gst")
    print(results)