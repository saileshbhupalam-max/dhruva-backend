# Migration Troubleshooting

## Rollback Failed Migration

```bash
# Check current migration
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.current(cfg)"

# Rollback one version
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.downgrade(cfg, '-1')"

# Fix migration file (alembic/versions/*.py)

# Re-apply migration
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.upgrade(cfg, 'head')"
```

## Reset Database (Development Only - DESTRUCTIVE)

```bash
# Rollback all migrations
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.downgrade(cfg, 'base')"

# Drop schema (if needed) - WARNING: THIS DELETES ALL DATA
psql -U postgres -d dhruva_pgrs -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-run migrations
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.upgrade(cfg, 'head')"

# Re-seed data
psql -U postgres -d dhruva_pgrs -f backend/db/seeds/seed_data.sql
```

## Check Migration History

```bash
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.history(cfg, verbose=True)"
```

## Common Issues

### Issue: "Target database is not up to date"

**Solution**: Check current revision and upgrade:
```bash
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.current(cfg)"
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.upgrade(cfg, 'head')"
```

### Issue: "Can't locate revision identified by 'xxx'"

**Solution**: This usually means the alembic_version table is out of sync:
```bash
# Check database revision
psql -U postgres -d dhruva_pgrs -c "SELECT * FROM alembic_version;"

# Manually set correct revision (replace 'xxx' with actual revision)
psql -U postgres -d dhruva_pgrs -c "UPDATE alembic_version SET version_num = 'xxx';"
```

### Issue: Migration fails midway

**Solution**: Alembic migrations are transactional. If a migration fails, no changes are committed. Simply fix the migration file and re-run:
```bash
# Check what failed
tail -n 50 /var/log/dhruva/app.log

# Fix the migration file
# Re-run
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.upgrade(cfg, 'head')"
```

## Testing Migrations

### Test migration on clean database

```bash
# Create test database
createdb -U postgres dhruva_pgrs_migration_test

# Run migrations
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/dhruva_pgrs_migration_test"
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.upgrade(cfg, 'head')"

# Verify all tables exist
psql -U postgres -d dhruva_pgrs_migration_test -c "\dt"

# Test rollback
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.downgrade(cfg, 'base')"

# Cleanup
dropdb -U postgres dhruva_pgrs_migration_test
unset DATABASE_URL
```

## Windows-Specific Commands

### PowerShell equivalents

```powershell
# Set DATABASE_URL
$env:DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/dhruva_pgrs_test"

# Run migration
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.upgrade(cfg, 'head')"

# Unset DATABASE_URL
Remove-Item Env:\DATABASE_URL
```
