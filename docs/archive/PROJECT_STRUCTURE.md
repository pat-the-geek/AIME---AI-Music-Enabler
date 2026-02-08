# 📁 AIME - AI Music Enabler - Structure du Projet

## 📊 Vue d'ensemble

```
AIME - AI Music Enabler/
├── 📄 Fichiers essentiels (top-level)
│   ├── README.md                    # Documentation principale
│   ├── docker-compose.yml           # Configuration Docker
│   ├── .env / .env.example          # Variables d'environnement
│   └── .gitignore                   # Fichiers ignorés Git
│
├── backend/                         # 🐍 API FastAPI
│   ├── app/
│   │   ├── main.py                 # Application principale
│   │   ├── models.py               # Modèles SQLAlchemy
│   │   ├── database.py             # Configuration BD
│   │   ├── api/                    # Endpoints API
│   │   └── services/               # Logique métier
│   ├── alembic/                    # Migrations BD
│   └── tests/                      # Tests unitaires
│
├── frontend/                        # ⚛️ Application React/Vite
│   ├── src/
│   │   ├── components/             # Composants React
│   │   ├── pages/                  # Pages principales
│   │   ├── hooks/                  # Hooks personnalisés
│   │   └── App.jsx
│   ├── public/                     # Assets publics
│   └── vite.config.ts              # Configuration Vite
│
├── roon-bridge/                    # 🎵 Bridge Roon
│   ├── app.js                      # Application Roon
│   ├── handlers/                   # Event handlers
│   └── config/                     # Configuration
│
├── scripts/                        # 🔧 Scripts d'automatisation
│   ├── tests/                      # 🧪 Fichiers de test
│   │   ├── test_*.py              # Tests unitaires/intégration
│   │   └── test_bash.sh           # Tests bash
│   │
│   ├── enrichment/                 # 🎨 Scripts d'enrichissement
│   │   ├── enrich_*.py            # Enrichissement des données
│   │   ├── auto_enrich_*.py       # Auto-enrichissement
│   │   └── enrichment_api_examples.py
│   │
│   ├── sync/                       # 🔄 Scripts de synchronisation
│   │   ├── sync_*.py              # Sync Discogs
│   │   └── sync_discogs*.py       # Variantes Discogs
│   │
│   ├── import/                     # 📥 Scripts d'import de données
│   │   ├── step1_fetch_discogs.py  # Fetch depuis Discogs
│   │   ├── step2_enrich_data.py    # Enrichissement
│   │   ├── step3_import_db.py      # Import en BD
│   │   └── step4_refresh_albums.py # Rafraîchissement
│   │
│   ├── verification/               # ✅ Scripts de vérification
│   │   ├── check_*.py             # Vérifications
│   │   └── verify_*.py            # Vérifications détaillées
│   │
│   └── utils/                      # 🛠️ Utilitaires
│       ├── run_*.py               # Scripts de lancement
│       ├── cleanup_*.py           # Nettoyage
│       ├── generate_*.py          # Génération
│       ├── refresh_*.py           # Rafraîchissement
│       ├── show_*.py              # Affichage
│       ├── fill_*.py              # Remplissage BD
│       ├── monitor_*.sh           # Monitoring
│       ├── phase*.py              # Phase scripts
│       ├── workflow_*.py          # Workflows
│       ├── euria_*.py             # Scripts Euria
│       ├── setup_*.py             # Setup scripts
│       └── final_*.py             # Finalisation
│
├── config/                        # ⚙️ Configuration
│   ├── database.yml              # Config BD
│   ├── api_keys.json            # Clés API
│   └── roon_config.json         # Config Roon
│
├── data/                         # 📚 Données
│   ├── discogs_data_*.json      # Données Discogs
│   ├── *.txt                    # Résultats de test
│   └── *.json                   # Données JSON
│
├── logs/                         # 📋 Fichiers de log
│   ├── enrichment.log           # Log d'enrichissement
│   ├── enrichment_*.log         # Logs variantes
│   ├── sync_output.log          # Log de sync
│   └── *.log                    # Autres logs
│
├── docs/                         # 📖 Documentation
│   ├── guides/                   # Guides pratiques
│   │   ├── AUTO-ENRICHISSEMENT-GUIDE.md
│   │   ├── EURIA-SPOTIFY-INTEGRATION-GUIDE.md
│   │   ├── INTEGRATION-SUMMARY.md
│   │   ├── PHASE4-*.md
│   │   ├── DISCOGS-*.md
│   │   ├── PLAYBACK-FIX-*.md
│   │   ├── ROON-*.md
│   │   └── ...
│   ├── api/                     # Documentation API
│   ├── architecture/            # Diagrammes architecture
│   ├── deployment/              # Déploiement
│   └── ...
│
└── tests/                        # 🧪 Résultats des tests
    ├── test_output.txt          # Sortie tests
    ├── normalization_test_results.txt
    └── perf_result.txt
```

## 📋 Guide rapide des fichiers

### 🚀 **Démarrage du projet**
```bash
cd backend && source .venv/bin/activate
python -m uvicorn app.main:app --reload

# Dans un autre terminal
cd frontend && npm run dev

# Roon Bridge
cd roon-bridge && node app.js
```

### 🔄 **Synchronisation Discogs**
```bash
python scripts/sync/sync_discogs_final.py
```

### 🎨 **Enrichissement des données**
```bash
python scripts/enrichment/auto_enrich_integrated.py
```

### ✅ **Vérifications**
```bash
python scripts/verification/check_enrichment_status.py
```

### 📊 **Tests**
```bash
# Tests spécifiques
python scripts/tests/test_discogs_simple.py

# Test bash complet
bash scripts/utils/test_bash.sh
```

## 🎯 Conventions de nommage

| Préfixe | Type | Localisation |
|---------|------|--------------|
| `test_` | Tests | `scripts/tests/` |
| `check_` | Vérification | `scripts/verification/` |
| `verify_` | Vérification détaillée | `scripts/verification/` |
| `sync_` | Synchronisation | `scripts/sync/` |
| `step*.py` | Import/pipeline | `scripts/import/` |
| `enrich_` | Enrichissement | `scripts/enrichment/` |
| `auto_enrich_` | Auto-enrichissement | `scripts/enrichment/` |
| `run_` | Lancement | `scripts/utils/` |
| `cleanup_` | Nettoyage | `scripts/utils/` |
| `generate_` | Génération | `scripts/utils/` |
| `monitor_` | Monitoring | `scripts/utils/` |

## 🔗 Dépendances principales

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Frontend**: React, Vite, TailwindCSS
- **Bridge**: Node.js, Roon API
- **BD**: PostgreSQL (ou SQLite en dev)
- **APIs**: Discogs, Spotify, IA services

## 📝 Notes importantes

- Les fichiers au **top-level** sont limités aux essentiels uniquement
- Tous les **scripts** sont organisés par **catégorie** dans `scripts/`
- La **documentation** est centralisée dans `docs/guides/`
- Les **logs** sont séparés dans `logs/`
- Les **données** temporaires vont dans `data/`

---

✨ **Dernière mise à jour**: 6 février 2026
