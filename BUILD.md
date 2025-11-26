# TASK_001 Database Foundation - Build Instructions

## Prerequisites

1. **PostgreSQL 15+** installed and running
2. **Python 3.11+** installed
3. **Git** (already initialized)

## Step 1: Database Setup

### Create PostgreSQL Databases

```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create main database
CREATE DATABASE dhruva_pgrs;

-- Create test database
CREATE DATABASE dhruva_pgrs_test;

-- Enable UUID extension on both databases
\c dhruva_pgrs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c dhruva_pgrs_test
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

## Step 2: Virtual Environment Setup

### Windows
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
```

### Linux/Mac
```bash
cd backend
python -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Environment Configuration

```bash
# Copy example environment file
copy .env.example .env  # Windows
# OR
cp .env.example .env    # Linux/Mac

# Edit .env and update:
# - DATABASE_URL with your PostgreSQL credentials
# - TEST_DATABASE_URL with your test database credentials
```

## Step 5: Run Alembic Migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "initial schema"

# Apply migrations
alembic upgrade head

# Verify current version
alembic current
```

## Step 6: Seed Data

```bash
# Set PostgreSQL password
set PGPASSWORD=your_password  # Windows
export PGPASSWORD=your_password  # Linux/Mac

# Run seed scripts
psql -h localhost -U postgres -d dhruva_pgrs -f app/scripts/seed_districts.sql
psql -h localhost -U postgres -d dhruva_pgrs -f app/scripts/seed_departments.sql
psql -h localhost -U postgres -d dhruva_pgrs -f app/scripts/seed_test_users.sql
```

## Step 7: Run Tests

```bash
# Run all tests with coverage
pytest

# Run only integration tests
pytest -m integration

# Run with verbose output
pytest -v

# Check coverage report
# Coverage report will be in htmlcov/index.html
```

## Step 8: Code Quality Checks

```bash
# Run black formatter
black app/ --check

# Format code
black app/

# Run flake8 linter
flake8 app/

# Run mypy type checker
mypy app/
```

## Step 9: Start Application

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access health check
# Browser: http://localhost:8000/health
# curl: curl http://localhost:8000/health
```

## Verification Checklist

- [ ] PostgreSQL databases created (dhruva_pgrs, dhruva_pgrs_test)
- [ ] UUID extension enabled on both databases
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] .env file configured with correct credentials
- [ ] Alembic migrations generated and applied
- [ ] All seed scripts executed successfully
- [ ] Pytest runs with 80%+ coverage
- [ ] Black formatting passes
- [ ] Flake8 linting passes
- [ ] Mypy type checking passes
- [ ] Health check endpoint returns 200 OK
- [ ] Database connection verified in health check

## Quick Start (All-in-One)

```bash
# Full setup script (after prerequisites installed)
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
# Configure .env manually
alembic upgrade head
pytest
uvicorn app.main:app --reload
```

## Troubleshooting

### Database Connection Error
- Verify PostgreSQL is running: `psql -U postgres -c "SELECT version();"`
- Check credentials in .env file
- Ensure databases exist: `psql -U postgres -l`

### Migration Error
- Drop and recreate test database if needed
- Check alembic/versions directory for conflicts
- Run `alembic history` to see migration chain

### Test Failures
- Ensure test database is clean: `pytest --create-db`
- Check test database URL in .env
- Verify all dependencies installed correctly

### Import Errors
- Ensure virtual environment is activated
- Run `pip list` to verify all packages installed
- Check Python version: `python --version` (should be 3.11+)

## Performance Targets

- Database queries: < 100ms p95
- Test coverage: 80%+ (currently should be 85-90%)
- Type coverage: 100% (mypy strict mode)
- Health check response: < 50ms

## Next Steps

After TASK_001 completion:
1. Mark checkboxes in PROJECT_ROADMAP.md
2. Commit all changes with proper message
3. Proceed to TASK_002 (API Layer)
