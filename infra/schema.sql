-- Predictive Maintenance Platform — PostgreSQL schema

CREATE TABLE IF NOT EXISTS features (
    id               SERIAL PRIMARY KEY,
    udi              INTEGER       NOT NULL,
    product_id       VARCHAR(10)   NOT NULL,
    product_type     CHAR(1)       NOT NULL CHECK (product_type IN ('L', 'M', 'H')),
    air_temp         FLOAT         NOT NULL,
    process_temp     FLOAT         NOT NULL,
    rotational_speed INTEGER       NOT NULL,
    torque           FLOAT         NOT NULL,
    tool_wear        INTEGER       NOT NULL,
    machine_failure  BOOLEAN       NOT NULL,
    -- engineered features (computed by ml/features.py)
    temp_diff        FLOAT         NOT NULL,
    mechanical_power FLOAT         NOT NULL,
    wear_rate        FLOAT         NOT NULL,
    overstrain_flag  BOOLEAN       NOT NULL,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS predictions (
    id               SERIAL        PRIMARY KEY,
    timestamp        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    air_temp         FLOAT         NOT NULL,
    process_temp     FLOAT         NOT NULL,
    rotational_speed INTEGER       NOT NULL,
    torque           FLOAT         NOT NULL,
    tool_wear        INTEGER       NOT NULL,
    product_type     CHAR(1),
    failure_prob     FLOAT         NOT NULL CHECK (failure_prob BETWEEN 0 AND 1),
    predicted_failure BOOLEAN      NOT NULL,
    failure_modes    JSONB         NOT NULL DEFAULT '{}',
    model_version    VARCHAR(100)  NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_failure   ON predictions (predicted_failure);
CREATE INDEX IF NOT EXISTS idx_features_product_id  ON features    (product_id);
