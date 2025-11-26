# Data Import Prevention Guide - DHRUVA PGRS

## Document Purpose
This guide documents all issues encountered during ML data import (Phase 3, Day 1) and provides systematic prevention strategies for future data import operations.

---

## Issues Encountered & Root Causes

### 1. **Schema Mismatch Between Models and Database**

**Issue**: Import scripts referenced `name_english` field but database had `dept_name`.

**Root Cause**:
- Migration autogeneration didn't detect new ML models
- Models were added but migration only contained schema alterations
- No verification of migration contents before applying

**Prevention**:
```bash
# ALWAYS verify migration after generation
alembic revision --autogenerate -m "description"
# Then MANUALLY review the generated migration file
cat alembic/versions/XXXX_*.py | grep "op.create_table"

# Verify table creation commands are present
# If missing, regenerate or write manual migration
```

**Checklist**:
- [ ] Read generated migration file completely
- [ ] Verify `op.create_table()` calls for new models
- [ ] Check column names match model definitions
- [ ] Test migration in development before applying

---

### 2. **Empty Reference Tables (Departments/Districts)**

**Issue**: 0 departments and 0 districts in database, causing all FK-dependent imports to skip records.

**Root Cause**:
- Seed scripts existed but were never executed
- No automated seeding in migration or setup process
- Seed SQL had schema mismatches (missing required columns)

**Prevention**:
```bash
# Create setup verification script
cat > backend/scripts/verify_setup.py << 'EOF'
import asyncio
from sqlalchemy import select, func
from app.database import get_session
from app.models import Department, District

async def verify():
    async for session in get_session():
        dept_count = await session.scalar(select(func.count(Department.id)))
        dist_count = await session.scalar(select(func.count(District.id)))

        print(f"Departments: {dept_count}")
        print(f"Districts: {dist_count}")

        if dept_count == 0 or dist_count == 0:
            print("ERROR: Reference tables empty. Run seed scripts first!")
            exit(1)

asyncio.run(verify())
EOF

# Run BEFORE any data import
python backend/scripts/verify_setup.py
```

**Checklist**:
- [ ] Always seed reference tables FIRST
- [ ] Verify seed SQL matches current schema
- [ ] Run count queries before import
- [ ] Document seeding order in README

---

### 3. **Seed SQL Schema Mismatch**

**Issue**: `seed_departments.sql` used `dept_name` initially, then `name_english`, but actual column was `dept_name`.

**Root Cause**:
- Seed SQL not updated when schema changed
- No automated testing of seed scripts
- Manual SQL instead of using models

**Prevention**:
```python
# Use Python seed scripts with actual models instead of SQL
# backend/scripts/seed_data.py

async def seed_departments():
    """Seed departments using actual models."""
    departments = [
        Department(dept_code="RD", dept_name="Rural Development",
                   name_telugu="గ్రామీణాభివృద్ధి", sla_days=7),
        # ... more departments
    ]

    async for session in get_session():
        for dept in departments:
            session.add(dept)
        await session.commit()

# This ensures schema compliance at code level
```

**Checklist**:
- [ ] Prefer Python seed scripts over raw SQL
- [ ] Use actual model classes for seeding
- [ ] Test seed scripts against current schema
- [ ] Version control seed data with migrations

---

### 4. **Data Naming Inconsistency**

**Issue**: Import scripts looked up departments by `name_english` from JSON, but some had slight variations:
- JSON: "Rural Development"
- DB: "Rural Development" ✓
- JSON: "Revenue (CCLA)"
- DB: "Revenue Department" ✗

**Root Cause**:
- Government data uses full official names
- Seed data uses abbreviated names
- No normalization or mapping layer

**Prevention**:
```python
# Create department name mapping
DEPARTMENT_ALIASES = {
    "Revenue (CCLA)": "Revenue Department",
    "Survey Settlements and Land Records": "Revenue Department",
    "AP Southern Power Distribution Co Ltd (SPDCL)": "Energy Department",
    # ... complete mapping
}

def normalize_department_name(raw_name: str) -> str:
    """Normalize department name to match database."""
    return DEPARTMENT_ALIASES.get(raw_name, raw_name)

# Use in import scripts
dept = db_departments.get(normalize_department_name(dept_name))
```

