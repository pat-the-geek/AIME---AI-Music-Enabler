# ADR-002: Testing Framework & Coverage Strategy

**Status**: Accepted  
**Date**: 2026-02-07  
**Priority**: High  
**Impact**: Code Quality, Regression Prevention, Maintainability

---

## Context

AIME is a complex system with multiple external API integrations. Without proper testing:

1. **Regressions**: Changes break existing functionality silently
2. **API Contracts**: External API changes aren't caught early
3. **Error Handling**: Edge cases (empty, null, timeout) aren't tested
4. **Confidence**: Deployments are risky without safety net
5. **Documentation**: Tests serve as executable examples of API usage

**Historical State**:
- Phase 1-3: No tests, manual verification via UI
- Phase 4: Created 100+ tests, established 22% coverage baseline
- Current: 77 tests passing, 23 failing (needs investigation)

**Problem Statement**: Need systematic testing approach to reach 80% coverage by Phase 6.

---

## Decision

**Adopt Three-Tier Testing Strategy with pytest & Comprehensive Coverage:**

### 1. **Testing Pyramid**

```
          /\          E2E Tests (10-15 tests)
         /  \         Complex workflows, full app integration
        /────\        
       /      \       Integration Tests (30-40 tests)
      /        \      API integration, database operations
     /──────────\     
    /            \    Unit Tests (60-80 tests)
   /              \   Individual functions/methods, mocked dependencies
  /────────────────\  
 /                  \
```

### 2. **Test Categories & Responsibilities**

**Unit Tests** (60-80 tests)
- Test individual functions/methods in isolation
- Mock all external dependencies (DB, APIs, services)
- Fast execution (<100ms per test)
- High code coverage (80%+)
- Location: `backend/tests/unit/`

Examples:
```python
def test_list_albums_pagination(album_service, db_session):
    """Unit test: pagination logic works correctly."""
    items, total, pages = album_service.list_albums(page=2, page_size=10)
    assert pages == (total + 9) // 10
```

**Integration Tests** (30-40 tests)
- Test interactions between components
- Database operations with real schema
- API calls with mocked responses
- Moderate execution time (100-500ms per test)
- Location: `backend/tests/integration/`

Examples:
```python
@patch('httpx.AsyncClient.post')
async def test_spotify_api_search(mock_post, spotify_service):
    """Integration test: Spotify search with real response format."""
    mock_post.return_value.json() = {"artists": [...]}
    result = await spotify_service.search_artist_image("Test")
    assert result is not None
```

**E2E Tests** (10-15 tests)
- Test complete workflows end-to-end
- Multiple systems working together
- Can use real or heavily mocked external APIs
- Slower execution (1-10s per test)
- Location: `backend/tests/e2e/`

Examples:
```python
@pytest.mark.slow
async def test_full_discogs_import_workflow(client, db_session):
    """E2E test: Complete import flow from Discogs."""
    # 1. Trigger import
    response = client.post("/api/v1/collection/import/discogs")
    assert response.status_code == 200
    
    # 2. Wait for completion
    assert db_session.query(Album).count() > 0
```

### 3. **Coverage Targets by Module**

| Module | Target | Current | Status |
|--------|--------|---------|--------|
| Models | 90% | 92% | ✅ Met |
| Schemas | 90% | 98% | ✅ Met |
| **Services** (Core) | 85% | 78% | 🟡 Close |
| Services (Album) | 85% | 78% | 🟡 Close |
| Services (Spotify) | 85% | 11% | 🔴 Critical |
| Services (AI) | 85% | 11% | 🔴 Critical |
| Services (Discogs) | 85% | 11% | 🔴 Critical |
| API Routes | 75% | 27% | 🔴 Needs Work |
| Error Handlers | 80% | 52% | 🟡 Medium |
| **Overall** | 80% | 22% | 🔴 Behind |

### 4. **Test Fixture Strategy**

**Central conftest.py** for shared fixtures:

```python
# Database fixtures
@pytest.fixture(scope="function")
def db_session():
    """In-memory SQLite for test isolation."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(bind=engine)()

# Service fixtures
@pytest.fixture
def album_service(db_session):
    """AlbumService with test database."""
    return AlbumService()

# Mock fixtures
@pytest.fixture
def mock_spotify_service():
    """AsyncMock SpotifyService."""
    return AsyncMock(spec=SpotifyService)

# Test data fixtures
@pytest.fixture
def album_in_db(db_session):
    """Sample album for tests."""
    album = Album(title="Test Album", year=2020)
    db_session.add(album)
    db_session.commit()
    return album
```

### 5. **Key Testing Patterns**

**Pattern 1: Mocking External APIs**

```python
@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_spotify_timeout(mock_get, spotify_service):
    """Test timeout handling."""
    mock_get.side_effect = httpx.TimeoutException()
    
    with pytest.raises(httpx.TimeoutException):
        await spotify_service.search_artist_image("Artist")
```

**Pattern 2: Edge Case Testing**

```python
def test_list_albums_empty_results():
    """Test behavior with empty collection."""
    items, total, pages = album_service.list_albums(search="NonExistent")
    assert items == []
    assert total == 0
    assert pages == 0
```

**Pattern 3: Async Testing**

