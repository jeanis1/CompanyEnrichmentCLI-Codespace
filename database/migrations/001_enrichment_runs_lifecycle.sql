BEGIN;

SET LOCAL lock_timeout = '5s';

--Prevent writes during validation & migration
LOCK TABLE companies, enrichment_runs, qualification_results
    IN ACCESS EXCLUSIVE MODE;

--Stop if historical data is ambiguous
DO $$
BEGIN
    IF EXISTS (
        SELECT e.id
        FROM enrichment_runs e
        LEFT JOIN qualification_results q 
            ON q.enrichment_run_id = e.id
        GROUP BY e.id
        HAVING COUNT(q.id) <> 1
            OR COUNT(q.is_qualified) <> 1
    ) THEN
        RAISE EXCEPTION
            'Each existing run must have exactly one non-null qualification result';
        
    END IF;

    IF EXISTS (
        SELECT 1
        FROM enrichment_runs e
        JOIN qualification_results q
            ON q.enrichment_run_id = e.id
        WHERE q.company_id IS DISTINCT FROM e.company_id
    ) THEN
        RAISE EXCEPTION 
            'Qualification and enrichment run company IDs do not match.';
    END IF;
END;
$$;

ALTER TABLE enrichment_runs
    ADD COLUMN requested_domain TEXT,
    ADD COLUMN status TEXT,
    ADD COLUMN error_code TEXT,
    ADD COLUMN finished_at TIMESTAMPTZ;

-- A run must be allowed to exist before a company is available.
ALTER TABLE enrichment_runs
    ALTER COLUMN company_id DROP NOT NULL;

-- Discard unreliable old qualification 
-- Boolean is restored from qualification_results below
ALTER TABLE enrichment_runs
    ALTER COLUMN result TYPE BOOLEAN
    USING NULL::BOOLEAN;

-- Restore correct values.
UPDATE enrichment_runs e 
SET requested_domain = c.domain,
    status = 'succeeded',
    result = q.is_qualified,
    finished_at = CURRENT_TIMESTAMP
FROM companies c, qualification_results q
WHERE c.id = e.company_id
    AND q.enrichment_run_id = e.id;

ALTER TABLE enrichment_runs
    ALTER COLUMN requested_domain SET NOT NULL,
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN status SET DEFAULT 'running',

    ADD CONSTRAINT enrichment_runs_status_check
    CHECK (
        status IN ('running', 'succeeded', 'failed')
    ),

    ADD CONSTRAINT enrichment_runs_lifecycle_check
        CHECK(
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
        );

COMMIT;