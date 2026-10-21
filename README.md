# Django + Zappa + uv Template

A production-ready template for deploying **Django** to **AWS Lambda** and **Amazon API Gateway** using the **Zappa** framework, **uv** for high-performance dependency management, and **`django-s3-sqlite`** as the default database backend for zero-fixed-cost serverless data persistence.

---

## Architecture Overview

```
                      +-----------------------------+
                      |         Web Client          |
                      +--------------+--------------+
                                     |  HTTPS
                                     v
                      +-----------------------------+
                      |     Amazon API Gateway      |
                      +--------------+--------------+
                                     |  WSGI Event
                                     v
                      +-----------------------------+
                      |      AWS Lambda (Zappa)     |
                      |   Python 3.13 (ARM64/Grav)  |
                      |          Django 6.x         |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               v                                           v
+-----------------------------+             +-----------------------------+
|    Amazon S3 (SQLite DB)    |             |  Amazon S3 (Static/Media)   |
|   `django-s3-sqlite` sync   |             |     `django-storages`       |
+-----------------------------+             +-----------------------------+
```

### Highlights

- **uv Powered:** Blazing-fast dependency resolution, locking, and virtual environment management via [`uv`](https://docs.astral.sh/uv/).
- **Zero-Fixed-Cost Database:** Defaults to `django-s3-sqlite`, synchronizing a single SQLite database file directly with an AWS S3 bucket. Eliminates $15–$30/month RDS minimum costs.
- **Serverless Scaling:** Deploys via Zappa to AWS Lambda, automatically scaling to zero when inactive and scaling up on demand.
- **Built-in Diagnostics & Demo:** Includes an interactive dashboard showing runtime environment variables, database backend status, and sample CRUD persistence tests.
- **Cross-Platform & Windows Ready:** Includes Docker-based packaging scripts (`scripts/zappa-docker.ps1`, `docker-compose.yml`) to guarantee 100% Linux binary wheel compatibility when deploying from Windows or macOS.
- **Automated CI/CD:** Ready-to-use GitHub Actions workflow (`.github/workflows/deploy.yml`) for automated testing and zero-downtime deployments.

---

## Project Structure

```
django-zappa-uv/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD deployment workflow
├── core/                       # Django project package
│   ├── __init__.py
│   ├── asgi.py                 # ASGI entry point
│   ├── settings.py             # Project settings (django-s3-sqlite, S3 static, etc.)
│   ├── urls.py                 # Root URL configuration + /health/ endpoint
│   └── wsgi.py                 # WSGI entry point for Zappa (core.wsgi.application)
├── demo/                       # Sample application demonstrating persistence
│   ├── admin.py
│   ├── apps.py
│   ├── models.py               # Item model for persistence tests
│   ├── templates/demo/
│   │   └── index.html          # Responsive dashboard & CRUD UI
│   ├── urls.py
│   └── views.py
├── scripts/                    # Deployment helpers
│   ├── deploy.ps1              # Local PowerShell deployment script
│   ├── deploy.sh               # Local Bash deployment script
│   ├── zappa-docker.ps1        # Windows Docker-based deployment runner
│   └── zappa-docker.sh         # Unix Docker-based deployment runner
├── tests/                      # Automated test suite
│   ├── conftest.py
│   ├── test_settings.py
│   └── test_views.py
├── .env.example                # Example environment configuration
├── .gitignore
├── .python-version             # Python version pin (3.13)
├── Dockerfile                  # Container build for Linux ARM64 packaging
├── docker-compose.yml          # Docker Compose helper (ARM64 platform)
├── manage.py                   # Django CLI
├── pyproject.toml              # Dependencies & project metadata for uv
├── README.md                   # This documentation
└── zappa_settings.json         # Zappa deployment stages (ARM64 & Python 3.13)
```

---

## Quickstart (Local Development)

### 1. Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/) installed:
  - **Windows (PowerShell):** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - **macOS / Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 2. Setup Environment

Clone the repository and install all dependencies:

```bash
# Clone the repository
git clone <your-repo-url>
cd django-zappa-uv

# Install dependencies and create .venv with uv
uv sync
```

### 3. Configure Local Environment

Copy `.env.example` to `.env`:

```bash
# On Linux/macOS
cp .env.example .env

# On Windows (PowerShell)
Copy-Item .env.example .env
```

> **Tip for Offline Local Development:**
> If you do not have AWS credentials configured locally, set `USE_S3_SQLITE=False` in your `.env` file to use a local `db.sqlite3` file on disk. When you are ready to test S3 sync or deploy to AWS, set `USE_S3_SQLITE=True` and configure `SQLITE_S3_BUCKET`.

### 4. Run Migrations & Start Server

```bash
# Apply migrations
uv run python manage.py migrate

# Create superuser (optional)
uv run python manage.py createsuperuser

# Start Django development server
uv run python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## How S3-backed SQLite Works (`django-s3-sqlite`)

`django-s3-sqlite` enables zero-fixed-cost database persistence for serverless applications:

1. **Invocation Startup:** When Django boots or connects to the database, `django-s3-sqlite` checks the ETag/MD5 of `/tmp/db.sqlite3`. If the S3 copy is newer, it downloads the database file from your S3 bucket into `/tmp/`.
2. **Execution:** Django reads and writes to `/tmp/db.sqlite3` with native SQLite speed.
3. **Connection Close:** When the database connection closes at the end of the request, `django-s3-sqlite` computes the MD5 hash of `/tmp/db.sqlite3`. If modified, it uploads the file back to your S3 bucket.

### Best Uses & Concurrency Caveats

- **Ideal For:** Personal projects, blogs, portfolio sites, internal dashboards, prototypes, and low-concurrency workloads where an Amazon RDS instance ($15–$30/month minimum) is unnecessary.
- **Concurrency Limitation:** Because SQLite is a single file synced on request completion, simultaneous concurrent write requests to different Lambda containers can result in the last writer winning.
- **Scaling to RDS:** If your application grows into a high-concurrency multi-user service, you can seamlessly transition to Amazon RDS (PostgreSQL/MySQL) by updating the `DATABASES` setting in `core/settings.py` without rewriting application logic.

---

## Deploying to AWS Lambda via Zappa

### Step 1: Create AWS S3 Buckets

You need two S3 buckets (or one bucket with different prefixes):
1. **Zappa Deployment Bucket:** Stores Lambda deployment zip packages (e.g. `mycompany-zappa-deployments`).
2. **SQLite Database Bucket:** Stores the synced `db.sqlite3` file (e.g. `mycompany-django-sqlite-db`).

You can create them via AWS CLI:

```bash
aws s3 mb s3://mycompany-zappa-deployments --region us-east-1
aws s3 mb s3://mycompany-django-sqlite-db --region us-east-1
```

> **Bucket Security Note:**
> Make sure both S3 buckets have **Block Public Access** enabled and encryption turned on (SSE-S3).

### Step 2: Configure `zappa_settings.json`

Open `zappa_settings.json` and replace the bucket placeholders:

```json
{
    "dev": {
        "app_function": "core.wsgi.application",
        "aws_region": "us-east-1",
        "project_name": "django-zappa-uv",
        "runtime": "python3.13",
        "architecture": "arm64",
        "s3_bucket": "mycompany-zappa-deployments",
        "keep_warm": true,
        "memory_size": 512,
        "timeout_seconds": 30,
        "use_precompiled_packages": true,
        "environment_variables": {
            "DJANGO_SETTINGS_MODULE": "core.settings",
            "DEBUG": "False",
            "ALLOWED_HOSTS": "*",
            "USE_S3_SQLITE": "true",
            "SQLITE_S3_BUCKET": "mycompany-django-sqlite-db",
            "SQLITE_DB_NAME": "db.sqlite3"
        }
    }
}
```

### Step 3: Required IAM Permissions

Zappa automatically creates a basic Lambda execution role. Ensure the role (or your custom execution role) has permissions to read and write to your SQLite bucket:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::mycompany-django-sqlite-db",
                "arn:aws:s3:::mycompany-django-sqlite-db/*"
            ]
        }
    ]
}
```

### Step 4: Deploy First Time

Run the initial deployment:

```bash
uv run zappa deploy dev
```

Zappa will package the project, upload it to S3, configure the AWS Lambda function and Amazon API Gateway, and output your live endpoint URL (e.g., `https://xxxxxx.execute-api.us-east-1.amazonaws.com/dev`).

### Step 5: Run Remote Migrations & Create Admin

Run Django management commands directly on AWS Lambda:

```bash
# Run database migrations remotely on Lambda
uv run zappa manage dev migrate

# Create admin superuser remotely
uv run zappa manage dev createsuperuser
```

### Step 6: Subsequent Updates

Whenever you make code changes, update your deployment:

```bash
uv run zappa update dev
```

---

## Automated CI/CD with GitHub Actions

The repository includes a ready-to-use GitHub Actions workflow in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) consisting of two decoupled jobs:

