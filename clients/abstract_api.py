import json
import os 
import requests
from dotenv import load_dotenv 

load_dotenv()

ABSTRACT_API_KEY = os.getenv("ABSTRACT_API_KEY")
ABSTRACT_COMPANY_URL = "https://companyenrichment.abstractapi.com/v1/"

class AbstractAPIError(Exception):
    pass

def get_company_by_domain(
    domain: str,
    inspect_response: bool = False,
) -> dict : 

    if not ABSTRACT_API_KEY:
        raise AbstractAPIError(
            "ABSTRACT_API_KEY is not configured."
        )

    params = { 
        "api_key": ABSTRACT_API_KEY,
        "domain": domain,
    }

    try: 
        response = requests.get(
            ABSTRACT_COMPANY_URL,
            params=params,
            timeout=10
        )

        #1. Validate HTTP status
        response.raise_for_status()

    except requests.Timeout as exc:
        raise AbstractAPIError(
            f"Abstract API timed out for: {domain}"
        ) from exc
        
    except requests.RequestException as exc: 
        raise AbstractAPIError(
            f"Abstract API request failed for : {domain}"
        ) from exc

    # 2.Validate response as JSON
    try: 
            data = response.json()

    except requests.JSONDecodeError as exc: 
        raise AbstractAPIError(
            "Abstract API returned invalid JSON."
        ) from exc

    # 3. Optional CLI Inspection
    if inspect_response: 
        print("\n---Asbtract API Response ---")
        print(json.dumps(data, indent=2))
        print("------------------------------\n")

    return data