CREATE TABLE IF NOT EXISTS companies ( 
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL, 
    domain TEXT NOT NULL UNIQUE,
    industry TEXT,
    CONSTRAINT companies_domain_canonical
        CHECK (domain <> '' AND domain = LOWER(BTRIM(domain)))
);


CREATE TABLE IF NOT EXISTS enrichment_runs ( 
    id BIGSERIAL PRIMARY KEY,

    requested_domain TEXT NOT NULL,
    company_id BIGINT REFERENCES companies(id),
    
    status TEXT NOT NULL DEFAULT 'running',

    --Qualification outcome; NULL when not determined.
    result BOOLEAN,
    error_code TEXT,
    
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,

    CONSTRAINT enrichment_runs_status_check
    CHECK (
        STATUS IN ('running', 'succeeded', 'failed')
    ),

    CONSTRAINT enrichment_runs_lifecycle_check
    CHECK ( 
        (
            status = 'running'
            AND result IS NULL
            AND error_code IS NULL
            AND finished_at IS NULL
        )
        OR
        (
            status = 'succeeded'
            AND company_id IS NOT NULL
            AND result IS NOT NULL
            AND error_code IS NULL
            AND finished_at IS NOT NULL
        )
        OR
        (
            status = 'failed'
            AND result IS NULL
            AND error_code IS NOT NULL
            AND finished_at IS NOT NULL
        )
    )
);


CREATE TABLE IF NOT EXISTS qualification_results (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(id),
    enrichment_run_id BIGINT NOT NULL REFERENCES enrichment_runs(id),
    icp_score INTEGER NOT NULL CHECK(icp_score BETWEEN 0 AND 100),
    is_qualified BOOLEAN NOT NULL
);

--Overlapping invocation cannot enrich same domain at same time.
CREATE UNIQUE INDEX IF NOT EXISTS enrichment_runs_one_running_per_domain
    ON enrichment_runs (requested_domain) WHERE status = 'running';


CREATE INDEX IF NOT EXISTS enrichment_runs_company_id_idx ON enrichment_runs(company_id);
CREATE INDEX IF NOT EXISTS enrichment_runs_status_started_idx ON enrichment_runs (status, started_at);
CREATE INDEX IF NOT EXISTS qualification_results_company_id_idx ON qualification_results(company_id);