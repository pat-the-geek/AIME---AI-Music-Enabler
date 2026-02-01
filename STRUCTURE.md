# 📁 Structure du Projet AIME - AI Music Enabler

## 🎯 Organisation des fichiers

### Racine du projet `/`
```
├── README.md                    # 📖 Vue d'ensemble et guide principal
├── STRUCTURE.md                 # 📁 Ce fichier - structure du projet
├── docker-compose.yml           # 🐳 Configuration Docker
├── .env                         # 🔐 Variables d'environnement (ignoré par Git)
├── .gitignore                   # 🚫 Fichiers ignorés par Git
├── backend/                     # 🔧 API FastAPI
├── frontend/                    # ⚛️ Application React
├── config/                      # ⚙️ Configuration application
├── data/                        # 🗄️ Base de données SQLite
├── docs/                        # 📚 Documentation complète
├── scripts/                     # 🛠️ Scripts de déploiement
├── Scheduled Output/            # 📦 Exports automatiques (haikus, markdown, json)
└── Screen captures/             # 🖼️ Captures d'écran de l'UI
```

### Documentation `/docs`
```
docs/
├── README.md                    # 📋 Index de la documentation
├── API.md                       # 🔌 Documentation API REST
├── QUICKSTART.md                # 🚀 Guide de démarrage rapide
├── TROUBLESHOOTING.md           # 🔧 Résolution des problèmes
├── GITHUB-REPO-INFO.md          # 📝 Info GitHub (description, topics, SEO)
├── PROJECT-SUMMARY.md           # 📊 Résumé complet du projet
├── STATUS.md                    # ✅ État actuel de l'application
├── QUICK-REFERENCE.md           # ⚡ Référence rapide
├── INSTALLATION-CHECKLIST.md   # ✓ Checklist installation
├── RELIABILITY-GUIDE.md         # 🛡️ Guide fiabilité système
│
├── architecture/                # 🏗️ Documentation architecture
│   ├── ARCHITECTURE-COMPLETE.md # Architecture complète du système
│   ├── ARCHITECTURE-SCHEMA.md   # Schémas visuels (ASCII art)
│   └── DATABASE-SCHEMA.md       # Schéma relationnel (Mermaid ER)
│
├── guides/                      # 📖 Guides utilisateur
│   ├── AUTO-RESTART-TEST-GUIDE.md # Guide test auto-restart services
│   └── TESTING.md               # Guide de test complet
│
├── features/                    # 🎵 Documentation des fonctionnalités
│   ├── NOUVELLES-FONCTIONNALITES.md
│   ├── JOURNAL-TIMELINE-DOC.md
│   ├── LASTFM-IMPORT-TRACKER-DOC.md
│   ├── ROON-TRACKER-DOC.md
│   │
│   └── roon/                    # 🎛️ Intégration Roon
│       ├── ROON-INTEGRATION-COMPLETE.md   # Guide complet intégration
│       ├── ROON-ZONES-FIX.md              # Fix zones au démarrage
│       ├── ROON-BUGS-TRACKING.md          # Suivi bugs et investigation
│       ├── ROON-FINAL-STATUS.md           # Statut final implémentation
│       ├── ROON-IMPLEMENTATION-COMPLETE.md
│       ├── ROON-IMPLEMENTATION-SUMMARY.md
│       └── FRONTEND-CHANGES-ROON-PLAYLISTS.md
│
├── changelogs/                  # 📝 Historique des modifications
│   ├── CHANGELOG.md
│   ├── CHANGELOG-UI-ENRICHMENT.md
│   └── CHANGELOG-UNIFIED-ALBUM-DISPLAY.md
│
├── config/                      # 🔧 Documentation de configuration
│   └── TRACKER-CONFIG-OPTIMALE.md
│
├── debug/                       # 🐛 Debug et corrections
│   ├── DEBUG-DISCOGS.md
│   ├── EXPLICATION-404-DISCOGS.md
│   ├── CORRECTIONS-SYNC-DISCOGS.md
│   ├── AMELIORATIONS-SYNC-ENRICHIE.md
│   ├── ENRICHISSEMENT-RETROACTIF.md
│   ├── LASTFM-IMPORT-CHANGES.md
│   ├── LASTFM-IMPORT-COMPLETE.md
│   ├── LASTFM-IMPORT-ENHANCEMENT.md
│   ├── PLAYLIST-CREATION-TROUBLESHOOT.md
│   ├── app.log
│   ├── backend-restart.log
│   ├── backend.log
│   └── startup.log
│
├── scripts-util/                # 🔨 Scripts utilitaires
│   ├── analyze_duplicates.py
│   ├── apply_10min_dedup.py
│   ├── check_db_final.py
│   ├── cleanup_duplicates.py
│   ├── find_album_dups.py
│   ├── merge_duplicate_albums.py
│   ├── merge_duplicate_tracks.py
│   ├── test_lastfm_import.py
│   ├── verify_db.py
│   └── test-playlist-endpoints.sh
│
└── specs/                       # 🏗️ Spécifications techniques
    └── SPECIFICATION-REACT-REBUILD.md
```

