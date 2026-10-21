
# Django Zappa uv Constitution

## Core Principles

### I. Serverless-First & Zero Fixed Infrastructure (NON-NEGOTIABLE)
All components, database adapters, and static file handlers MUST execute within ephemeral, stateless compute environments (AWS Lambda). Local file storage must never be assumed persistent across function invocations; all persistent state MUST synchronize to durable cloud object storage (Amazon S3) or managed services upon request completion. The template architecture MUST scale to zero when inactive, avoiding compulsory fixed monthly database costs.

### II. Modern Dependency & Tooling Standard with uv
Dependency resolution, virtual environment provisioning, and lockfile management MUST strictly be driven by `uv`. Project specifications in `pyproject.toml` MUST adhere to PEP 517/621 standards using modern `[dependency-groups]` for development tooling. Every deployable environment MUST be reproducible via a committed `uv.lock`.

### III. Graviton & ARM64 Architecture Alignment
Deployment configurations, container build definitions, and Lambda profiles MUST explicitly target the AWS Graviton (`arm64`) architecture. Build pipelines and Docker packaging helpers MUST compile Linux ARM64 binary wheels so that compiled C-extensions function identically on AWS Lambda regardless of whether developer host machines run Windows, macOS, or Linux.

### IV. Dual-Mode Database Resilience (django-s3-sqlite with Local Fallback)
The project MUST default to S3-backed SQLite (`django-s3-sqlite`) for zero-cost cloud deployments, while maintaining seamless, zero-credential local SQLite operation for offline local development and test execution via `USE_S3_SQLITE=False`. Database handlers MUST adhere to S3 persistence lifecycles (fetching from S3 to `/tmp` at connection start, verifying hash, and uploading modified databases on close).

### V. Test-First & Automated Verification Gates
Every new view, endpoint, and data model MUST have accompanying automated unit and integration tests executed with `pytest` and `pytest-django`. Code formatting and linting MUST pass `ruff check .` with zero unaddressed warnings. No deployment to AWS Lambda stage (`dev` or `prod`) may occur without passing automated test and lint suites in CI/CD.

### VI. Zero-Trust Credential & Secret Protection (NON-NEGOTIABLE)
Sensitive credentials, API keys, database connection strings, and authorization secrets MUST NEVER be hardcoded into codebases, committed to version control, or cached within `.agents/`, `.specify/`, or other repository directories. Agent configurations and local tooling workspaces MUST remain strictly stateless regarding authentication tokens and credentials; secret values MUST only be read at runtime from uncommitted environment variables (`.env`, which MUST remain gitignored) or retrieved dynamically from secure external secret managers (e.g., AWS Systems Manager Parameter Store or AWS Secrets Manager). AI agents, scripts, and automation tools MUST enforce zero-secret persistence and actively prevent caching credentials in local metadata or configuration stores.

## Technology & Operational Constraints

- **Runtime & Language**: Python 3.13 (CPython 3.13) targeting AWS Lambda ARM64 (Graviton2).
- **Web Framework**: Django 6.x configured for WSGI deployment through Zappa (`core.wsgi.application`).
- **Serverless Integration**: AWS Lambda behind Amazon API Gateway with `SECURE_PROXY_SSL_HEADER` HTTPS forwarding.
- **Storage & State**: Amazon S3 for SQLite synchronization (`django-s3-sqlite`) and optional static asset storage (`django-storages`). Local writable disk operations are strictly confined to `/tmp/`.
- **Security & Secret Management**: Strict zero-secret-persistence policy across repository artifacts. Secrets MUST be loaded via environment variables or AWS Systems Manager Parameter Store / AWS Secrets Manager in deployed environments. No secrets or authentication tokens may ever be stored or cached within `.agents/` or source-controlled directories.
- **Cross-Platform Compatibility**: Native support for Windows PowerShell and POSIX shells, backed by Docker container build recipes (`--platform linux/arm64`) to eliminate OS-specific wheel incompatibilities.

## Development & Quality Workflow

- **Local Execution**: All local management commands and development servers run via `uv run` (e.g. `uv run python manage.py runserver`, `uv run pytest`).
- **Quality Gates**: `uv run ruff check .` and `uv run pytest` MUST pass before code is merged or deployed.
- **Database Migrations**: Migrations MUST be created locally and committed to source control before executing remote migrations on Lambda (`uv run zappa manage <stage> migrate`).
- **Deployment Lifecycle**: Initial deployments use `zappa deploy <stage>`; subsequent updates use `zappa update <stage>`. Staging (`dev`) validation MUST precede production (`prod`) rollout.

## Governance

This Constitution serves as the definitive architectural and engineering standard for the `django-zappa-uv` template and derived applications. All code changes, pull requests, and feature implementations MUST demonstrate compliance with these core principles.

Amendments to this constitution require documentation of rationale, approval, and version updates following Semantic Versioning:
- **MAJOR**: Fundamental changes or revocations of core serverless or architectural principles.
- **MINOR**: Addition of new principles, runtime targets, or major architectural layers.
- **PATCH**: Clarifications, non-semantic wording updates, and typographical corrections.

**Version**: 1.1.0 | **Ratified**: 2026-09-30 | **Last Amended**: 2026-10-01
