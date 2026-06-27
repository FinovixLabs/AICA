import os 


from dotenv import load_dotenv

load_dotenv()

CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")
DEBUG: bool = os.getenv("FLASK_DEBUG", "debug") == "1"


#-------------------------------------------------------------------------------------
#                      D A T A B A S E   C O N N E C T I O N 
#-------------------------------------------------------------------------------------
SUPABASE_DATABASE_URL=os.environ["SUPABASE_DATABASE_URL"]
#Special API Key : BYPASS RLS SECURITY
SUPABASE_SERVICE_KEY=os.environ.get("SUPABASE_SERVICE_KEY")
#Public endpoint: to connect from frontend 
#purpose: initialize supabase client library
SUPABASE_URL=os.environ.get("SUPABASE_URL")
#Sign & verify JWT tokens: USER AUTHENTICATION
SUPABASE_JWT_SECRET=os.environ["SUPABASE_JWT_SECRET"]


#-------------------------------------------------------------------------------------
#                      A I   A P I   K E Y S
#-------------------------------------------------------------------------------------


#-------------------------------------------------------------------------------------
#                      R A G   C O N F I G
#-------------------------------------------------------------------------------------
RAG_CHUNK_SIZE: int = 500
RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")