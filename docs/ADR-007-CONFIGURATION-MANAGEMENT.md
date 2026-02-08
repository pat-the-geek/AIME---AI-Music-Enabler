# ADR-007: Configuration Management

**Status**: ✅ Accepted  
**Date**: 2026-02-07  
**Priority**: High  
**Author**: Engineering Team  
**Reviewers**: Architecture Committee  

## 1. Context

AIME requires configuration for many settings across environments:

### 1.1 Configuration Needs

**Environment-Specific**:
- Database URL (dev: SQLite, prod: PostgreSQL)
- API endpoints (dev: localhost, prod: cloud.provider.com)
- Log levels (dev: DEBUG, prod: WARNING)
- Cache TTL (dev: 5 min, prod: 1 hour)

**Secrets** (never in code):
- Spotify OAuth client secret
- Discogs API key
- Database password
- JWT signing key
- API tokens for EurIA service

**Feature Flags** (control behavior without redeployment):
- Enable/disable Roon integration
- Enable beta AI features
- Toggle maintenance mode

**Performance Tuning**:
- Database connection pool size
- Rate limit delays (per service)
- Import batch sizes
- Cache sizes

### 1.2 Current Challenges

1. **Multiple Config Sources**
   - Environment variables: `DB_URL`, `SPOTIFY_CLIENT_ID`
   - Config files: `config/app.json`, `config/enrichment_config.json`
   - Hardcoded defaults scattered in code
   - No single source of truth

2. **Secret Exposure Risk**
   - API keys in config files (sometimes committed by accident)
   - Secrets.json in gitignore but easy to forget
   - No encryption at rest
   - Difficult to rotate keys

3. **Type Safety**
   - Settings loaded as strings, cast Ad hoc in code
   - No validation of required fields
   - Unit tests can't easily override config

4. **Dynamic Updates**
   - Feature flags require server restart
   - Rate limits can't be adjusted without redeployment
   - Maintenance mode requires code change

**Problem**: How to manage configuration consistently, securely, typesafe, and dynamically across environments?

## 2. Decision

We adopt **Pydantic BaseSettings for configuration** with **layered config sources** (environment vars > secrets file > defaults).

### 2.1 Configuration Architecture

