import psycopg 
from psycopg import Connection

class DatabaseConnectionError(Exception): 
    pass

def get_connection(database_url: str) -> Connection: 
        return psycopg.connect(
            database_url,
            autocommit=True,
            connect_timeout=5,
            options="-c statement_timeout=10000 -c lock_timeout=3000",
        )

 