**Checklist**:
- [ ] Create comprehensive name mapping file
- [ ] Extract all unique names from government data
- [ ] Map to seed data names
- [ ] Use fuzzy matching as fallback

---

### 5. **Duplicate Records in Source Data**

**Issue**: 54 templates in JSON, but 10 duplicates (template_id), only 44 unique.

**Root Cause**:
- Source data extraction didn't deduplicate
- No unique constraint checking before insert
- Import script assumed clean data

**Prevention**:
```python
# Always check for duplicates BEFORE import
def validate_source_data(json_path):
    """Validate source data before import."""
    with open(json_path) as f:
        data = json.load(f)

    items = data.get('templates', [])
    ids = [item['template_id'] for item in items]

    if len(ids) != len(set(ids)):
        dupes = [id for id in ids if ids.count(id) > 1]
        print(f"WARNING: Found {len(dupes)} duplicate IDs: {set(dupes)}")
        return False

    return True

# Use in import
if not validate_source_data(json_path):
    print("Fix source data before importing")
    exit(1)
```

**Checklist**:
- [ ] Validate source data before import
- [ ] Check for duplicates on unique fields
- [ ] Log skipped duplicates
- [ ] Consider using UPSERT logic

---

### 6. **Incomplete Department Coverage**

**Issue**: Seed data has 15 departments, government data references 30+ departments.

**Root Cause**:
- Seed data created manually with subset
- No automated extraction of all department names from government docs
- Missing departments cause silent data loss

**Prevention**:
```python
# Extract ALL unique departments from government data FIRST
def extract_all_departments():
    """Extract all unique departments from all government data sources."""
    all_departments = set()

    # From PGRS keywords
    with open('pgrs_book_keywords.json') as f:
        data = json.load(f)
        for dept in data['departments']:
            all_departments.add(dept['name_english'])

    # From officer performance
    with open('officer_performance.json') as f:
        data = json.load(f)
        for officer in data['officers']:
            all_departments.add(officer['department'])

    # From satisfaction metrics
    # ... repeat for all sources

    print(f"Found {len(all_departments)} unique departments")
    return sorted(all_departments)

# Generate comprehensive seed data from extraction
```

**Checklist**:
- [ ] Extract all unique departments from ALL data sources
- [ ] Generate seed data programmatically
- [ ] Verify 100% coverage before import
- [ ] Log unmatched departments during import

---

### 7. **Missing District Mappings**

**Issue**: 26 districts seeded, but lapse cases reference "Guntur" and other variations.

**Root Cause**:
- District seed data from separate source
- Audit reports use different district naming
- No validation of district name consistency

**Prevention**:
- Same as #6 - extract ALL unique districts first
- Create mapping file for variations
- Normalize before lookup

---

### 8. **Async Session Management Issues**

**Issue**: Some imports failed silently due to session not committing properly.

**Root Cause**:
- Using `session.commit()` inside transaction block
- `async with session.begin()` already manages transaction
- Double commit or rollback on error

**Prevention**:
```python
# CORRECT pattern:
async with async_session() as session:
    async with session.begin():
        # Add all data
        for item in items:
            session.add(Model(**item))
        # Transaction auto-commits on exit

# INCORRECT pattern:
async with async_session() as session:
    async with session.begin():
        for item in items:
            session.add(Model(**item))
        await session.commit()  # WRONG - double commit
```

**Checklist**:
- [ ] Never call commit() inside begin() block
- [ ] Let context manager handle transaction
- [ ] Use rollback only on exceptions
- [ ] Test with small batch first

---

### 9. **Unicode Encoding Issues in Output**

**Issue**: Windows console couldn't display Telugu characters, causing script crashes.

**Root Cause**:
- Console encoding set to cp1252
- Telugu characters in error messages
- No UTF-8 handling in print statements

**Prevention**:
```python
# Set UTF-8 encoding at start of script
import sys
import io

# Force UTF-8 for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# OR strip non-ASCII from error messages
try:
    # ... code
except Exception as e:
    error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
    print(f"ERROR: {error_msg}")
```

