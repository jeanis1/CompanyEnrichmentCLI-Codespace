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
INSERT INTO enrichment_runs(company_id, result)
VALUES (%s,%s)
RETURNING id;
"""


INSERT_QUALIFICATION_RESULT =  """
INSERT INTO qualification_results(company_id, enrichment_run_id, icp_score, is_qualified)
VALUES(%s, %s, %s, %s)
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


GET_ALL_INDUSTRY_COUNT = """
SELECT industry, COUNT(*) as total_accounts
FROM companies 
GROUP BY industry
ORDER BY total_accounts DESC;
"""


GET_THIS_INDUSTRY = """
SELECT c.name, c.domain, q.icp_score
FROM companies c 
JOIN qualification_results q 
    ON c.id = q.company_id
WHERE c.industry = %s
ORDER BY q.icp_score DESC;
"""

GET_FAILED = """
SELECT c.name, c.domain
FROM companies c
JOIN enrichment_runs e
    ON c.id = e.company_id
WHERE e.result = 'fail'
"""

#Unecessary due to input filtering, but included as required learning practice.
GET_DUPLICATE = """
SELECT LOWER(TRIM(domain)), COUNT(*) AS cnt
FROM companies
GROUP BY LOWER(TRIM(domain))
HAVING COUNT(*) > 1
ORDER BY cnt DESC;
"""

GET_TOTAL_QUALIFICATION_RATE = """
SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE is_qualified) / COUNT(*), 2) AS pct_true
FROM qualification_results;
"""

GET_BATCH_QUALIFICATION_RATE = """
SELECT q.is_qualified 
FROM companies c
JOIN qualification_results q 
    on c.id = q.company_id
WHERE c.domain = ANY(%s)
"""

GET_PROCESSED_THIS_WEEK = """
SELECT c.domain
FROM companies c 
JOIN enrichment_runs e 
    on c.id = e.company_id
WHERE e.started_at >= NOW() - INTERVAL '7 days'
"""






