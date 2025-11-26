# Pagination Strategy

## Overview

This guide covers two pagination strategies for the DHRUVA PGRS system:
1. **Offset-Based Pagination** - Simple, supports random page access
2. **Cursor-Based Pagination** - Scalable, better performance for large datasets

## Offset-Based Pagination (Simple)

### Use Cases
- Admin dashboards with page numbers
- Reports requiring total count
- Small to medium datasets (< 10,000 rows)
- When users need to jump to specific pages

### Implementation

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Grievance
from typing import List

async def get_grievances_paginated(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None
) -> tuple[List[Grievance], int]:
    """
    Get paginated grievances with total count.

    Args:
        session: Database session
        page: Page number (1-indexed)
        page_size: Number of results per page
        status_filter: Optional status filter

    Returns:
        Tuple of (grievances list, total count)
    """
    # Calculate offset
    offset = (page - 1) * page_size

    # Build base query
    base_query = (
        select(Grievance)
        .where(Grievance.deleted_at == None)
    )

    if status_filter:
        base_query = base_query.where(Grievance.status == status_filter)

    # Get total count
    from sqlalchemy import func
    count_query = select(func.count()).select_from(base_query.subquery())
    total_count = await session.scalar(count_query)

    # Get paginated results
    query = (
        base_query
        .order_by(Grievance.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    result = await session.execute(query)
    grievances = list(result.scalars().all())

    return grievances, total_count
```

### Response Format

```python
from pydantic import BaseModel

class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_pages: int
    total_count: int
    has_next: bool
    has_previous: bool

class PaginatedResponse(BaseModel):
    data: list
    pagination: PaginationMeta

# Usage in endpoint
@router.get("/grievances")
async def list_grievances(
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_async_session)
):
    grievances, total_count = await get_grievances_paginated(
        session, page, page_size
    )

    total_pages = (total_count + page_size - 1) // page_size

    return PaginatedResponse(
        data=grievances,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            total_count=total_count,
            has_next=page < total_pages,
            has_previous=page > 1,
        )
    )
```

### Pros and Cons

**Pros:**
- Simple to implement
- Supports jumping to specific pages
- Familiar UX (page numbers)
- Total count available

**Cons:**
- Performance degrades with large offsets (OFFSET 10000 scans 10000 rows)
- Inconsistent results if data changes between requests
- Higher database load for large offsets

---

## Cursor-Based Pagination (Scalable)

### Use Cases
- Public APIs with large datasets
- Infinite scroll UIs
- Real-time feeds
- Large datasets (> 10,000 rows)
- When consistent performance is critical

### Implementation

```python
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Grievance

async def get_grievances_cursor(
    session: AsyncSession,
    cursor: Optional[datetime] = None,
    limit: int = 20,
    status_filter: str | None = None
) -> List[Grievance]:
    """
    Get grievances using cursor-based pagination.

    Args:
        session: Database session
        cursor: Last created_at timestamp from previous page
        limit: Number of results to return
        status_filter: Optional status filter

    Returns:
        List of grievances created before cursor
    """
    query = (
        select(Grievance)
        .where(Grievance.deleted_at == None)
    )

    if status_filter:
        query = query.where(Grievance.status == status_filter)

    if cursor:
        # Get records created before cursor
        query = query.where(Grievance.created_at < cursor)

    query = (
        query
        .order_by(Grievance.created_at.desc())
        .limit(limit + 1)  # Fetch one extra to check if more exist
    )

    result = await session.execute(query)
    grievances = list(result.scalars().all())

    # Check if more results exist
    has_more = len(grievances) > limit
    if has_more:
        grievances = grievances[:limit]

    return grievances, has_more
```

### Response Format

```python
from pydantic import BaseModel
from datetime import datetime

class CursorPaginationMeta(BaseModel):
    next_cursor: datetime | None
    has_more: bool
    limit: int

class CursorPaginatedResponse(BaseModel):
    data: list
    pagination: CursorPaginationMeta

# Usage in endpoint
@router.get("/grievances/feed")
async def list_grievances_feed(
    cursor: Optional[datetime] = None,
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session)
):
    grievances, has_more = await get_grievances_cursor(
        session, cursor, limit
    )

    # Next cursor is the created_at of the last item
    next_cursor = grievances[-1].created_at if grievances and has_more else None

    return CursorPaginatedResponse(
        data=grievances,
        pagination=CursorPaginationMeta(
            next_cursor=next_cursor,
            has_more=has_more,
            limit=limit,
        )
    )