1. **`Lint & Test`**: Runs automatically on all pushes and pull requests. Sets up Python 3.13 via `uv`, runs pre-commit hooks via `prek` (Ruff formatting, linting, file hygiene), and executes `pytest` with `USE_S3_SQLITE=false`. **Requires zero cloud credentials.**
2. **`Deploy to AWS Lambda`**: Triggered upon push to `main` (or via manual `workflow_dispatch`). Verifies credentials, runs `zappa update` (or `zappa deploy`), and applies remote database migrations.

### Enabling Automated Deployments

By default, the deployment job checks whether AWS secrets are present. If secrets are not configured, it emits a warning notice and safely skips deployment so your automated test pipeline stays green.

To enable automated AWS deployments from GitHub Actions, configure the required AWS credentials as repository secrets:

#### Option A: Using GitHub CLI (`gh`) (Recommended)

Run the following commands in your local terminal. The GitHub CLI will prompt you securely for each value without echoing or logging sensitive keys:

```bash
# Set AWS Access Key ID
gh secret set AWS_ACCESS_KEY_ID

# Set AWS Secret Access Key
gh secret set AWS_SECRET_ACCESS_KEY

# Set AWS Default Region (e.g. us-east-2)
gh secret set AWS_DEFAULT_REGION -b "us-east-2"
```

