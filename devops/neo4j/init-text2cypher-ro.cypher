// Read-only user for text2cypher (Task 07 guardrail #1).
// Applied idempotently via: make graph-init-ro
// Password is taken from NEO4J_RO_PASSWORD in .env (not this file).
// GRANT ROLE reader — Enterprise only; Community: separate user + app guardrails.

CREATE USER text2cypher_ro IF NOT EXISTS
  SET PASSWORD 'change-me' CHANGE NOT REQUIRED;
// Enterprise: GRANT ROLE reader TO text2cypher_ro;