### Backend `/backend`
```
backend/
├── Dockerfile                   # Image Docker backend
├── requirements.txt             # Dépendances Python
├── alembic/                     # Migrations de base de données
│   └── versions/
│
└── app/
    ├── __init__.py
    ├── main.py                  # Point d'entrée FastAPI
    ├── database.py              # Configuration SQLAlchemy
    │
    ├── api/                     # 🌐 Endpoints API
    │   └── v1/
    │       ├── collection.py    # Albums Discogs
    │       ├── history.py       # Historique d'écoute
    │       ├── playlists.py     # Playlists intelligentes
    │       └── services.py      # Services (trackers, scheduler)
    │
    ├── core/                    # ⚙️ Configuration
    │   └── config.py
    │
    ├── models/                  # 🗄️ Modèles SQLAlchemy
    │   ├── album.py
    │   ├── artist.py
    │   ├── track.py
    │   ├── listening_history.py
    │   ├── playlist.py
    │   ├── metadata.py
    │   ├── image.py
    │   └── service_state.py     # 🆕 États services (auto-restart)
    │
    ├── schemas/                 # 📋 Schémas Pydantic
    │   ├── album.py
    │   ├── artist.py
    │   ├── track.py
    │   ├── history.py
    │   └── playlist.py
    │
    ├── services/                # 🔌 Services externes
    │   ├── ai_service.py        # IA Euria
    │   ├── spotify_service.py   # Spotify API
    │   ├── discogs_service.py   # Discogs API
    │   ├── lastfm_service.py    # Last.fm API
    │   ├── roon_service.py      # Roon API
    │   ├── tracker_service.py   # Tracker Last.fm
    │   ├── roon_tracker_service.py  # Tracker Roon
    │   ├── scheduler_service.py # Scheduler IA
    │   └── playlist_generator.py # Générateur de playlists
    │
    └── utils/                   # 🛠️ Utilitaires
        └── __init__.py
```

### Frontend `/frontend`
```
frontend/
├── Dockerfile                   # Image Docker frontend
├── nginx.conf                   # Configuration Nginx
├── package.json                 # Dépendances npm
├── tsconfig.json                # Configuration TypeScript
├── vite.config.ts               # Configuration Vite
├── index.html                   # Point d'entrée HTML
│
├── public/                      # Fichiers publics statiques
│
└── src/
    ├── main.tsx                 # Point d'entrée React
    ├── App.tsx                  # Composant principal
    │
    ├── api/                     # 🌐 Client API
    │   └── client.ts
    │
    ├── components/              # 🧩 Composants réutilisables
    │   ├── AlbumDetailDialog.tsx
    │   ├── FloatingRoonController.tsx  # 🆕 Widget Roon flottant
    │   └── layout/
    │       ├── Layout.tsx
    │       ├── Sidebar.tsx
    │       └── TopBar.tsx
    │
    ├── contexts/                # 🔄 Contextes React
    │   └── RoonContext.tsx      # 🆕 État global Roon
    │
    ├── pages/                   # 📄 Pages de l'application
    │   ├── Collection.tsx       # Collection Discogs
    │   ├── Journal.tsx          # Historique d'écoute
    │   ├── Timeline.tsx         # Vue chronologique
    │   ├── Analytics.tsx        # Analytics & patterns
    │   ├── Playlists.tsx        # Playlists intelligentes + Roon controls 🆕
    │   └── Settings.tsx         # Configuration trackers/scheduler
    │
    ├── styles/                  # 🎨 Styles
    │   └── theme.ts             # Thème Material-UI
    │
    └── types/                   # 📐 Types TypeScript
        └── models.ts
```

### Configuration `/config`
```
config/
├── app.json                     # Configuration de l'application
└── secrets.json                 # Clés API (ignoré par Git)
```

### Données `/data`
```
data/
├── musique.db                   # Base SQLite (ignorée par Git)
└── backups/                     # Sauvegardes (ignorées par Git)
    └── .gitkeep
```

### Scripts `/scripts`
```
scripts/
├── setup.sh                     # Installation complète
├── start-dev.sh                 # Démarrage en mode dev
├── check_db_status.py           # Vérifier la base
├── check_sync.py                # Vérifier la synchronisation
├── enrich_albums.py             # Enrichir les albums
├── enrich_all_fast.py           # Enrichissement rapide
├── enrich_spotify.py            # Enrichir Spotify uniquement
├── import_lastfm_history.py     # Importer historique Last.fm
├── optimize_tracker_config.py   # Optimiser config tracker (IA)
├── test_discogs.py              # Tester Discogs
├── test_sync_enhanced.py        # Tester synchronisation
├── find_404_releases.py         # Trouver releases 404
└── validate_corrections.py      # Valider corrections
```

