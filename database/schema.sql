CREATE TABLE IF NOT EXISTS companies ( 
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL, 
    domain TEXT NOT NULL UNIQUE,
    industry TEXT
);


CREATE TABLE IF NOT EXISTS enrichment_runs ( 
    id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    result TEXT -- success / fail
);


CREATE TABLE IF NOT EXISTS qualification_results (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES companies(id) NOT NULL,
    enrichment_run_id BIGINT REFERENCES enrichment_runs(id),
    icp_score INTEGER
);