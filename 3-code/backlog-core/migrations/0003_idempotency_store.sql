-- idempotency store for service-to-service calls
-- per DEC-idempotency-keys

CREATE TABLE idempotency_keys (
    key UUID PRIMARY KEY,
    response_payload JSONB NOT NULL,
    response_status INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for automatic cleanup (retention)
CREATE INDEX idempotency_keys_created_at_idx ON idempotency_keys (created_at);