#### Option B: Using the GitHub Web Interface

1. Navigate to your repository on GitHub.
2. Go to **Settings** > **Secrets and variables** > **Actions**.
3. Under **Repository secrets**, click **New repository secret**.
4. Add the following secrets:
   - `AWS_ACCESS_KEY_ID`: IAM access key ID with Zappa and S3 permissions.
   - `AWS_SECRET_ACCESS_KEY`: IAM secret access key.
   - `AWS_DEFAULT_REGION`: AWS region for your deployment (e.g., `us-east-2`).

### Manual Workflow Dispatch

You can also trigger a deployment on demand to any Zappa stage (e.g., `dev` or `prod`) directly from GitHub:
1. Navigate to the **Actions** tab in your repository.
2. Select **CI & CD (Zappa AWS Lambda)** in the left sidebar.
3. Click **Run workflow**, choose your branch and target stage, and click **Run workflow**.

## Multi-Architecture (ARM64 & AMD64) Packaging with Docker

AWS Lambda in this template defaults to **ARM64 (AWS Graviton)** (`"architecture": "arm64"` in `zappa_settings.json`). When packages contain compiled C-extensions (such as cryptography, regex, or database drivers), they must be compiled for the target Lambda architecture.

The project provides dual-architecture compatibility across both **ARM64** and **AMD64/x86_64**:
- **`Dockerfile`**: Multi-platform container definition leveraging multi-arch base images (`python:3.13-slim` and `ghcr.io/astral-sh/uv:latest`) and frozen dependency resolution (`uv sync --frozen`).
- **`docker-compose.yml`**: Configures `platform: ${DOCKER_DEFAULT_PLATFORM:-linux/arm64}`, allowing dynamic platform selection.
- **`scripts/zappa-docker.sh` & `scripts/zappa-docker.ps1`**: Build and execute container operations with explicit platform tags. Both scripts default to `linux/arm64` while allowing easy overrides to `amd64`.

### Running the Docker Deployment Helper

```powershell
# Using PowerShell helper script (Windows - defaults to ARM64):
.\scripts\zappa-docker.ps1 update dev
.\scripts\zappa-docker.ps1 manage dev migrate

# Explicitly target AMD64/x86_64 in PowerShell:
.\scripts\zappa-docker.ps1 -Platform amd64 update dev

# Using Bash helper script (macOS / Linux - defaults to ARM64):
./scripts/zappa-docker.sh update dev
./scripts/zappa-docker.sh manage dev migrate

# Explicitly target AMD64 in Bash:
TARGET_ARCH=amd64 ./scripts/zappa-docker.sh update dev

# Or using Docker Compose / Podman Compose:
docker compose run --rm zappa update dev
# Target AMD64 via Compose:
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose run --rm zappa update dev
```

