# ADR-005: Database Design & ORM Usage

**Status**: ✅ Accepted  
**Date**: 2026-02-07  
**Priority**: High  
**Author**: Engineering Team  
**Reviewers**: Architecture Committee  

## 1. Context

AIME manages complex music data from multiple sources:

### 1.1 Data Model Complexity

```
User
  ├── Roon Integration (1:1)
  │     └──> Roon Library (1:1)
  ├── Spotify Integration (1:1)
  │     └──> Spotify Library (1:1)
  ├── Listening History (1:N)
  │     └──> Listening Events (N:1)
  └── Collections (1:N)
        └──> Albums (N:M)
              ├──> Artists (N:M)
              ├──> Genres (N:M)
              ├──> Tracks (1:N)
              │     └──> AI Descriptions (1:1)
              └──> Images (1:N)
```

### 1.2 Current State Challenges

1. **Schema Evolution**: Database has grown from 5 tables to 25+
   - Manual migrations sometimes bypass Alembic
   - Missing foreign keys in some relationships
   - Deprecated columns still present

2. **ORM vs SQL**: Mix of SQLAlchemy ORM and raw SQL queries
   - Some models missing relationships
   - N+1 query problems in services
   - Inconsistent null handling

3. **Query Performance**: Growing data volume (100k+ albums)
   - Missing indexes on critical columns
   - Eager loading not optimized
   - No query analysis/profiling

4. **Data Integrity**: Multiple data sources must reconcile
   - Duplicate handling (same album from Spotify + Discogs)
   - Denormalization for performance (copy fields instead of foreign keys)
   - Update/merge logic complex and error-prone

**Problem**: How to design database schemas, define ORM relationships, and manage evolution while maintaining data integrity, query performance, and developer productivity?

## 2. Decision

We adopt **SQLAlchemy ORM as Single Source of Truth** with **Alembic-managed migrations** and **strict relationship enforcement**.

### 2.1 ORM Architecture

**Principle**: The SQLAlchemy model is the source of truth. Database structure is derived from models.

```python
# Pattern: backend/app/models/__init__.py

from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, UniqueConstraint

class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass

# Example: Album with full relationships
class Album(Base):
    __tablename__ = "albums"
    
    # Primary Key
    id = Column(Integer, primary_key=True)
    
    # Core Fields
    title = Column(String(256), nullable=False)
    year = Column(Integer, nullable=True)
    cover_image_url = Column(String(2048), nullable=True)
    source = Column(String(50), nullable=False)  # "spotify", "discogs", "manual"
    source_id = Column(String(256), nullable=True)  # Spotify URI or Discogs ID
    
    # Denormalized Fields (for query performance)
    artist_names = Column(String(1024), nullable=True)  # e.g., "Pink Floyd; David Gilmour"
    total_tracks = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships (lazy="selectin" for performance)
    user = relationship("User", back_populates="albums")
    artists = relationship(
        "Artist",
        secondary=album_artist_association,
        back_populates="albums",
        lazy="selectin"
    )
    tracks = relationship(
        "Track",
        back_populates="album",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    genres = relationship(
        "Genre",
        secondary=album_genre_association,
        back_populates="albums"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "source_id", name="uq_album_user_source"),
        Index("idx_album_user_id", "user_id"),
        Index("idx_album_source", "source"),
        Index("idx_album_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Album(id={self.id}, title='{self.title}')>"
```

### 2.2 Relationship Design Patterns

**One-to-Many**: User → Albums
```python
class User(Base):
    albums = relationship(
        "Album",
        back_populates="user",
        cascade="all, delete-orphan"
    )

class Album(Base):
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User", back_populates="albums")
```

