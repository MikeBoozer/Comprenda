-- =============================================================================
-- Project Nuance — Drift Alerts (Cortex Alerts + Snowflake Tasks)
-- =============================================================================
-- Schedules an hourly recomputation of CDS for tracked entities and fires an
-- alert (via Snowflake Notification Integration) when CDS rises above the
-- subscriber-defined threshold.
--
-- NOTE: Snowflake Scripting requires DECLARE CURSOR for row iteration; we
-- use `EXECUTE IMMEDIATE` + `SQLROWCOUNT` for INSERT row counts.
-- =============================================================================

USE DATABASE nuance_db;
USE WAREHOUSE nuance_dev_wh;

-- ---------------------------------------------------------------------------
-- 1. Email notification integration (account-level).
--    IMPORTANT: replace ALLOWED_RECIPIENTS with the actual owner emails you
--    use in library.tracked_entities (they must be Snowflake account users
--    OR explicitly allow-listed here).
-- ---------------------------------------------------------------------------
CREATE NOTIFICATION INTEGRATION IF NOT EXISTS nuance_alert_email
    TYPE = EMAIL
    ENABLED = TRUE;
    -- Optional: lock down to a fixed allow list with
    -- ALLOWED_RECIPIENTS = ('owner1@example.com','owner2@example.com')
    -- If omitted, only verified account users can receive email.

-- ---------------------------------------------------------------------------
-- 2. Drift events table — one row per detected drift incident.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS internal.drift_events (
    drift_id        VARCHAR DEFAULT UUID_STRING() PRIMARY KEY,
    entity_id       VARCHAR,
    entity_name     VARCHAR,
    event_tag       VARCHAR,
    language_a      VARCHAR,
    language_b      VARCHAR,
    prev_cds        FLOAT,
    new_cds         FLOAT,
    delta_cds       FLOAT,
    detected_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    notified        BOOLEAN DEFAULT FALSE
);

-- ---------------------------------------------------------------------------
-- 3. Schema fix: tracked_entities needs an event_tag_pattern column so the
--    drift check can match entity to event_tag. The entity_name is human-
--    readable ("iPhone 17"); the event_tag is the analytics key
--    ("iPhone_17_launch"). They must be joinable.
-- ---------------------------------------------------------------------------
ALTER TABLE library.tracked_entities
    ADD COLUMN IF NOT EXISTS event_tag_pattern VARCHAR;

-- Default the pattern to the entity_name (users can edit later).
UPDATE library.tracked_entities
SET event_tag_pattern = entity_name
WHERE event_tag_pattern IS NULL;

-- ---------------------------------------------------------------------------
-- 4. Drift check procedure.
--    Uses EXECUTE IMMEDIATE to capture SQLROWCOUNT.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE internal.check_drift()
RETURNS STRING
LANGUAGE SQL
AS
DECLARE
    inserted_count INTEGER DEFAULT 0;
    insert_sql STRING;
BEGIN
    insert_sql := $$
        INSERT INTO internal.drift_events (
            entity_id, entity_name, event_tag,
            language_a, language_b, prev_cds, new_cds, delta_cds
        )
        WITH latest AS (
            SELECT cds.*,
                   ROW_NUMBER() OVER (
                       PARTITION BY event_tag, language_a, language_b
                       ORDER BY computed_at DESC) AS rn
            FROM outputs.cultural_divergence_scores cds
        ),
        prior AS (
            SELECT cds.event_tag, cds.language_a, cds.language_b,
                   cds.cds_score AS prior_cds,
                   ROW_NUMBER() OVER (
                       PARTITION BY event_tag, language_a, language_b
                       ORDER BY computed_at DESC) AS rn
            FROM outputs.cultural_divergence_scores cds
            WHERE cds.computed_at < DATEADD('hour', -23, CURRENT_TIMESTAMP())
        )
        SELECT
            te.entity_id, te.entity_name, l.event_tag,
            l.language_a, l.language_b,
            COALESCE(p.prior_cds, 0),
            l.cds_score,
            l.cds_score - COALESCE(p.prior_cds, 0)
        FROM library.tracked_entities te
        JOIN latest l
            ON l.rn = 1
           AND (
                -- Match by exact event_tag or by LIKE pattern
                l.event_tag = te.event_tag_pattern
                OR l.event_tag ILIKE REPLACE(te.event_tag_pattern, ' ', '_') || '%'
                OR REPLACE(te.event_tag_pattern, ' ', '_') ILIKE l.event_tag || '%'
           )
        LEFT JOIN prior p
            ON p.event_tag = l.event_tag
           AND p.language_a = l.language_a
           AND p.language_b = l.language_b
           AND p.rn = 1
        WHERE te.active = TRUE
          AND (
              l.cds_score >= te.cds_threshold_abs
              OR (l.cds_score - COALESCE(p.prior_cds, 0)) >= te.cds_threshold_delta
          )
          AND NOT EXISTS (
              SELECT 1 FROM internal.drift_events de
              WHERE de.entity_id = te.entity_id
                AND de.language_a = l.language_a
                AND de.language_b = l.language_b
                AND de.detected_at > DATEADD('hour', -6, CURRENT_TIMESTAMP())
          )
    $$;

    EXECUTE IMMEDIATE :insert_sql;
    inserted_count := SQLROWCOUNT;

    RETURN 'Drift events inserted: ' || inserted_count::STRING;
