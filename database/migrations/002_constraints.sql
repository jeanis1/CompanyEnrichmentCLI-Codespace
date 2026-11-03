--Update existing DB (001 must be applied) to same state as schema.sql
BEGIN;

SET LOCAL lock_timeout = '5s';

--Prevent write during validation & migration
LOCK TABLE companies, enrichment_runs, qualification_results
    IN ACCESS EXCLUSIVE MODE;

DO $$
BEGIN 
    IF NOT EXISTS(
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'enrichment_runs' AND column_name = 'status'
    ) THEN
        RAISE EXCEPTION 'enrichment_runs.status is missing: apply 001 first.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM qualification_results 
        WHERE enrichment_run_id IS NULL OR icp_score IS NULL OR is_qualified IS NULL
    ) THEN
        RAISE EXCEPTION 'qualification_results has rows with NULL enrichment_run_id, icp_score or is_qualified.';
    END IF;

    IF EXISTS(
        SELECT 1 FROM qualification_results 
        GROUP BY enrichment_run_id
        HAVING COUNT(*) > 1 
    ) THEN
        RAISE EXCEPTION 'qualification_results has more than one row for the same enrichment_run_id.';
    END IF;

    IF EXISTS(
        SELECT 1 FROM qualification_results
        WHERE icp_score NOT BETWEEN 0 AND 100
    ) THEN
        RAISE EXCEPTION 'qualification_results has icp_score values outside 0-100.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM companies
        WHERE domain = '' OR domain <> LOWER(BTRIM(domain))
    ) THEN
        RAISE EXCEPTION 'companies has empty or non-canonical domains (uppercase or surrounding spaces).';
    END IF;
END;
$$;

--Fail stale running rows. Then one-running-per-domain index can be created
UPDATE enrichment_runs
SET status = 'failed', error_code = 'interrupted', finished_at = NOW()
WHERE status = 'running'
    AND started_at < NOW() - make_interval(mins => 15);

DO $$
BEGIN
    IF EXISTS(
        SELECT 1 FROM enrichment_runs
        WHERE status = 'running'
        GROUP BY requested_domain
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'More than one recent running run for the same domain. Wait 15 minutes and re-run.';
    END IF;
END;
$$;

-- A run is created before its company exists (no-op is already nullable)
ALTER TABLE enrichment_runs
    ALTER COLUMN company_id DROP NOT NULL;

ALTER TABLE qualification_results
    ALTER COLUMN enrichment_run_id SET NOT NULL,
    ALTER COLUMN icp_score SET NOT NULL,
    ALTER COLUMN is_qualified SET NOT NULL;


DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'companies_domain_canonical') THEN
        ALTER TABLE companies ADD CONSTRAINT companies_domain_canonical
            CHECK (domain <> '' AND domain = LOWER(BTRIM(domain)));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'qualification_results_enrichment_run_id_key') THEN
        ALTER TABLE qualification_results ADD CONSTRAINT qualification_results_enrichment_run_id_key
            UNIQUE (enrichment_run_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'qualification_results_icp_score_check') THEN
        ALTER TABLE qualification_results ADD CONSTRAINT qualification_results_icp_score_check
            CHECK (icp_score BETWEEN 0 and 100);
    END IF;
END;
$$;

CREATE UNIQUE INDEX IF NOT EXISTS enrichment_runs_one_running_per_domain
    ON enrichment_runs (requested_domain) WHERE status = 'running';

CREATE INDEX IF NOT EXISTS enrichment_runs_company_id_idx ON enrichment_runs(company_id);
CREATE INDEX IF NOT EXISTS enrichment_runs_status_started_idx ON enrichment_runs(status, started_at);
CREATE INDEX IF NOT EXISTS qualification_results_company_id_idx ON qualification_results(company_id);

COMMIT;


    

