---
name: database-workflow
description: "Plan and implement the selected project's database schema, migrations, access boundaries and database tests for SQLite, MySQL, PostgreSQL, Supabase or MongoDB."
---

# Database workflow

Read the database choice in the project brief and inspect existing models, migrations and driver
versions before proposing changes. Do not replace an existing database or provision a service
because a skill mentions it. Selecting a database does not create accounts or grant live-data access.

Model the actual read/write paths and invariants first. Choose keys, relations or document boundaries,
uniqueness and indexes from those paths. Keep credentials in the runtime's secret configuration;
never place server credentials in browser code. Use the project's query builder or parameterized
queries, validate input and enforce authorization independently of input validation.

Use only the relevant guidance in [database choices](references/databases.md). Verify version-specific
syntax against the installed engine and its official documentation. Treat numerical tuning values
from other skills as hypotheses to measure, not defaults to copy.

Make schema changes through the project's migration mechanism. Describe existing-data effects,
backfill/rollback limits and a backup strategy where needed. Exercise migrations on disposable data,
including upgrading an existing schema; do not silently reset a real database to make a test pass.

Test the useful behavior: constraints reject invalid data, transactions preserve invariants,
unauthorized users cannot cross ownership boundaries, and important queries use suitable plans.
Report which engine and environment were tested. A mocked repository test does not establish
real database behavior. Record schema decisions and remaining migration work in the project handoff note.