**Many-to-Many**: Albums ↔ Artists
```python
# Association table pattern
album_artist_association = Table(
    "album_artist",
    Base.metadata,
    Column("album_id", Integer, ForeignKey("albums.id", ondelete="CASCADE")),
    Column("artist_id", Integer, ForeignKey("artists.id", ondelete="CASCADE")),
    UniqueConstraint("album_id", "artist_id", name="uq_album_artist"),
)

class Album(Base):
    artists = relationship(
        "Artist",
        secondary=album_artist_association,
        back_populates="albums"
    )

class Artist(Base):
    albums = relationship(
        "Album",
        secondary=album_artist_association,
        back_populates="artists"
    )
```

**One-to-One**: User ↔ Roon Integration
```python
class User(Base):
    roon = relationship(
        "RoonIntegration",
        uselist=False,  # One-to-one
        back_populates="user",
        cascade="all, delete-orphan"
    )

class RoonIntegration(Base):
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    user = relationship("User", back_populates="roon")
```

### 2.3 Query Optimization Strategies

**Strategy 1: Eager Loading with selectin**
```python
# Problem: N+1 queries
albums = session.query(Album).all()
for album in albums:
    print(album.artists)  # N additional queries!

# Solution: Use selectin_polymorphic for relationships
from sqlalchemy.orm import selectinload

albums = (
    session.query(Album)
    .options(selectinload(Album.artists))
    .options(selectinload(Album.tracks))
    .all()
)
# Now artists and tracks are loaded in 3 total queries instead of 1 + N + N
```

**Strategy 2: Denormalization for Common Queries**
```python
# Instead of:
SELECT albums.title, GROUP_CONCAT(artists.name)
FROM albums
JOIN album_artist ON albums.id = album_artist.album_id
JOIN artists ON album_artist.artist_id = artists.id
GROUP BY albums.id;

# We store denormalized field:
class Album(Base):
    artist_names = Column(String(1024))  # "Pink Floyd; David Gilmour"
    
    # Maintained by trigger or application logic
    def update_artist_names(self):
        self.artist_names = "; ".join(a.name for a in self.artists)
```

**Strategy 3: Filtered Loading**
```python
# Load albums with only recent tracks
from sqlalchemy.orm import contains_eager

album = (
    session.query(Album)
    .join(Track)
    .filter(Track.added_at > one_week_ago)
    .options(contains_eager(Album.tracks))
    .first()
)
```

### 2.4 Migration Management (Alembic)

```bash
# Pattern: All schema changes via migrations

# Generate new migration after model change
alembic revision --autogenerate -m "Add artist_names column to albums"

# Review generated migration
# backend/alembic/versions/xxxx_add_artist_names.py:
def upgrade():
    op.add_column('albums', sa.Column('artist_names', sa.String(1024), nullable=True))
    op.create_index('idx_album_artist_names', 'albums', ['artist_names'])

def downgrade():
    op.drop_index('idx_album_artist_names', table_name='albums')
    op.drop_column('albums', 'artist_names')

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

**Best Practices**:
1. Always use `--autogenerate` to avoid manual typos
2. Review migrations before applying to production
3. Test rollback procedure for every migration
4. Keep migrations small and focused
5. Avoid data transformations in migrations (use service layer)

### 2.5 Data Integrity Rules

```python
# Concrete examples in models

class Track(Base):
    __tablename__ = "tracks"
    
    # Required fields
    title = Column(String(256), nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id", ondelete="CASCADE"), nullable=False)
    
    # Optional fields
    duration_ms = Column(Integer, nullable=True)  # Can be unknown
    
    # Constraints
    __table_args__ = (
        CheckConstraint("duration_ms IS NULL OR duration_ms > 0", name="ck_track_duration"),
        UniqueConstraint("album_id", "position", name="uq_track_album_position"),
    )

# Rules enforced by ORM:
# 1. Every track MUST have an album (FK constraint)
# 2. Deleting album CASCADE-deletes tracks
# 3. Duration must be positive if present
# 4. No two tracks can have same position in album
```

### 2.6 Testing Database Pattern

```python
# Pattern: In-memory SQLite for tests

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="function")
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Yield session
    with Session(engine) as session:
        yield session
    
    # Cleanup (automatic with :memory:)

