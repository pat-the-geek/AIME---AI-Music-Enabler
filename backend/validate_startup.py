#!/usr/bin/env python3
"""
Script de validation robuste du démarrage de l'application AIME
Vérifie tous les prérequis avant le lancement
"""

import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_python_version():
    """Vérifier la version de Python."""
    required_version = (3, 10)
    if sys.version_info < required_version:
        logger.error(f"❌ Python {required_version[0]}.{required_version[1]}+ required, got {sys.version_info[0]}.{sys.version_info[1]}")
        return False
    logger.info(f"✅ Python {sys.version_info[0]}.{sys.version_info[1]} OK")
    return True


def check_directories():
    """Vérifier et créer les répertoires nécessaires."""
    dirs_to_check = [
        ("data", "Data directory"),
        ("config", "Config directory"),
        ("backend", "Backend directory"),
        ("frontend", "Frontend directory"),
    ]
    
    project_root = Path(__file__).parent.parent
    
    for dir_name, description in dirs_to_check:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            logger.error(f"❌ {description} not found: {dir_path}")
            return False
        
        if dir_name in ["data", "config"]:
            # Vérifier les permissions d'écriture
            if not os.access(dir_path, os.W_OK):
                logger.error(f"❌ No write permission for {description}: {dir_path}")
                return False
        
        logger.info(f"✅ {description} OK: {dir_path}")
    
    # Créer les répertoires s'ils n'existent pas
    (project_root / "data").mkdir(exist_ok=True)
    (project_root / "config").mkdir(exist_ok=True)
    
    return True


def check_dependencies():
    """Vérifier les dépendances Python."""
    required_modules = [
        "fastapi",
        "sqlalchemy",
        "uvicorn",
        "pydantic",
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✅ {module} installed")
        except ImportError:
            logger.error(f"❌ {module} not installed")
            return False
    
    return True


def check_database_config():
    """Vérifier la configuration de la base de données."""
    try:
        from app.core.config import get_settings
        from app.database import engine
        from sqlalchemy import text
        
        settings = get_settings()
        logger.info(f"✅ Database URL configured: {settings.database_url}")
        
        # Tester la connexion
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        
        logger.info("✅ Database connection OK")
        return True
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False


def check_imports():
    """Vérifier que tous les modules critiques peuvent être importés."""
    critical_modules = [
        "app.main",
        "app.database",
        "app.core.config",
        "app.services.health_monitor",
        "app.api.v1.collection",
    ]
    
    for module_path in critical_modules:
        try:
            __import__(module_path)
            logger.info(f"✅ {module_path} imported")
        except Exception as e:
            logger.error(f"❌ Failed to import {module_path}: {e}")
            return False
    
    return True


def main():
    """Exécuter toutes les vérifications."""
    logger.info("=" * 60)
    logger.info("AIME - Application Startup Validation")
    logger.info("=" * 60)
    
    checks = [
        ("Python version", check_python_version),
        ("Directories", check_directories),
        ("Python dependencies", check_dependencies),
        ("Database configuration", check_database_config),
        ("Module imports", check_imports),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        logger.info(f"\nRunning: {check_name}...")
        try:
            if not check_func():
                all_passed = False
                logger.error(f"❌ {check_name} check failed")
        except Exception as e:
            all_passed = False
            logger.error(f"❌ {check_name} check failed with exception: {e}", exc_info=True)
    
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("✅ All validation checks passed!")
        logger.info("Application is ready to start")
        return 0
    else:
        logger.error("❌ Some validation checks failed!")
        logger.error("Fix the issues above and try again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
