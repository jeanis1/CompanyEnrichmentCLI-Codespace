import os 
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    abstract_api_key:str
    apollo_api_key:str
    db_host:str
    db_port:str
    db_name:str
    db_user:str
    db_password:str
    database_url:str


    output_dir: Path = Path("data/output")

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        abstract_api_key = os.getenv("ABSTRACT_API_KEY")
        apollo_api_key = os.getenv("APOLLO_API_KEY")

        if not abstract_api_key:
            raise ValueError(
            "ABSTRACT_API_KEY is not configured."
            )

        if not apollo_api_key: 
            raise ValueError(
                "APOLLO_API_KEY is not configured."
            )

        return cls(
            abstract_api_key=abstract_api_key,
            apollo_api_key=apollo_api_key,
            output_dir=Path("data/output"),
            db_host=os.getenv("DB_HOST"),
            db_port=os.getenv("DB_PORT"),
            db_name=os.getenv("DB_NAME"),
            db_user=os.getenv("DB_USER"),
            db_password=os.getenv("DB_PASSWORD"),
            database_url=os.getenv("DATABASE_URL")
        )

        