**Checklist**:
- [ ] Set UTF-8 encoding in all import scripts
- [ ] Sanitize error messages for console
- [ ] Test on Windows with Telugu data
- [ ] Use logging instead of print

---

### 10. **No Pre-Import Validation**

**Issue**: Discovered data issues AFTER import started.

**Root Cause**:
- No validation phase before import
- Assumed data quality
- No dry-run mode

**Prevention**:
```python
def validate_before_import():
    """Run all validations before starting import."""
    validations = [
        ("Database Connection", check_db_connection),
        ("Reference Tables", check_reference_tables),
        ("Source Data Files", check_source_files),
        ("Schema Compatibility", check_schema_match),
        ("Data Duplicates", check_duplicates),
        ("Department Coverage", check_department_coverage),
    ]

    print("Pre-Import Validation")
    print("=" * 60)

    for name, func in validations:
        try:
            result = func()
            status = "PASS" if result else "FAIL"
            print(f"[{status}] {name}")
            if not result:
                return False
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            return False

    return True

# Always run before import
if not validate_before_import():
    print("\nValidation failed. Fix issues before importing.")
    exit(1)
```

**Checklist**:
- [ ] Create validation script
- [ ] Run before every import
- [ ] Log all validation results
- [ ] Fail fast on critical issues

---

## Recommended Import Workflow

```bash
# 1. Verify Environment
python backend/scripts/verify_environment.py

# 2. Check Database Connection
python backend/scripts/check_db.py

# 3. Seed Reference Tables (if empty)
python backend/scripts/seed_departments.py
python backend/scripts/seed_districts.py

# 4. Validate Reference Data
python backend/scripts/validate_references.py

# 5. Extract Department/District Mappings
python backend/ml/extract_mappings.py

# 6. Validate Source Data
python backend/ml/validate_source_data.py

# 7. Dry Run Import (no commit)
python backend/ml/scripts/import_all.py --dry-run

# 8. Review Dry Run Report
cat backend/ml/import_dry_run_report.txt

# 9. Run Actual Import
python backend/ml/scripts/import_all.py

# 10. Verify Import Results
python backend/ml/scripts/verify_import.py
```

---

## Critical Checklist for Future Imports

### Before Starting
- [ ] Database is running and accessible
- [ ] Latest migrations applied
- [ ] Reference tables seeded
- [ ] All source data files present
- [ ] Source data validated (no duplicates)
- [ ] Schema matches between models and DB

### Department/District Handling
- [ ] All unique names extracted from government data
- [ ] Mapping file created for name variations
- [ ] Seed data covers 100% of government data
- [ ] Normalization function implemented

### Import Scripts
- [ ] Use actual models, not raw SQL
- [ ] Proper async session management
- [ ] UTF-8 encoding for console output
- [ ] Error messages sanitized for display
- [ ] Duplicate handling logic
- [ ] Transaction boundaries correct
- [ ] Validation before insert

### Testing
- [ ] Dry run completed successfully
- [ ] Small batch test (10 records)
- [ ] Full import test in dev environment
- [ ] Verification queries run
- [ ] Count matches expected values

### Documentation
- [ ] Import process documented
- [ ] Data sources documented
- [ ] Known issues logged
- [ ] Workarounds documented

---

## Lessons Learned

1. **Always verify migrations**: Autogeneration can fail silently
2. **Seed first, import second**: Reference data must exist
3. **Extract before mapping**: Let data drive the schema
4. **Validate early**: Catch issues before import starts
5. **Use models over SQL**: Type safety and schema compliance
6. **Plan for variations**: Government data is inconsistent
7. **Test incrementally**: Small batches before full import
8. **Document everything**: Future you will thank present you

---

## Tools to Build

1. **Department Mapper**: Extract and normalize all department names
2. **Data Validator**: Pre-import validation suite
3. **Import Verifier**: Post-import verification queries
4. **Seed Generator**: Auto-generate seeds from government data
5. **Dry Run Mode**: Test imports without committing

---

**Document Version**: 1.0
**Created**: 2025-11-25
**Author**: DHRUVA Development Team
**Status**: Living Document - Update with new learnings
