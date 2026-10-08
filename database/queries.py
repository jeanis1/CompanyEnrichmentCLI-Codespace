INSERT_COMPANY = """
INSERT INTO companies (name, domain, industry)
VALUES (%s, %s, %s)
ON CONFLICT (domain)
DO UPDATE SET
    name = EXCLUDED.name,
    industry = EXCLUDED.industry
RETURNING id;
"""

INSERT_ENRICHMENT_RUN = """
INSERT INTO enrichment_runs(result)
VALUES (%s)
RETURNING id;
"""


INSERT_QUALIFICATION_RESULT =  """
INSERT INTO qualification_results(company_id, enrichment_run_id, icp_score)
VALUES(%s, %s, %s)
RETURNING id;
"""


GET_HIGHEST_ICP_SCORE = """
SELECT c.*, q.icp_score
FROM qualification_results AS q 
JOIN companies AS c 
    ON q.company_id = c.id
ORDER BY q.icp_score DESC
LIMIT 5 
"""


GET_INDUSTRY_COUNT = """
SELECT industry, COUNT(*) as total_accounts
FROM companies 
GROUP BY industry
ORDER BY total_accounts DESC;
"""