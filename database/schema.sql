CREATE TABLE IF NOT EXISTS companies ( 
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL, 
    domain TEXT NOT NULL UNIQUE,
    industry TEXT
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
    company_id BIGINT REFERENCES companies(id) NOT NULL,
    enrichment_run_id BIGINT REFERENCES enrichment_runs(id),
    icp_score INTEGER,
    is_qualified BOOLEAN
);