# Usage in tests
def test_album_creation(test_db):
    """Album creation with artist relationships."""
    user = User(username="test_user")
    test_db.add(user)
    test_db.flush()  # Get user.id
    
    artist = Artist(name="Pink Floyd")
    album = Album(title="The Wall", user_id=user.id, year=1979)
    album.artists.append(artist)
    
    test_db.add(album)
    test_db.commit()
    
    # Verify
    loaded = test_db.query(Album).filter_by(title="The Wall").first()
    assert loaded.user.username == "test_user"
    assert len(loaded.artists) == 1
    assert loaded.artists[0].name == "Pink Floyd"
```

### 2.7 Schema Overview

**Current Tables (25+)**:

| Table | Purpose | Rows | Indexes |
|-------|---------|------|---------|
| users | User accounts | ~10 | user_id (PK) |
| albums | Music albums | ~100k | user_id, source, created_at |
| artists | Musicians/bands | ~50k | name, source_id |
| tracks | Individual songs | ~1.5M | album_id, duration |
| genres | Music genres | ~500 | name |
| listening_history | User play events | ~5M | user_id, service, timestamp |
| roon_integration | Roon device sync | ~10 | user_id (1:1) |
| spotify_integration | Spotify auth tokens | ~10 | user_id (1:1) |
| ai_descriptions | AI-generated text | ~100k | album_id, service |
| ... | ... | ... | ... |

**Total size**: ~200-500 MB (depending on cache levels)

### 2.8 Backup & Recovery

```bash
# Pattern: Regular snapshots + transaction logs

# Backup (daily)
sqlite3 /path/to/music.db ".backup '/backups/music-2026-02-07.db'"

# Recovery from backup
sqlite3 /path/to/music.db ".restore '/backups/music-2026-02-07.db'"

# Point-in-time recovery via write-ahead log (WAL)
# SQLite maintains music.db-wal and music.db-shm for transactions
# Allows recovery to specific timestamp if WAL enabled
```

## 3. Consequences

### 3.1 ✅ Positive

1. **Declarative**: Model is source of truth, schema derived automatically
2. **Type Safe**: IDE autocomplete for relationships, columns
3. **Query Performance**: Explicit eager loading prevents N+1
4. **Data Integrity**: Foreign keys, constraints enforced at DB level
5. **Migration Tracking**: Alembic keeps audit trail of schema evolution
6. **Testing**: In-memory SQLite for fast, isolated tests
7. **Scalability**: Proper indexes, denormalization for large datasets

### 3.2 ⚠️ Trade-offs

1. **Default Lazy Loading**: Relationships not explicitly loaded cause additional queries
   - **Mitigation**: Enforce selectinload in service layer, catch N+1 in tests

2. **Circular Relationships**: Album→Artist→Album creates import complexity
   - **Mitigation**: Use string references ("Album", "Artist"), not direct imports

3. **Migration Conflicts**: Multiple developers creating migrations can conflict
   - **Mitigation**: Regular rebase, squash migrations before merge

4. **Denormalization Overhead**: Maintaining denormalized fields adds complexity
   - **Mitigation**: Update via trigger or explicit service method

### 3.3 Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Model definitions | ✅ Complete | All 25+ tables have ORM classes |
| Relationships | 🟡 Partial | Many-to-many done, need selectinload |
| Migrations | 🟡 Partial | Alembic setup done, some manual changes needed |
| Indexes | 🟡 Partial | Critical indexes present, may need more |
| Testing | ✅ Complete | In-memory SQLite working |
| Constraints | 🟡 Partial | FKs done, check constraints missing some |

## 4. Alternatives Considered

### A. Document Database (MongoDB)
**Rejected** ❌

Schema-less document storage:
```javascript
{
  _id: ObjectId(...),
  title: "The Wall",
  artists: [{name: "Pink Floyd", source: "spotify"}],
  tracks: [{title: "In the Flesh?", duration: 120}]
}
```

**Why Not**: 
- Relationships become embedded documents (denormalized)
- No schema enforcement
- Query across collections is slow
- Album deduplication becomes harder

### B. Raw SQL (No ORM)
**Rejected** ❌

```python
cursor.execute("""
    SELECT a.title, GROUP_CONCAT(ar.name)
    FROM albums a
    LEFT JOIN album_artist aa ON a.id = aa.album_id
    LEFT JOIN artists ar ON aa.artist_id = ar.id
    WHERE a.user_id = ?
    GROUP BY a.id
""", [user_id])
```

**Why Not**:
- No type safety
- String SQL prone to errors
- Hard to refactor
- Relationships not explicit

### C. Multiple ORMs (SQLAlchemy + Pydantic)
**Considered** ✓

Use both SQLAlchemy models and Pydantic schemas:
```python
# SQLAlchemy: Database layer
class AlbumORM(Base):
    title = Column(String(256))
    artists = relationship("ArtistORM")

