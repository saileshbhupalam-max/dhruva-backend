# Database Verification

## Verify Tables

```bash
psql -U postgres -d dhruva_pgrs -c "\dt"
```

Expected output:
```
             List of relations
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+----------
 public | alembic_version | table | postgres
 public | attachments     | table | postgres
 public | audit_logs      | table | postgres
 public | departments     | table | postgres
 public | districts       | table | postgres
 public | grievances      | table | postgres
 public | users           | table | postgres
 public | verifications   | table | postgres
(8 rows)
```

## Verify Indexes

```bash
psql -U postgres -d dhruva_pgrs -c "\d+ grievances"
```

Expected indexes:
- `ix_grievances_grievance_id`
- `ix_grievances_citizen_id`
- `ix_grievances_district_id`
- `ix_grievances_department_id`
- `ix_grievances_status`
- `idx_grievances_district_status` (composite, partial)
- `idx_grievances_department_created` (composite)

```bash
psql -U postgres -d dhruva_pgrs -c "\d+ users"
```

Expected indexes:
- `ix_users_mobile_number`
- `ix_users_email`
- `idx_users_role_mobile` (composite)
- `idx_users_email_role` (composite)

```bash
psql -U postgres -d dhruva_pgrs -c "\d+ audit_logs"
```

Expected indexes:
- `ix_audit_logs_grievance_id`
- `ix_audit_logs_user_id`
- `ix_audit_logs_action`
- `ix_audit_logs_current_hash`
- `ix_audit_logs_timestamp`
- `idx_audit_logs_recent` (partial index for last 90 days)

## Verify Constraints

```bash
psql -U postgres -d dhruva_pgrs -c "SELECT conname FROM pg_constraint WHERE conrelid = 'grievances'::regclass;"
```

Expected constraints:
- `check_resolved_at_valid`
- `check_resolved_at_requires_status`

```bash
psql -U postgres -d dhruva_pgrs -c "SELECT conname FROM pg_constraint WHERE conrelid = 'attachments'::regclass;"
```

Expected constraints:
- `check_file_size_valid`

## Verify Triggers

```bash
psql -U postgres -d dhruva_pgrs -c "SELECT tgname FROM pg_trigger WHERE tgrelid = 'grievances'::regclass;"
```

Expected triggers:
- `update_grievances_updated_at`

```bash
# Check all updated_at triggers
psql -U postgres -d dhruva_pgrs -c "
SELECT t.tgname AS trigger_name,
       c.relname AS table_name
FROM pg_trigger t
JOIN pg_class c ON t.tgrelid = c.oid
WHERE t.tgname LIKE 'update_%_updated_at'
ORDER BY c.relname;
"
```

Expected triggers (7 tables):
- `update_districts_updated_at`
- `update_departments_updated_at`
- `update_users_updated_at`
- `update_grievances_updated_at`
- `update_attachments_updated_at`
- `update_audit_logs_updated_at`
- `update_verifications_updated_at`

## Verify Extensions

```bash
psql -U postgres -d dhruva_pgrs -c "\dx"
```

Expected extensions:
- `plpgsql` (built-in)
- `pgcrypto` (for gen_random_uuid and digest)

## Verify Trigger Function

```bash
psql -U postgres -d dhruva_pgrs -c "\df update_updated_at_column"
```

Expected output:
```
                                    List of functions
 Schema |         Name               | Result data type | Argument data types | Type
--------+----------------------------+------------------+---------------------+--------
 public | update_updated_at_column   | trigger          |                     | func
```

## Test Trigger Functionality

```bash
# Test updated_at trigger on districts table
psql -U postgres -d dhruva_pgrs -c "
INSERT INTO districts (id, district_code, district_name)
VALUES (gen_random_uuid(), 'TEST', 'Test District');

SELECT district_code, created_at, updated_at
FROM districts
WHERE district_code = 'TEST';

-- Wait 2 seconds
SELECT pg_sleep(2);

UPDATE districts
SET district_name = 'Test District Updated'
WHERE district_code = 'TEST';

SELECT district_code, created_at, updated_at
FROM districts
WHERE district_code = 'TEST';

-- Cleanup
DELETE FROM districts WHERE district_code = 'TEST';
"
```

Expected: `updated_at` should be later than `created_at` after UPDATE.

## Verify Foreign Keys

```bash
psql -U postgres -d dhruva_pgrs -c "
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
  ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;
"
```

Expected foreign keys:
- `grievances.citizen_id` → `users.id` (RESTRICT)
- `grievances.district_id` → `districts.id` (RESTRICT)
- `grievances.department_id` → `departments.id` (RESTRICT)
- `attachments.grievance_id` → `grievances.id` (CASCADE)
- `audit_logs.grievance_id` → `grievances.id` (CASCADE)
- `audit_logs.user_id` → `users.id` (RESTRICT)
- `verifications.grievance_id` → `grievances.id` (CASCADE)

## Database Size and Performance

```bash
# Check table sizes
psql -U postgres -d dhruva_pgrs -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY bytes DESC;
"

# Check index sizes
psql -U postgres -d dhruva_pgrs -c "
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexname::regclass) DESC;
"
```

## Quick Verification Script

```bash
#!/bin/bash
# save as verify_database.sh

DB_NAME="dhruva_pgrs"
DB_USER="postgres"

echo "=== Tables ==="
psql -U $DB_USER -d $DB_NAME -c "\dt" -t | wc -l
echo "Expected: 8 tables (including alembic_version)"

echo -e "\n=== Indexes ==="
psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';" -t
echo "Expected: 20+ indexes"

echo -e "\n=== Triggers ==="
psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE 'update_%_updated_at';" -t
echo "Expected: 7 triggers"

echo -e "\n=== Extensions ==="
psql -U $DB_USER -d $DB_NAME -c "\dx pgcrypto" -t | wc -l
echo "Expected: pgcrypto extension installed"

echo -e "\n=== Constraints ==="
psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM pg_constraint WHERE contype = 'c' AND conrelid IN (SELECT oid FROM pg_class WHERE relnamespace = 'public'::regnamespace);" -t
echo "Expected: 3+ CHECK constraints"
```