```python
# Pattern: backend/app/core/config.py

from pydantic import BaseSettings, Field, validator
from typing import Optional, Dict, Any
import json
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings loaded from environment and config files.
    
    Priority: 
    1. Environment variables (NODE_ENV, DATABASE_URL, etc.)
    2. .env file (development)
    3. Secrets file (config/secrets.json)
    4. Defaults (in class definition)
    
    Usage:
        settings = get_settings()
        db_url = settings.database_url
    """
    
    # ============ Core Application ============
    app_name: str = Field(default="AIME", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # ============ Server ============
    host: str = Field(default="0.0.0.0", description="Server listen address")
    port: int = Field(default=8000, description="Server listen port")
    reload: bool = Field(default=True, description="Auto-reload on code change")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # ============ Database ============
    database_url: str = Field(
        default="sqlite:///./app.db",
        description="Database URL (SQLite for dev, PostgreSQL for prod)"
    )
    database_pool_size: int = Field(default=5, description="DB connection pool size")
    database_pool_recycle: int = Field(default=3600, description="Recycle connections after N seconds")
    
    # ============ Authentication ============
    jwt_secret: str = Field(
        default="change-me-in-production",
        description="JWT signing secret (CHANGE IN PRODUCTION!)"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT token lifetime")
    
    # ============ Spotify Integration ============
    spotify_enabled: bool = Field(default=True, description="Enable Spotify integration")
    spotify_client_id: str = Field(
        default="",
        description="Spotify OAuth client ID"
    )
    spotify_client_secret: str = Field(
        default="",
        description="Spotify OAuth client secret (SECRET!)"
    )
    spotify_redirect_uri: str = Field(
        default="http://localhost:3000/auth/spotify/callback",
        description="Spotify OAuth redirect URL"
    )
    
    # ============ Discogs Integration ============
    discogs_enabled: bool = Field(default=True, description="Enable Discogs integration")
    discogs_api_key: str = Field(
        default="",
        description="Discogs API key (optional, for higher rate limits)"
    )
    discogs_username: str = Field(
        default="",
        description="Discogs username (for collection access)"
    )
    discogs_rate_limit_delay: float = Field(
        default=0.5,
        description="Minimum seconds between Discogs requests"
    )
    
    # ============ EurIA/AI Integration ============
    euria_enabled: bool = Field(default=True, description="Enable AI descriptions")
    euria_endpoint: str = Field(
        default="http://localhost:5000/api/describe",
        description="EurIA service endpoint"
    )
    euria_timeout: int = Field(default=120, description="AI generation timeout (seconds)")
    euria_batch_size: int = Field(default=10, description="Batch size for AI requests")
    
    # ============ Roon Integration ============
    roon_enabled: bool = Field(default=False, description="Enable Roon integration")
    roon_core_ip: str = Field(
        default="",
        description="Roon Core IP address"
    )
    roon_token: str = Field(
        default="",
        description="Roon API token (SECRET!)"
    )
    
    # ============ Caching ============
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_type: str = Field(
        default="memory",
        description="Cache backend: memory, redis"
    )
    cache_redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL (if cache_type=redis)"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        description="Default cache TTL"
    )
    cache_max_size_mb: int = Field(
        default=100,
        description="Max memory for in-memory cache"
    )
    
    # ============ Feature Flags ============
    feature_advanced_search: bool = Field(
        default=False,
        description="Enable advanced multi-source search"
    )
    feature_smart_collections: bool = Field(
        default=False,
        description="Enable AI-powered collection organization"
    )
    feature_export_magazine: bool = Field(
        default=True,
        description="Enable magazine export feature"
    )
    
    # ============ Rate Limiting ============
    rate_limit_enabled: bool = Field(default=True, description="Enable API rate limiting")
    rate_limit_requests: int = Field(
        default=60,
        description="API rate limit: requests per minute"
    )
    rate_limit_per_user: int = Field(
        default=100,
        description="Rate limit per authenticated user (requests/minute)"
    )
    
    # ============ Logging ============
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    log_file: str = Field(
        default="logs/aime.log",
        description="Log file path"
    )
    log_file_max_bytes: int = Field(
        default=10485760,  # 10MB
        description="Max log file size before rotation"
    )
    log_file_backup_count: int = Field(
        default=5,
        description="Number of rotated log files to keep"
    )
    
    # ============ Performance Tuning ============
    max_concurrent_imports: int = Field(
        default=10,
        description="Max concurrent import jobs"
    )
    import_batch_size: int = Field(
        default=100,
        description="Batch size for database inserts during import"
    )
    search_timeout_seconds: int = Field(
        default=30,
        description="Search operation timeout"
    )
    
    # ============ CORS & Security ============
    cors_origins: list = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS"
    )
    
    # ============ Validators ============
    
    @validator("environment")
    def validate_environment(cls, v):
        """Ensure environment is valid."""
        if v not in ["development", "staging", "production"]:
            raise ValueError("environment must be development|staging|production")
        return v
    
    @validator("cache_type")
    def validate_cache_type(cls, v):
        """Ensure cache type is supported."""
        if v not in ["memory", "redis"]:
            raise ValueError("cache_type must be memory|redis")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Ensure log level is valid."""
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log level")
        return v
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"  # Load from .env if exists
        env_file_encoding = "utf-8"
        case_sensitive = False

# Singleton instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """
    Get application settings (lazy-loaded singleton).
    
    Returns:
        Settings: Application configuration
        
    Note:
        First call loads and validates all settings.
        Subsequent calls return cached instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# For FastAPI dependency injection
def get_settings_as_dependency() -> Settings:
    """FastAPI dependency for injecting settings."""
    return get_settings()
```

### 2.2 Secrets Management

