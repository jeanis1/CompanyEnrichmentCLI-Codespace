import os 
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    abstract_api_key:str
    output_dir: Path = Path("output")

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        api_key = os.getenv("ABSTRACT_API_KEY")

        if not api_key:
            raise ValueError(
            "ABSTRACT_API_KEY is not configured."
            )

        return cls(
            abstract_api_key=api_key,
        )

        