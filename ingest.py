from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader,
    DirectoryLoader,
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
)

#  CHUNKING  MODULE 
from langchain_text_splitters import RecursiveCharacterTextSplitter

# EMBEDDER MODULE
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
load_dotenv()
DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL")


#---------------------------------------------------------------------------
#                     D O C U M E N T    L O A D E R 
#---------------------------------------------------------------------------

class DocumentLoadingService :
    """
    Reusable document loader for AICA RAG ingestion.
    Supports:
    - Single .txt file
    - Single .pdf file
    - Single .docx file
    - Single .csv file
    - Folder containing multiple supported files
    """
    
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding
        self.supported_extensions = {".txt", ".pdf", ".docx", ".csv"}

    def load(self, path: str) -> List[Document]:
        path_obj = Path(path)
        
        if not path_obj.exists():   
            raise FileNotFoundError(f"Path not found: {path_obj}")
        if path_obj.is_file():
            return self._load_file(path_obj)
        if path_obj.is_dir():
            return self._load_directory(path_obj)
        raise ValueError(f"Invalid path: {path_obj}")
    
    def _load_file(self,file_path:Path) -> List[Document]:
        suffix=file_path.suffix.lower()
        
        if suffix==".txt":
            loader=TextLoader(str(file_path),encoding=self.encoding)
        elif suffix==".pdf":
            loader=PyPDFLoader(str(file_path))
        elif suffix==".docx":
            loader=Docx2txtLoader(str(file_path))
        elif suffix == ".csv" :
            loader=CSVLoader(str(file_path),encoding=self.encoding)
        else :
            raise ValueError(f"Unsupported file type: {suffix}")
        
        return loader.load()
    
    def _load_directory(self, directory_path: Path) -> List[Document]:
        all_documents: List[Document] = []

        for file_path in directory_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                documents = self._load_file(file_path)
                all_documents.extend(documents)

        return all_documents
#-------------------------------------------------------------------------
#                            C H U N K E R 
#-------------------------------------------------------------------------
#SPLIT DOCUMENTS INTO REDABLE CHUNKS
class document_splitter :
    def __init__ (self):
        self.splitter= RecursiveCharacterTextSplitter(
            chunk_size=2500,
            chunk_overlap=300,
            separators=["---" , "\n\n" , "\n" , "."]
        )
    
    def split (self,documents):
        return self.splitter.split_documents(documents)
#-------------------------------------------------------------------------
#                         E M B E D D E R 
#-------------------------------------------------------------------------
class EmbeddingService:
    def __init__(self, collection_name):
        if not DATABASE_URL:
            raise ValueError("SUPABASE_DATABASE_URL missing from .env")

        self.collection_name = collection_name

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )

        self.vectorstore = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            connection=DATABASE_URL,
            use_jsonb=True
        )

    def upload_chunks(self, chunks):
        self.vectorstore.add_documents(chunks)
        return f"Uploaded {len(chunks)} documents"

    def get_vectorstore(self):
        return self.vectorstore

#--------------------------------------------------------------------------
#                        I N G E S T O R 
#--------------------------------------------------------------------------
def ingest_documents(path:str,collection_name:str):
    documents=DocumentLoadingService().load(path)
    chunks=document_splitter().split(documents)
    return EmbeddingService(collection_name).upload_chunks(chunks)