```python
# Pattern: backend/app/core/secrets.py

from pathlib import Path
import json
from typing import Dict, Any, Optional
from .config import get_settings

class SecretsManager:
    """
    Load secrets from encrypted/gitignore'd files.
    
    Priority:
    1. Environment variables (for production)
    2. config/secrets.json (for development)
    3. Default empty string
    """
    
    def __init__(self, secrets_file: str = "config/secrets.json"):
        self.secrets_file = Path(secrets_file)
        self._secrets: Dict[str, Any] = {}
        self._load_secrets()
    
    def _load_secrets(self) -> None:
        """Load secrets from file if exists."""
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, "r") as f:
                    self._secrets = json.load(f)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in {self.secrets_file}")
        else:
            # File not found okay (use env vars instead)
            pass
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get secret value from file or environment.
        
        Priority:
        1. Environment variable (uppercase key)
        2. Secrets file (exact key)
        3. Default value
        4. Empty string
        """
        # Try environment variable first
        import os
        env_value = os.getenv(key.upper())
        if env_value:
            return env_value
        
        # Try secrets file
        if key in self._secrets:
            return self._secrets[key]
        
        # Use default or empty
        return default or ""

# Usage in config loading
def load_secrets_into_settings(settings: Settings) -> Settings:
    """
    Enhance settings with secrets from file/env.
    
    Overrides settings defaults with actual secrets.
    """
    manager = SecretsManager()
    
    # Spotify
    settings.spotify_client_secret = manager.get("SPOTIFY_CLIENT_SECRET")
    
    # Discogs
    settings.discogs_api_key = manager.get("DISCOGS_API_KEY")
    
    # JWT
    settings.jwt_secret = manager.get("JWT_SECRET", settings.jwt_secret)
    
    # Roon
    settings.roon_token = manager.get("ROON_TOKEN")
    
    return settings
```

### 2.3 Environment-Specific Configs

**Development** (.env):
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./dev.db
SPOTIFY_CLIENT_ID=dev-client-id
CACHE_TTL_SECONDS=300
FEATURE_ADVANCED_SEARCH=false
```

**Staging** (environment variables):
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@staging-db.example.com/aime
SPOTIFY_CLIENT_ID=staging-client-id
CACHE_TTL_SECONDS=1800
FEATURE_ADVANCED_SEARCH=true
```

**Production** (secure environment):
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:secure_pass@prod-db.aws.com/aime_prod
SPOTIFY_CLIENT_ID=prod-client-id
CACHE_TTL_SECONDS=3600
JWT_SECRET=long-random-secret-key-here
FEATURE_ADVANCED_SEARCH=true
```

### 2.4 Feature Flags Implementation

```python
# Pattern: Feature flags for gradual rollouts

