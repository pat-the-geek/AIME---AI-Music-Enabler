# 🔧 Guide de Dépannage - AIME - AI Music Enabler

Ce document liste tous les problèmes rencontrés lors de l'installation et du démarrage de AIME - AI Music Enabler, ainsi que leurs solutions.

## 📋 Table des matières

1. [Problèmes de compatibilité Python](#problèmes-de-compatibilité-python)
2. [Erreurs de base de données](#erreurs-de-base-de-données)
3. [Problèmes de configuration](#problèmes-de-configuration)
4. [Problèmes de développement](#problèmes-de-développement)

---

## Problèmes de compatibilité Python

### ❌ Problème 1: Python 3.14 incompatible avec SQLAlchemy

**Symptômes:**
```
AttributeError: type object 'TypingOnly' has no attribute '__mro_entries__'
ModuleNotFoundError: No module named 'sqlalchemy.orm.decl_base'
```

**Cause:**
Python 3.14.1 est trop récent et SQLAlchemy 2.0.25 (version stable) ne le supporte pas encore. La classe `TypingOnly` a changé dans Python 3.14.

**Solution:**
Installer la version de développement de SQLAlchemy qui supporte Python 3.14:

```bash
cd backend
source .venv/bin/activate
pip uninstall -y sqlalchemy
pip install git+https://github.com/sqlalchemy/sqlalchemy.git@main
```

**Version installée:** SQLAlchemy 2.1.0b2.dev0

**Alternative:**
Si possible, utiliser Python 3.10, 3.11 ou 3.12 avec SQLAlchemy stable:
```bash
# Installer Python 3.12
brew install python@3.12

# Recréer l'environnement virtuel
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Erreurs de base de données

### ❌ Problème 2: Conflit avec le nom d'attribut `metadata`

**Symptômes:**
```python
ArgumentError: Attribute name 'metadata' is reserved when using the Declarative API
```

**Cause:**
Dans `backend/app/models/album.py`, la relation était nommée `metadata`, ce qui est un attribut réservé par SQLAlchemy pour gérer les métadonnées de la table.

**Solution appliquée:**
Renommer la relation dans `backend/app/models/album.py`:

```python
# ❌ Avant
metadata = relationship("Metadata", back_populates="album", ...)

# ✅ Après
album_metadata = relationship("Metadata", back_populates="album", ...)
```

**Fichiers modifiés:**
- `backend/app/models/album.py` (ligne 27)
- Tous les fichiers référençant `album.metadata` doivent être mis à jour en `album.album_metadata`

---

### ❌ Problème 3: Import ForeignKey manquant

**Symptômes:**
```python
NameError: name 'ForeignKey' is not defined
```

**Cause:**
Dans `backend/app/models/playlist.py`, l'import de `ForeignKey` était manquant dans la ligne d'imports SQLAlchemy.

**Solution appliquée:**
Ajouter `ForeignKey` aux imports dans `backend/app/models/playlist.py`:

```python
# ❌ Avant
from sqlalchemy import Column, Integer, String, Text, DateTime

# ✅ Après
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
```

---

### ❌ Problème 4: Chemin de base de données incorrect

**Symptômes:**
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file
```

**Cause:**
Le calcul du chemin de la base de données dans `backend/app/core/config.py` utilisait `Path(__file__).parent.parent.parent`, ce qui ne fonctionnait pas correctement lorsque l'application était lancée depuis différents répertoires.

**Solution appliquée:**

1. **Modification de config.py** pour utiliser une variable d'environnement:
```python
# backend/app/core/config.py

@property
def project_root(self) -> Path:
    """Racine du projet - utilise PROJECT_ROOT env var ou calcule depuis __file__."""
    if "PROJECT_ROOT" in os.environ:
        return Path(os.environ["PROJECT_ROOT"])
    return Path(__file__).parent.parent.parent.parent

@property
def database_url(self) -> str:
    """URL de la base de données avec chemin absolu."""
    db_path = self.data_dir / "musique.db"
    return f"sqlite:///{db_path}"
```

2. **Modification du script de démarrage** pour définir PROJECT_ROOT:
```bash
# scripts/start-dev.sh

# Démarrer le backend
echo -e "${BLUE}🚀 Démarrage Backend (Port 8000)...${NC}"
export PROJECT_ROOT="$(pwd)"  # ← Ajout de cette ligne
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000 &
```

3. **Ajout de logique de création de répertoire** dans database.py:
```python
def init_db():
    """Initialiser la base de données (créer les tables)."""
    import os
    from pathlib import Path
    
    # Créer le répertoire de données si nécessaire
    db_url = str(settings.database_url)
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
```

**Vérification:**
```bash
# Créer le répertoire data manuellement si besoin
mkdir -p data

# Vérifier que la base est créée
ls -lh data/musique.db
```

---

## Problèmes de configuration

### ❌ Problème 5: Fichier .env manquant

**Symptômes:**
L'application démarre mais les services externes (Last.fm, Spotify, etc.) ne fonctionnent pas.

**Cause:**
Le fichier `.env` contenant les clés API n'existe pas ou est mal configuré.

**Solution:**
Créer un fichier `.env` à la racine du projet:

```bash
# .env

# Last.fm API
LASTFM_API_KEY=votre_clé_api
LASTFM_API_SECRET=votre_secret
LASTFM_USERNAME=votre_username

# Spotify API
SPOTIFY_CLIENT_ID=votre_client_id
SPOTIFY_CLIENT_SECRET=votre_client_secret

# Discogs API
DISCOGS_TOKEN=votre_token

# EurIA / Infomaniak AI
EURIA_API_KEY=votre_clé_api
EURIA_API_URL=https://api.infomaniak.com/1/ai
```

**Alternative:**
Les configurations peuvent aussi être placées dans `config/*.json` selon l'architecture du projet.

---

## Problèmes de développement

### ❌ Problème 6: Reloads infinis d'Uvicorn

**Symptômes:**
Le serveur backend redémarre continuellement avec des messages:
```
WARNING: WatchFiles detected changes in '.venv/lib/python3.14/site-packages/...'
INFO: Shutting down
INFO: Started server process [...]
```

**Cause:**
Par défaut, Uvicorn avec `--reload` surveille tous les fichiers Python, y compris ceux dans `.venv/`, causant des rechargements constants lors du scan initial des dépendances.

**Solution appliquée:**
Limiter la surveillance au seul répertoire `app/`:

```bash
# scripts/start-dev.sh

# ❌ Avant
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ✅ Après
uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
```

**Alternative:**
Exclure explicitement .venv (peut ne pas fonctionner avec toutes les versions):
```bash
uvicorn app.main:app --reload --reload-exclude '.venv/*' --host 0.0.0.0 --port 8000
```

---

### ❌ Problème 7: Node.js ou npm manquant

**Symptômes:**
```
command not found: node
command not found: npm
```

**Cause:**
Node.js n'est pas installé sur le système.

**Solution macOS:**
```bash
# Avec Homebrew
brew install node

# Vérifier l'installation
node --version
npm --version
```

**Solution Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nodejs npm

# Ou avec nvm (recommandé)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

---

## 🔍 Diagnostic général

### Vérifier que tout fonctionne

```bash
# 1. Vérifier que Python est bien installé
python3 --version  # Devrait afficher 3.10+ (idéalement 3.10-3.13)

# 2. Vérifier que Node.js est installé
node --version     # Devrait afficher v18+
npm --version

# 3. Vérifier que les dépendances backend sont installées
cd backend
source .venv/bin/activate
python -c "import fastapi; import sqlalchemy; print('OK')"

# 4. Vérifier que la base de données est créée
ls -lh ../data/musique.db

# 5. Vérifier les tables
sqlite3 ../data/musique.db ".tables"

# 6. Tester le backend
curl http://localhost:8000/health

# 7. Vérifier le frontend
curl http://localhost:5173/
```

### Logs de débogage

```bash
# Logs backend avec détails
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --reload-dir app --log-level debug

# Logs frontend
cd frontend
npm run dev -- --debug
```

---

## 📞 Support

Si vous rencontrez d'autres problèmes:

1. Vérifiez les logs d'erreur complets
2. Consultez la documentation API: http://localhost:8000/docs
3. Vérifiez les issues GitHub du projet
4. Créez une issue détaillée avec:
   - Version de Python et Node.js
   - Système d'exploitation
   - Message d'erreur complet
   - Étapes pour reproduire

---

**Dernière mise à jour:** 30 janvier 2026  
**Problèmes documentés:** 7  
**Statut:** Tous résolus ✅
