from pathlib import Path

def create_tables(conn) -> None:
    schema = Path("database/schema.sql").read_text()

    with conn.cursor() as cursor:
        cursor.execute(schema)

    conn.commit()