```

### Frontend Implementation (Infinite Scroll)

```typescript
// React example with infinite scroll
const useInfiniteGrievances = () => {
  const [grievances, setGrievances] = useState([]);
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(true);

  const loadMore = async () => {
    const params = new URLSearchParams();
    if (cursor) params.append('cursor', cursor);
    params.append('limit', '20');

    const response = await fetch(`/api/grievances/feed?${params}`);
    const data = await response.json();

    setGrievances(prev => [...prev, ...data.data]);
    setCursor(data.pagination.next_cursor);
    setHasMore(data.pagination.has_more);
  };

  return { grievances, loadMore, hasMore };
};
```

### Pros and Cons

**Pros:**
- Consistent O(1) performance regardless of dataset size
- Handles real-time data changes gracefully
- Lower database load
- Efficient for infinite scroll

**Cons:**
- Cannot jump to specific pages
- No total count (expensive to compute)
- Slightly more complex implementation
- Requires indexed cursor column

---

## Index Requirements

### For Offset-Based Pagination

```python
# In app/models/grievance.py
__table_args__ = (
    # Single column index for ORDER BY
    Index('idx_grievances_created_at_desc', 'created_at'),

    # Composite index for filtered queries
    Index('idx_grievances_status_created', 'status', 'created_at'),
)
```

### For Cursor-Based Pagination

```python
# In app/models/grievance.py
__table_args__ = (
    # Composite index: filter + cursor column
    Index(
        'idx_grievances_status_created',
        'status', 'created_at',
        postgresql_where=text("deleted_at IS NULL")  # Partial index
    ),
)
```

---

## Choosing the Right Strategy

| Requirement | Offset-Based | Cursor-Based |
|------------|--------------|--------------|
| Total count needed | ✅ Yes | ❌ No |
| Jump to page N | ✅ Yes | ❌ No |
| Infinite scroll | ⚠️ OK | ✅ Best |
| Large datasets (>10k) | ❌ Slow | ✅ Fast |
| Real-time consistency | ❌ No | ✅ Yes |
| Implementation complexity | ✅ Simple | ⚠️ Medium |

### Recommendations

**Use Offset-Based For:**
- Admin dashboards showing "Page 1 of 45"
- Reports with export functionality
- Small datasets (< 10,000 rows)
- When total count is required

**Use Cursor-Based For:**
- Public grievance feed (infinite scroll)
- Mobile apps
- Large datasets (> 10,000 rows)
- Real-time updates

---

## Performance Tips

### 1. Index Cursor Column

Always ensure the cursor column (`created_at`) is indexed:
```python
Index('idx_grievances_created_at_desc', 'created_at')
```

### 2. Use Partial Indexes for Soft Deletes

```python
Index(
    'idx_grievances_active',
    'created_at',
    postgresql_where=text("deleted_at IS NULL")
)
```

### 3. Avoid COUNT(*) with Cursor Pagination

If you must show "approximate" total:
```sql
SELECT reltuples::bigint AS estimate
FROM pg_class
WHERE relname = 'grievances';
```

### 4. Limit Page Size

Enforce maximum page size:
```python
MAX_PAGE_SIZE = 100

page_size = min(requested_page_size, MAX_PAGE_SIZE)
```

### 5. Cache Total Counts

For offset pagination, cache total counts:
```python
from redis import Redis

redis = Redis()
cache_key = f"grievances:count:{status_filter}"
total_count = redis.get(cache_key)

if not total_count:
    total_count = await get_total_count(session, status_filter)
    redis.setex(cache_key, 300, total_count)  # Cache 5 minutes
```

---

## Testing Pagination

### Unit Tests

```python
import pytest
from app.models import Grievance

@pytest.mark.asyncio
async def test_offset_pagination(async_session):
    # Create 50 test grievances
    for i in range(50):
        grievance = Grievance(...)
        async_session.add(grievance)
    await async_session.commit()

    # Test first page
    grievances, total = await get_grievances_paginated(async_session, page=1, page_size=20)
    assert len(grievances) == 20
    assert total == 50

    # Test last page
    grievances, total = await get_grievances_paginated(async_session, page=3, page_size=20)
    assert len(grievances) == 10
    assert total == 50

@pytest.mark.asyncio
async def test_cursor_pagination(async_session):
    # Create test data
    # ...

    # Test first page
    grievances, has_more = await get_grievances_cursor(async_session, cursor=None, limit=20)
    assert len(grievances) == 20
    assert has_more is True

    # Test next page with cursor
    cursor = grievances[-1].created_at
    next_grievances, has_more = await get_grievances_cursor(async_session, cursor=cursor, limit=20)
    assert len(next_grievances) == 20
```

---

## Migration from Offset to Cursor

If you need to support both (gradual migration):

```python
@router.get("/grievances")
async def list_grievances(
    # Offset-based params
    page: Optional[int] = None,
    page_size: int = 20,
    # Cursor-based params
    cursor: Optional[datetime] = None,
    limit: Optional[int] = None,
    session: AsyncSession = Depends(get_async_session)
):
    # If cursor provided, use cursor-based
    if cursor is not None:
        limit = limit or page_size
        grievances, has_more = await get_grievances_cursor(session, cursor, limit)
        return CursorPaginatedResponse(...)

    # Otherwise, use offset-based
    page = page or 1
    grievances, total_count = await get_grievances_paginated(session, page, page_size)
    return PaginatedResponse(...)
```

---

**Last Updated**: 2025-11-24
**Author**: DHRUVA PGRS Team