### Running ARM64 Containers on x86_64 Hosts

If your host machine uses an x86_64 (Intel/AMD) CPU, your system must support multi-architecture emulation via QEMU:

- **Docker Desktop (Windows / macOS):** Emulation is built-in and enabled out of the box.
- **Linux / WSL2 (Podman or Native Docker):** If you encounter `exec container process /bin/sh: Exec format error`, your Linux kernel needs QEMU binfmt emulation registered. Install `qemu-user-static`:
  ```bash
  sudo apt-get update && sudo apt-get install -y qemu-user-static binfmt-support
  ```
  Or register emulation via `tonistiigi/binfmt`:
  ```bash
  docker run --privileged --rm docker.io/tonistiigi/binfmt --install arm64
  ```

---

## Static Files Management

This template provides two options for serving static files:

1. **WhiteNoise (Default):** Static assets are bundled into the Lambda package and served directly with compression and caching headers via WhiteNoise. Ideal for quick setups and smaller asset libraries.
2. **Amazon S3 (`django-storages`):** To serve static files from S3/CloudFront, set in `zappa_settings.json` or `.env`:
   - `USE_S3_STATIC=True`
   - `AWS_STORAGE_BUCKET_NAME=mycompany-static-assets`
   Then collect static files:
   ```bash
   uv run python manage.py collectstatic --noinput
   # or remotely:
   uv run zappa manage dev collectstatic --noinput
   ```

---

## Code Quality & Pre-commit Hooks (`prek`)

This project uses [**`prek`**](https://github.com/j178/prek) — a fast, Rust-based Git hooks manager — to automatically run Ruff linting, formatting, and file hygiene checks prior to committing:

```bash
# 1. Install Git hook shims into .git/hooks/
uv run prek install

# 2. Run all hooks manually across the entire codebase
uv run prek run --all-files
```

The hooks are configured in [`prek.toml`](file:///C:/Users/dunn0172/Documents/GitHub/django-zappa-uv/prek.toml) and include:
- **`ruff`**: Python linting with automatic fixes (`--fix`).
- **`ruff-format`**: Code formatting.
- **Builtin checks**: Trailing whitespace removal, end-of-file fixer, YAML/TOML syntax validation, and large file prevention.

---

## Running Automated Tests

Run the test suite with `pytest`:

```bash
uv run pytest
```

---

## Common Commands Cheat Sheet

| Task | Command |
| :--- | :--- |
| **Sync dependencies** | `uv sync` |
| **Install git hooks** | `uv run prek install` |
| **Run pre-commit checks** | `uv run prek run --all-files` |
| **Format & lint code** | `uv run ruff check --fix . && uv run ruff format .` |
| **Run test suite** | `uv run pytest` |
| **Add dependency** | `uv add <package>` |
| **Local runserver** | `uv run python manage.py runserver` |
| **Run migrations locally** | `uv run python manage.py migrate` |
| **Deploy first time** | `uv run zappa deploy dev` |
| **Update deployment** | `uv run zappa update dev` |
| **Run remote migration** | `uv run zappa manage dev migrate` |
| **Tail CloudWatch logs** | `uv run zappa tail dev` |
| **Check Lambda status** | `uv run zappa status dev` |
| **Undeploy / delete stack** | `uv run zappa undeploy dev` |

---

## Automated Dependency Updates (Dependabot & uv)

The template includes out-of-the-box automated dependency maintenance:
- [`.github/dependabot.yml`](file:///C:/Users/dunn0172/Documents/GitHub/django-zappa-uv/.github/dependabot.yml): Configured for weekly grouped updates for Python dependencies (`pyproject.toml`) and GitHub Actions workflows every Monday at 04:00 UTC, bundling updates into consolidated PRs to minimize noise.
- [`.github/workflows/dependabot-uv.yml`](file:///C:/Users/dunn0172/Documents/GitHub/django-zappa-uv/.github/workflows/dependabot-uv.yml):
  - **Weekly lockfile upgrades**: Automatically executes `uv lock --upgrade`, runs quality checks and unit tests, and submits an automated pull request.
  - **Dependabot lockfile synchronization**: Automatically generates and commits the matching `uv.lock` whenever Dependabot updates `pyproject.toml`.

---

## License

MIT License. Feel free to use this template for personal, academic, or commercial projects.
