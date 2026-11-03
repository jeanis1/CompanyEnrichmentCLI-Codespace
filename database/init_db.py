from pathlib import Path

def create_tables(conn) -> None:
    schema = Path("database/schema.sql").read_text()

    with conn.cursor() as cursor:
        cursor.execute(schema)

    conn.commit()
    
if __name__ == "__main__":
    from config import Settings
    from database.database import get_connection

    with get_connection(Settings.from_env().database_url) as conn:
        create_tables(conn)
    print("Tables created.")