### Tests Backend `/backend`
```
backend/
├── create_service_states_table.py  # 🆕 Migration table service_states
├── test_auto_restart.py            # 🆕 Tests auto-restart services
├── test_markdown_export.py         # Tests export Markdown
└── validate_startup.py             # Validation démarrage
```

---

## 📝 Conventions de nommage

### Fichiers de documentation (Markdown)
- **MAJUSCULES** avec tirets : `NOUVELLES-FONCTIONNALITES.md`
- Suffixes :
  - `-DOC` pour documentations : `ROON-TRACKER-DOC.md`
  - `-SPEC` pour spécifications : `SPECIFICATION-REACT-REBUILD.md`
- Préfixes :
  - `CHANGELOG-` pour historiques : `CHANGELOG-UI-ENRICHMENT.md`
  - `DEBUG-` pour debug : `DEBUG-DISCOGS.md`

### Code Backend (Python)
- **snake_case** : `tracker_service.py`
- Suffixe `_service` pour les services
- Suffixe `_model` implicite dans `/models`
- Suffixe `_schema` implicite dans `/schemas`

### Code Frontend (TypeScript)
- **PascalCase** pour composants : `AlbumDetailDialog.tsx`
- **camelCase** pour utilitaires : `client.ts`
- **PascalCase** pour pages : `Analytics.tsx`

### Scripts (Python)
- **snake_case** avec verbes : `check_db_status.py`
- Préfixes courants : `check_`, `test_`, `enrich_`, `import_`

---

## 🎯 Placement des nouveaux fichiers

| Type | Emplacement | Exemple |
|------|-------------|---------|
| **Documentation générale** | `/docs/` | `API.md` |
| **Changelog** | `/docs/changelogs/` | `CHANGELOG-PLAYLISTS.md` |
| **Doc fonctionnalité** | `/docs/features/` | `HAIKU-DOC.md` |
| **Configuration** | `/docs/config/` | `SCHEDULER-CONFIG.md` |
| **Debug/Correction** | `/docs/debug/` | `FIX-ROON-AUTH.md` |
| **Spécification** | `/docs/specs/` | `SPEC-MOBILE-APP.md` |
| **Endpoint API** | `/backend/app/api/v1/` | `recommendations.py` |
| **Service backend** | `/backend/app/services/` | `recommendation_service.py` |
| **Modèle SQLAlchemy** | `/backend/app/models/` | `recommendation.py` |
| **Schéma Pydantic** | `/backend/app/schemas/` | `recommendation.py` |
| **Page frontend** | `/frontend/src/pages/` | `Recommendations.tsx` |
| **Composant réutilisable** | `/frontend/src/components/` | `TrackCard.tsx` |
| **Script utilitaire** | `/scripts/` | `export_playlists.py` |

---

## 🔄 Workflow de développement

### Ajout d'une nouvelle fonctionnalité

1. **Spécification** : Créer `/docs/specs/SPEC-FEATURE.md`
2. **Backend** :
   - Modèle dans `/backend/app/models/`
   - Service dans `/backend/app/services/`
   - Endpoint dans `/backend/app/api/v1/`
   - Schéma dans `/backend/app/schemas/`
3. **Frontend** :
   - Types dans `/frontend/src/types/`
   - Composants dans `/frontend/src/components/`
   - Page dans `/frontend/src/pages/`
4. **Documentation** :
   - Doc utilisateur dans `/docs/features/`
   - Mise à jour API dans `/docs/API.md`
   - Changelog dans `/docs/changelogs/CHANGELOG.md`
5. **Tests** : Script dans `/scripts/test_feature.py`

### Correction de bug

1. **Debug** : Documenter dans `/docs/debug/FIX-*.md`
2. **Code** : Corriger dans le module concerné
3. **Test** : Ajouter test dans `/scripts/`
4. **Doc** : Mettre à jour `/docs/TROUBLESHOOTING.md` si pertinent
5. **Changelog** : Ajouter entrée

---

## ✅ Checklist avant commit

- [ ] Les nouveaux fichiers sont au bon endroit
- [ ] Le nommage respecte les conventions
- [ ] La documentation est à jour (`/docs/`)
- [ ] Le changelog est mis à jour
- [ ] Les imports sont corrects
- [ ] Les tests passent
- [ ] `.gitignore` est à jour si nécessaire

---

**Version** : 4.0.0  
**Dernière mise à jour** : 31 janvier 2026  
**Auteur** : AIME Project Team