class FeatureFlags:
    """Dynamic feature flag management."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._overrides: Dict[str, bool] = {}
    
    def is_enabled(self, feature_name: str) -> bool:
        """
        Check if feature is enabled.
        
        Priority:
        1. Temporary override (for A/B testing)
        2. Config setting (for feature flags)
        3. Default (false)
        """
        # Check temporary override (expires after session)
        if feature_name in self._overrides:
            return self._overrides[feature_name]
        
        # Check settings
        attr_name = f"feature_{feature_name.lower()}"
        if hasattr(self.settings, attr_name):
            return getattr(self.settings, attr_name)
        
        return False
    
    def set_override(self, feature_name: str, enabled: bool) -> None:
        """
        Temporarily override feature flag (for this session only).
        
        Useful for A/B testing without redeployment.
        """
        self._overrides[feature_name] = enabled
    
    # Convenience methods
    def advanced_search(self) -> bool:
        """Smart search across multiple sources."""
        return self.is_enabled("advanced_search")
    
    def smart_collections(self) -> bool:
        """AI-powered collection organization."""
        return self.is_enabled("smart_collections")
    
    def export_magazine(self) -> bool:
        """Magazine export feature."""
        return self.is_enabled("export_magazine")

# Usage in routes
from fastapi import FastAPI, Depends

app = FastAPI()
settings = get_settings()
features = FeatureFlags(settings)

@app.get("/search")
async def search(query: str):
    """Search endpoint (conditionally enables advanced search)."""
    if features.advanced_search():
        return advanced_search_implementation(query)
    else:
        return basic_search_implementation(query)

# Or inject as dependency
def get_features() -> FeatureFlags:
    return FeatureFlags(get_settings())

@app.get("/collections/smart")
async def smart_collections(
    features: FeatureFlags = Depends(get_features)
):
    """Smart collections only if enabled."""
    if not features.smart_collections():
        raise HTTPException(status_code=404, detail="Feature not available")
    return smartly_organize_collections()
```

### 2.5 Testing with Config Overrides

```python
# Pattern: Override config in tests

import pytest
from app.core.config import Settings, get_settings

@pytest.fixture
def test_settings() -> Settings:
    """
    Create test configuration with safe defaults.
    
    All external services disabled to prevent accidental API calls.
    """
    return Settings(
        environment="testing",
        debug=False,
        database_url="sqlite:///:memory:",
        spotify_enabled=False,
        discogs_enabled=False,
        euria_enabled=False,
        roon_enabled=False,
        cache_enabled=False,
        log_level="WARNING",
    )

@pytest.fixture
def app_with_test_config(test_settings):
    """FastAPI app configured for testing."""
    # Monkey-patch global settings
    import app.core.config as config_module
    original_settings = config_module._settings
    config_module._settings = test_settings
    
    from app.main import app
    
    yield app
    
    # Restore original
    config_module._settings = original_settings

# Using in tests
@pytest.mark.asyncio
async def test_spotify_disabled(app_with_test_config):
    """When Spotify disabled, search skips it."""
    from fastapi.testclient import TestClient
    
    client = TestClient(app_with_test_config)
    response = client.get("/search?query=test")
    
    # Should succeed but not include Spotify results
    assert response.status_code == 200
    data = response.json()
    assert "spotify" not in data or data["spotify"] == {}
```

### 2.6 Configuration Validation at Startup

```python
# Pattern: Validate critical config at app startup

from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate configuration on startup."""
    settings = get_settings()
    
    errors = []
    
    # Production checks
    if settings.is_production():
        if settings.jwt_secret == "change-me-in-production":
            errors.append("❌ JWT_SECRET not set! Security risk!")
        
        if settings.debug:
            errors.append("❌ DEBUG=true in production!")
        
        if not settings.spotify_client_secret:
            errors.append("⚠️ SPOTIFY_CLIENT_SECRET not configured")
        
        if settings.database_url.startswith("sqlite://"):
            errors.append("❌ SQLite database in production! Use PostgreSQL")
    
    # Development checks
    if settings.is_development():
        if not settings.spotify_client_id:
            logger.warning("⚠️ Spotify not configured (set SPOTIFY_CLIENT_ID)")
    
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error("  " + error)
        if settings.is_production():
            raise RuntimeError("Invalid configuration for production")
    else:
        logger.info("✅ Configuration validated successfully")
    
    yield  # App runs here

app = FastAPI(lifespan=lifespan)
```

## 3. Consequences

### 3.1 ✅ Positive

1. **Type Safety**: Pydantic validates all settings
2. **Flexibility**: Environment-specific configs without code changes
3. **Security**: Secrets separated from code, never logged
4. **Testability**: Easy to override settings in tests
5. **Documentation**: All config options self-documenting
6. **Feature Toggles**: Enable/disable features without redeployment

### 3.2 ⚠️ Trade-offs

1. **Complexity**: More code for typed config vs simple dict
   - **Mitigation**: Clear patterns, simple API

2. **Startup Overhead**: Config validation at startup
   - **Mitigation**: Fast (<100ms), happens once

3. **Secrets File Required**: Must maintain secrets.json for dev
   - **Mitigation**: .gitignore prevents accidents, template provided

4. **Environment Variable Naming**: Convention-based (UPPERCASE_WITH_UNDERSCORES)
   - **Mitigation**: Clear documentation in code

### 3.3 Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| BaseSettings class | ✅ Done | Pydantic config schema complete |
| Secrets loading | ✅ Done | secrets.json and env vars supported |
| Feature flags | 🟡 Partial | Basic structure, needs integration |
| Config docs | 🟡 Partial | Inline docstrings done, guide needed |
| Startup validation | ✅ Done | Production safety checks in place |
| Test overrides | ✅ Done | Test fixtures with safe defaults |

## 4. Alternatives Considered

### A. Using Environment Variables Only
**Rejected** ❌

```bash
export DB_URL="postgresql://..."
export SPOTIFY_CLIENT_ID="..."
export SPOTIFY_CLIENT_SECRET="..."
```

**Why Not**:
- Difficult to track all variables
- Easy to forget required vars
- No type validation
- No documentation

### B. YAML Configuration Files
**Considered** ✓

```yaml
# config.yaml
database:
  url: postgresql://...
  pool_size: 10
