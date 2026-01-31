"""Configuration du backend avec Pydantic Settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache
import json
import os
from pathlib import Path


class Settings(BaseSettings):
    """Configuration de l'application."""
    
    # Chemins
    @property
    def project_root(self) -> Path:
        """Racine du projet - utilise PROJECT_ROOT env var ou calcule depuis __file__."""
        if "PROJECT_ROOT" in os.environ:
            return Path(os.environ["PROJECT_ROOT"])
        return Path(__file__).parent.parent.parent.parent
    
    @property
    def config_dir(self) -> Path:
        return self.project_root / "config"
    
    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"
    
    # Application
    app_name: str = "AIME - AI Music Enabler"
    app_version: str = "4.0.0"
    environment: str = "development"
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]
    
    # Database - utilise un chemin absolu construit depuis PROJECT_ROOT
    @property
    def database_url(self) -> str:
        """URL de la base de données avec chemin absolu."""
        db_path = self.data_dir / "musique.db"
        return f"sqlite:///{db_path}"
    
    database_echo: bool = False
    
    # Tracker
    tracker_enabled: bool = True
    tracker_interval: int = 120
    listen_start_hour: int = 6
    listen_end_hour: int = 23
    
    # Cache pour les configurations chargées
    _app_config_cache: dict = None
    _secrets_cache: dict = None
    
    def load_config_file(self, filename: str) -> dict:
        """Charger un fichier de configuration JSON."""
        config_path = self.config_dir / filename
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_config_file(self, filename: str, data: dict) -> None:
        """Sauvegarder un fichier de configuration JSON."""
        config_path = self.config_dir / filename
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @property
    def app_config(self) -> dict:
        """Configuration de l'application depuis app.json (avec cache)."""
        if self._app_config_cache is None:
            self._app_config_cache = self.load_config_file("app.json")
        return self._app_config_cache
    
    def save_app_config(self) -> None:
        """Sauvegarder app_config dans app.json."""
        self.save_config_file("app.json", self._app_config_cache)
    
    @property
    def secrets(self) -> dict:
        """Secrets depuis secrets.json (avec cache)."""
        if self._secrets_cache is None:
            self._secrets_cache = self.load_config_file("secrets.json")
        return self._secrets_cache
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Obtenir l'instance des settings (singleton)."""
    return Settings()
