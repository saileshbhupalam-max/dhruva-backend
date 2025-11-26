# Database Seed Scripts

This directory contains SQL scripts to populate the database with initial data.

## Scripts

1. **seed_districts.sql** - All 26 Andhra Pradesh districts with district codes
2. **seed_departments.sql** - 15 major government departments handling grievances
3. **seed_test_users.sql** - Sample users (5 citizens + 3 officials) for testing

## Running Seed Scripts

### Using psql Command Line

```bash
# Set environment variable for password (optional)
set PGPASSWORD=your_password

# Run districts seed
psql -h localhost -U postgres -d dhruva_pgrs -f backend/app/scripts/seed_districts.sql

# Run departments seed
psql -h localhost -U postgres -d dhruva_pgrs -f backend/app/scripts/seed_departments.sql

# Run test users seed
psql -h localhost -U postgres -d dhruva_pgrs -f backend/app/scripts/seed_test_users.sql
```

### Using Python Script (Alternative)

```python
import asyncio
import asyncpg

async def run_seed_script(script_path: str):
    conn = await asyncpg.connect(
        "postgresql://postgres:password@localhost/dhruva_pgrs"
    )
    with open(script_path, 'r') as f:
        sql = f.read()
    await conn.execute(sql)
    await conn.close()

# Run for each script
asyncio.run(run_seed_script("backend/app/scripts/seed_districts.sql"))
```

## Verification

Each script includes verification queries in comments. Run them after seeding:

```sql
-- Verify districts (expect 26)
SELECT COUNT(*) FROM districts;

-- Verify departments (expect 15)
SELECT COUNT(*) FROM departments;

-- Verify users (expect 8)
SELECT role, COUNT(*) FROM users WHERE deleted_at IS NULL GROUP BY role;
```

## Important Notes

1. Scripts use `ON CONFLICT DO NOTHING` to be idempotent (safe to run multiple times)
2. Run scripts in order: districts → departments → users
3. UUIDs are generated using PostgreSQL's `gen_random_uuid()` function
4. Timestamps use `NOW()` for current timestamp
5. Scripts are safe for both development and test databases