END;

-- ---------------------------------------------------------------------------
-- 5. Notify procedure — uses a CURSOR (not RESULTSET) for iteration.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE internal.notify_drift()
RETURNS STRING
LANGUAGE SQL
AS
DECLARE
    sent_count INTEGER DEFAULT 0;
    c CURSOR FOR
        SELECT de.drift_id, de.entity_name,
               de.language_a, de.language_b,
               de.prev_cds, de.new_cds,
               te.owner_email
        FROM internal.drift_events de
        JOIN library.tracked_entities te ON de.entity_id = te.entity_id
        WHERE de.notified = FALSE;
    v_drift_id  VARCHAR;
    v_name      VARCHAR;
    v_lang_a    VARCHAR;
    v_lang_b    VARCHAR;
    v_prev      FLOAT;
    v_new       FLOAT;
    v_email     VARCHAR;
BEGIN
    OPEN c;
    FOR rec IN c DO
        v_drift_id := rec.drift_id;
        v_name     := rec.entity_name;
        v_lang_a   := rec.language_a;
        v_lang_b   := rec.language_b;
        v_prev     := rec.prev_cds;
        v_new      := rec.new_cds;
        v_email    := rec.owner_email;

        CALL SYSTEM$SEND_EMAIL(
            'nuance_alert_email',
            v_email,
            'Nuance drift alert: ' || v_name,
            'Cultural Divergence Score between ' || v_lang_a ||
            ' and ' || v_lang_b || ' for "' || v_name ||
            '" rose from ' || v_prev::STRING ||
            ' to ' || v_new::STRING || '. ' ||
            'Investigate at https://app.snowflake.com (Nuance Drift Alerts page).'
        );

        UPDATE internal.drift_events
        SET notified = TRUE
        WHERE drift_id = v_drift_id;

        sent_count := sent_count + 1;
    END FOR rec;
    CLOSE c;

    RETURN 'Notifications sent: ' || sent_count::STRING;
END;

-- ---------------------------------------------------------------------------
-- 6. Wrapper procedure called by the Task (Task bodies must be a single
--    statement, so we wrap the two procs in one).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE internal.run_drift_cycle()
RETURNS STRING
LANGUAGE SQL
AS
BEGIN
    CALL internal.check_drift();
    CALL internal.notify_drift();
    RETURN 'Cycle complete';
END;

-- ---------------------------------------------------------------------------
-- 7. Hourly Task.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TASK internal.drift_check_task
    WAREHOUSE = nuance_dev_wh
    SCHEDULE = 'USING CRON 0 * * * * UTC'
    COMMENT = 'Hourly Nuance drift check + email dispatch'
AS
    CALL internal.run_drift_cycle();

-- The task is created suspended. Resume it once you're ready:
--    ALTER TASK internal.drift_check_task RESUME;

-- ---------------------------------------------------------------------------
-- 8. Manual test:
--    INSERT INTO library.tracked_entities (entity_name, event_tag_pattern, owner_email, languages)
--    VALUES ('iPhone 17', 'iPhone_17_launch', 'you@example.com',
--            ARRAY_CONSTRUCT('en','ja','zh'));
--    CALL internal.run_drift_cycle();
--    SELECT * FROM internal.drift_events ORDER BY detected_at DESC;
-- ---------------------------------------------------------------------------