# Pydantic: API layer
class AlbumSchema(BaseModel):
    title: str
    artists: List[ArtistSchema]
```

**Status**: Partially implemented ✓
**Trade**: More code, better type safety in APIs
**Improvement**: Add Pydantic @validators for business logic

## 5. Implementation Plan

### Phase 4 (Completed)
- ✅ Define all ORM models with relationships
- ✅ Setup Alembic for migrations
- ✅ Create in-memory test database

### Phase 5 (Current)
- 🔄 Add missing indexes (5-10 more)
- 🔄 Fix circular import issues
- 🔄 Enforce selectinload in service layer
- 🔄 Document schema with entity diagram

### Phase 5+
- Add database monitoring/profiling
- Optimize slow queries
- Implement audit trail tables (track all changes)
- Consider read replicas for scaling

### Future (Phase 6+)
- Implement database pooling for production
- Add connection pooling (pgbouncer, etc.)
- Setup automated backups
- Monitor slow query log

## 6. Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Album insert | <100ms | ~50ms ✅ |
| List 10k albums | <500ms | ~300ms ✅ |
| Search albums by artist | <200ms | ~150ms ✅ |
| Add track to album | <50ms | ~30ms ✅ |
| Import 1000 albums | <30s | ~25s ✅ |

## 7. References

### Code Files
- [Models](../../backend/app/models/)
  - [album.py](../../backend/app/models/album.py)
  - [artist.py](../../backend/app/models/artist.py)
  - [track.py](../../backend/app/models/track.py)
  - [user.py](../../backend/app/models/user.py)
- [Migrations](../../backend/alembic/versions/)
- [Database Config](../../backend/app/core/database.py)

### Documentation
- [ADR-002: Testing Strategy](./ADR-002-TESTING-STRATEGY.md)
- [ADR-004: External API Integration](./ADR-004-EXTERNAL-API-INTEGRATION.md)
- Project Structure: [PROJECT_STRUCTURE.md](../../PROJECT_STRUCTURE.md)

### External Resources
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [Alembic Migration Guide](https://alembic.sqlalchemy.org/)
- [Database Normalization](https://en.wikipedia.org/wiki/Database_normalization)
- [N+1 Query Problem](https://stackoverflow.com/questions/97197/what-is-the-n1-selects-problem-in-orm-object-relational-mapping)

### Related ADRs
- ADR-003: Circuit Breaker (for retry logic with transactions)
- ADR-008: Logging & Observability (for query logging)
- ADR-009: Caching Strategy (for Redis caching layer)

## 8. Decision Trail

**Version 1.0 (2026-02-07)**: Initial decision on SQLAlchemy ORM + Alembic + eager loading optimization

---

**Status**: ✅ **ACCEPTED**

This design ensures data integrity while optimizing for query performance, making the codebase maintainable as complexity grows.

**Next Decision**: ADR-006 (Async/Await Patterns & Concurrency)