spotify:
  client_id: ...
```

**Status**: Rejected (overengineering) ✗
**Reason**: Pydantic handles validation better, env vars standard in Docker/Kubernetes

### C. Central Config Server (Consul, Spring Cloud)
**Considered for Future** ⏳

External service manages all configs

**Status**: Not adopted yet
**Use Case**: Large scale, multiple deployments, real-time config updates
**When**: If AIME scales to fleet of services

### D. No Explicit Configuration
**Rejected** ❌

Hard-code all settings, environment detection via `if os.environ.get("ENV") == "prod"`

**Why Not**: 
- No validation
- Easy to miss configs
- Security risk with secrets

## 5. Implementation Plan

### Phase 4 (Completed)
- ✅ Pydantic Settings class created
- ✅ Environment variables supported
- ✅ Secrets file pattern established
- ✅ Test fixtures with overrides

### Phase 5 (Current)
- 🔄 Document configuration guide (this ADR)
- 🔄 Implement feature flags fully
- 🔄 Add startup validation checks
- 🔄 Create configuration templates

### Phase 5+
- Add configuration UI/dashboard
- Implement hot-reload for flags
- Add audit logging for config changes
- Setup secrets rotation

## 6. Configuration Reference

### Essential Environment Variables

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| ENVIRONMENT | ✅ | `production` | deployment context |
| LOG_LEVEL | ✅ | `INFO` | Logging verbosity |
| DATABASE_URL | ✅ | `postgresql://...` | Database connection |
| JWT_SECRET | ✅ | (random 32+ chars) | Auth token signing |
| SPOTIFY_CLIENT_ID | ✅ | `abc123...` | Spotify OAuth |
| SPOTIFY_CLIENT_SECRET | ✅ | (secret key) | Spotify OAuth |

### Optional Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| DEBUG | `false` | Debug mode enable |
| PORT | `8000` | Server port |
| CORS_ORIGINS | localhost | Allowed CORS origins |
| CACHE_TTL_SECONDS | `3600` | Cache lifetime |
| ROON_CORE_IP | (none) | Roon device IP |

## 7. References

### Code Files
- [Config module](../../backend/app/core/config.py)
- [Secrets manager](../../backend/app/core/secrets.py)
- [Environment file](../../backend/.env.example)

### Documentation
- [ADR-002: Testing Strategy](./ADR-002-TESTING-STRATEGY.md)
- [ADR-003: Circuit Breaker](./ADR-003-CIRCUIT-BREAKER.md)

### External Resources
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Environment Variables](https://12factor.net/config)
- [Feature Flags Guide](https://martinfowler.com/articles/feature-toggles.html)

### Related ADRs
- ADR-002: Testing Strategy (test config)
- ADR-008: Logging & Observability (log config)
- ADR-009: Caching Strategy (cache config)

## 8. Decision Trail

**Version 1.0 (2026-02-07)**: Initial decision on Pydantic-based config with env/file layering

---

**Status**: ✅ **ACCEPTED**

This approach provides flexibility for multi-environment deployments while maintaining type safety and security best practices.

**Next Decision**: ADR-008 (Logging & Observability)
