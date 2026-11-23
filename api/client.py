import requests

rows = [
    {
        "row_number": 11,
        "name": "Lam Research",
        "domain": "lamresearch.com",
        "industry": "Semiconductor Manufacturing Equipment",
        "employee_count": 19700,
        "annual_revenue": 20600000000,
        "year_founded": 1980,
        "city": "Fremont",
        "state": "California",
        "country": "United States",
        "company_type": "Public Company",
        "description": "",
        "linkedin_url": "",
        "enrichment_source": "https://www.lamresearch.com/company/company-overview/",
        "icp_score": "",
        "employee_score": "",
        "industry_score": "",
        "geography_score": "",
        "revenue_score": "",
        "is_qualified": "",
    }
]

resp = requests.post("http://localhost:8001/companies", json=rows)
resp.raise_for_status()
companies = resp.json()  # TODO - Change to ICP Score & Qualification
print(companies["11"]["name"])  # test output "Lam Research"
