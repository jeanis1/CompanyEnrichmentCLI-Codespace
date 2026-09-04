import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigurationError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    abstract_api_key: str
    abstract_api_url: str = "https://companyenrichment.abstractapi.com/v1/"
    request_timeout_seconds: float = 10.0
    max_retries: int = 3
    backoff_seconds: float = 1.0
    output_dir: Path = Path("output")

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        api_key = os.getenv("ABSTRACT_API_KEY")
        if not api_key:
            raise ConfigurationError("ABSTRACT_API_KEY is not configured.")

        return cls(abstract_api_key=api_key)
