import psycopg 
from psycopg import Connection

class DatabaseConnectionError(Exception): 
    pass

def get_connection(database_url: str) -> Connection: 
    try:
        return psycopg.connect(
            database_url,
            connect_timeout=5,
        )

    except psycopg.OperationalError as exc:
        raise DatabaseConnectionError(
            "Unable to conntect to PostgreSQL."
        ) from exc