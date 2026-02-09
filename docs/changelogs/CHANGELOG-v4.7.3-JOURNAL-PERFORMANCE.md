# Journal Performance Optimization - Descending Indexes

**Date**: 9 février 2026  
**Version**: v4.7.3  
**Issue**: Journal display was slow due to missing descending indexes on timestamp

## Problem Analysis

The Journal endpoint (`GET /history/tracks`) performs queries with:
```sql
SELECT * FROM listening_history 
WHERE [filters]
ORDER BY timestamp DESC
LIMIT 50 OFFSET [page]
```

**Without DESC indexes**, the database had to:
1. Find all matching rows (using available indexes)
2. **Sort them in memory** by timestamp DESC
3. Apply pagination (LIMIT/OFFSET)

This is extremely slow for large datasets because sorting in memory is an O(n log n) operation before pagination can even be applied.

## Solution: Descending Indexes

Added 3 specialized indexes with timestamp in **descending order**:

### 1. `idx_history_timestamp_desc`
- **Columns**: `timestamp DESC`
- **Purpose**: Indexes for core ORDER BY sorting
- **Benefit**: Database can retrieve rows pre-sorted without in-memory sort
- **Query pattern**: Any query with ORDER BY timestamp DESC

### 2. `idx_history_timestamp_source_desc`
- **Columns**: `timestamp DESC, source`
- **Purpose**: Optimizes filtered queries by source
- **Benefit**: Combines filter + sort in single index
- **Query pattern**: WHERE source = X ORDER BY timestamp DESC

### 3. `idx_history_timestamp_loved_desc`
- **Columns**: `timestamp DESC, loved`
- **Purpose**: Optimizes loved/unloved track queries
- **Benefit**: Combines filter + sort in single index
- **Query pattern**: WHERE loved = true/false ORDER BY timestamp DESC

## Performance Impact

### Before Optimization
- Large journal pages (e.g., page 50+) with full dataset
- Full-table scan followed by in-memory sort
- Query time: **O(n log n)** where n = all listening history rows

### After Optimization
- Direct index range scan
- Pre-sorted results retrieved directly
- Query time: **O(log n + rows_returned)** - dramatic improvement
- Pagination becomes efficient even at high page numbers

## Implementation Details

```python
# Migration: backend/alembic/versions/006_add_desc_indexes.py
# Application script: backend/apply_desc_indexes.py

# Indexes created via SQLite CREATE INDEX with DESC order
CREATE INDEX idx_history_timestamp_desc 
  ON listening_history(timestamp DESC);

CREATE INDEX idx_history_timestamp_source_desc 
  ON listening_history(timestamp DESC, source);

CREATE INDEX idx_history_timestamp_loved_desc 
  ON listening_history(timestamp DESC, loved);
```

## Affected Components

- ✅ **Frontend**: [Journal.tsx](../../frontend/src/pages/Journal.tsx) - Now displays instantly with live pagination
- ✅ **API**: `GET /history/tracks` endpoint ([history.py](../../backend/app/api/v1/content/history.py))
- ✅ **Database**: listening_history table indexed

## Testing

To verify the indexes:
```bash
# Run in backend directory
python apply_desc_indexes.py
```

Expected output:
```
✓ idx_history_timestamp_desc
✓ idx_history_timestamp_source_desc
✓ idx_history_timestamp_loved_desc
```

## Database Query Analysis

The Journal query pattern:
```python
query = db.query(ListeningHistory).join(Track).join(Album).join(Album.artists)
# Apply filters: source, loved, artist, album, start_date, end_date
query = query.order_by(ListeningHistory.timestamp.desc())
query = query.offset((page-1)*50).limit(50)
```

**Index selection logic**:
- With `idx_history_timestamp_desc`: Database uses this index for all queries
- When filtering by source: Uses `idx_history_timestamp_source_desc` if available
- When filtering by loved status: Uses `idx_history_timestamp_loved_desc` if available
- Falls back to `idx_history_timestamp_desc` for other filter combinations

## Related Changes

- Previous optimization: [v4.7.0 - 21 basic indexes](../changelogs/CHANGELOG-v4.7.0-DATABASE-OPTIMIZATION.md)
- Previous optimization: [Timeline refresh sync v4.7.3](../changelogs/CHANGELOG-v4.7.3-UI-REFRESH-SYNC.md)

## Notes

- DESC indexes are most critical for paginated queries with ORDER BY DESC
- Index maintenance (inserts/updates) is slightly higher but query performance gain is worth it
- SQLite supports DESC in composite indexes (PostgreSQL/MySQL also support)
- No schema changes needed - purely index-based optimization
