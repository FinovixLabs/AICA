# test works
# testing
from psycopg2.pool import SimpleConnectionPool
from config import SUPABASE_DATABASE_URL

_pool = SimpleConnectionPool(
    minconn=1, maxconn=10,
    dsn=SUPABASE_DATABASE_URL,
)