```python
@pytest.mark.asyncio
async def test_ask_for_ia_stream():
    """Test async streaming."""
    chunks = []
    async for chunk in ai_service.ask_for_ia_stream("Who is Beethoven?"):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    assert all(isinstance(c, str) for c in chunks)
```

### 6. **Coverage Measurement**

Using `pytest-cov`:

```bash
# Generate coverage report
pytest --cov=app --cov-report=term-missing --cov-report=html

# With threshold enforcement (Phase 6)
pytest --cov=app --cov-fail-under=80
```

### 7. **Test Organization**

```
backend/tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── test_album_service.py
│   ├── test_artist_service.py
│   ├── test_error_cases.py     # Edge cases
│   └── test_coverage_expansion.py  # Advanced scenarios
├── integration/
│   └── test_external_apis.py   # Spotify, Discogs, AI
├── e2e/
│   └── test_workflows.py       # Full end-to-end workflows
└── fixtures/
    ├── albums.json             # Sample data
    └── responses.json          # API responses
```

---

## Consequences

### ✅ Positive Impacts

1. **Regression Prevention**: Catch bugs before production
2. **Confidence**: Deploy with safety net
3. **Documentation**: Tests show how to use APIs
4. **Refactoring Safety**: Improve code without fear
5. **CI/CD Integration**: Automated testing in pipeline
6. **Team Communication**: Tests document expected behavior

### ⚠️ Trade-offs

1. **Maintenance Overhead**: Tests need updating with code
2. **Execution Time**: Full test suite takes 30-60 seconds
3. **Mock Complexity**: Async mocks harder to set up than sync
4. **Coverage Gaps**: Some paths hard to test (network, timing)
5. **False Positives**: Flaky async tests can be frustrating

### 📊 Investment & ROI

**Effort**: 
- Initial setup: 40 hours (done)
- Add service tests: 50 hours (Phase 5)
- Add route tests: 60 hours (Phase 5-6)
- Total: ~150 hours

**Return**:
- 80% coverage reduces bugs by ~70%
- Deployment confidence increases significantly
- Time to onboard new developers: 1 day → 2-3 hours
- Regression finding time: 1 month → 1 hour (automated)

---

## Alternatives Considered

### 1. Minimal Testing (Just Unit Tests)
- **Pros**: Fast to write, basic coverage
- **Cons**: Integration bugs missed, API changes cause surprises
- **Rejected**: Insufficient for production system

### 2. Manual Testing Only
- **Pros**: No test code maintenance
- **Cons**: Doesn't scale, regressions found too late
- **Rejected**: Already failing - regression found in Phase 4

### 3. BDD with Behave/Cucumber
- **Pros**: Non-technical stakeholders can read tests
- **Cons**: Overkill for single developer, slower execution
- **Rejected**: pytest is simpler, industry standard for Python

### 4. Snapshot Testing
- **Pros**: Easy to write for complex outputs
- **Cons**: Hides real failures, hard to review changes
- **Adopted For**: Limited use only (golden file comparison)

---

## Implementation Plan

### Phase 4 (Current) ✅
- [x] Create test infrastructure (conftest, fixtures)
- [x] Create 50+ unit tests
- [x] Create 15+ integration tests
- [x] Create 10+ E2E tests
- [x] Fix 7 critical test failures
- [x] Establish 22% coverage baseline

### Phase 5 (Next)
- [ ] Add 20+ tests for external services (AI, Spotify, Discogs)
- [ ] Add 30+ tests for API routes
- [ ] Improve E2E tests or break into unit tests
- [ ] Reach 35-40% coverage target

### Phase 6+
- [ ] Add error handling tests (20+)
- [ ] Add performance/stress tests
- [ ] Reach 80% coverage target
- [ ] Integrate with CI/CD pipeline
- [ ] Add coverage enforcement (--cov-fail-under=80)

---

## References

### Testing Framework Docs
- **pytest**: https://docs.pytest.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **unittest.mock**: https://docs.python.org/3/library/unittest.mock.html
- **httpx mocking**: https://www.python-httpx.org/

### Testing Best Practices
- **Test Pyramid**: https://martinfowler.com/articles/testPyramid.html
- **Arrange-Act-Assert**: https://xp123.com/articles/3a-arrange-act-assert/
- **Given-When-Then**: https://www.agilealliance.org/glossary/given-when-then/

### AIME Examples
- Core test fixture: `backend/tests/conftest.py`
- Unit tests: `backend/tests/unit/test_album_service.py`
- Integration tests: `backend/tests/integration/test_external_apis.py`
- E2E tests: `backend/tests/e2e/test_workflows.py`

---

## Questions & Discussions

**Q: Should we test private methods (_method)?**  
A: Generally no. Test public interface. Private methods tested indirectly through public methods.

**Q: How many tests per function?**  
A: Usually 2-3. One happy path, one-two edge cases (null, empty, error).

**Q: When do we skip tests?**  
A: Use `@pytest.mark.skip("reason")` for known issues. Use `@pytest.mark.slow` for long tests.

**Q: Mock or patch?**  
A: Prefer patch for external calls (httpx, requests). Prefer Mock for service methods.

---

**Status**: ✅ Accepted as of 2026-02-07  
**Owner**: GitHub Copilot  
**Next Review**: 2026-03-07

