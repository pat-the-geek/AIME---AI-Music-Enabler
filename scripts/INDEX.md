# 🔧 AIME Scripts - Index et Organisation

## 📁 Structure des Répertoires

```
scripts/
├── 📄 README.md           (Documentation des scripts)
├── 📄 INDEX.md            (Ce fichier)
│
├── 🧪 tests/              (Tests - 30+ fichiers)
│   ├── test_*.py         (Tests unitaires/intégration)
│   ├── test-*.sh         (Tests bash)
│   ├── test_bash.sh      (Suite de test complète)
│   └── ...
│
├── 🎨 enrichment/         (Enrichissement de données - 14 fichiers)
│   ├── enrich_*.py       (Scripts d'enrichissement)
│   ├── auto_enrich_*.py  (Auto-enrichissement)
│   ├── enrichment_api_examples.py
│   └── ...
│
├── 🔄 sync/               (Synchronisation Discogs - 9 fichiers)
│   ├── sync_discogs*.py  (Sync Discogs variantes)
│   ├── sync_*.py         (Autres sync)
│   └── ...
│
├── 📥 import/             (Import de données - 4 fichiers)
│   ├── step1_fetch_discogs.py
│   ├── step2_enrich_data.py
│   ├── step3_import_db.py
│   └── step4_refresh_albums.py
│
├── ✅ verification/       (Vérification et audit - 20+ fichiers)
│   ├── audit_*.py        (Audit de base de données)
│   ├── check_*.py        (Vérifications)
│   ├── validate_*.py     (Validations)
│   ├── verify_*.py       (Vérifications détaillées)
│   └── ...
│
└── 🛠️  utils/             (Utilitaires - 70+ fichiers)
    ├── *.sh              (Scripts shell - setup, start, stop, health-check)
    ├── cleanup_*.py      (Nettoyage de base de données)
    ├── fix_*.py          (Corrections)
    ├── repair_*.py       (Réparations)
    ├── generate_*.py     (Génération de rapports)
    ├── optimize_*.py     (Optimisations)
    ├── improvement_*.py  (Améliorations)
    ├── final_*.py        (Scripts finaux)
    ├── SCHEDULER*.py     (Scripts scheduler)
    ├── PUBLICATION*.py   (Publication)
    ├── trigger_*.py      (Déclencheurs)
    ├── import_lastfm*.py (Import LastFM)
    ├── find_*.py         (Recherche/diagnostic)
    ├── deploy_*.py       (Déploiement)
    ├── IMPROVEMENTS_SUMMARY.py
    └── ...
```

## 📊 Statistiques

```
Total: 150+ fichiers de scripts organisés

│ Catégorie      │ Fichiers │ Type                    │
├────────────────┼──────────┼─────────────────────────┤
│ tests          │   30+    │ Tests et validation     │
│ enrichment     │   14     │ Enrichissement IA/API   │
│ sync           │    9     │ Synchronisation données │
│ import         │    4     │ Pipeline d'import       │
│ verification   │   20+    │ Vérifications/Audit     │
│ utils          │   70+    │ Utilitaires/Outils      │
└────────────────┴──────────┴─────────────────────────┘
```

## 🚀 Guide Rapide d'Utilisation

### Démarrage des Services
```bash
cd scripts/utils
bash start-services.sh      # Démarre tous les services
bash stop-services.sh       # Arrête tous les services
bash health-check.sh        # Vérification de santé
```

### Synchronisation Discogs
```bash
cd scripts/sync
python3 sync_discogs_final.py
```

### Enrichissement des Données
```bash
cd scripts/enrichment
python3 auto_enrich_integrated.py
```

### Vérification des Données
```bash
cd scripts/verification
python3 check_enrichment_status.py
python3 audit_database.py
```

### Tests
```bash
cd scripts/tests
python3 test_discogs_simple.py      # Test Discogs simple
bash test_bash.sh                   # Suite complète
```

## 🎯 Convention de Nommage

| Préfixe/Pattern | Répertoire | Type |
|-----------------|-----------|------|
| `test_` | tests/ | Tests unitaires |
| `test-` | tests/ | Tests bash |
| `enrich_` | enrichment/ | Enrichissement basique |
| `auto_enrich_` | enrichment/ | Auto-enrichissement |
| `sync_` | sync/ | Synchronisation |
| `step*.py` | import/ | Pipeline d'import |
| `audit_` | verification/ | Audit BD |
| `check_` | verification/ | Vérifications |
| `validate_` | verification/ | Validations |
| `verify_` | verification/ | Vérifications détaillées |
| `cleanup_` | utils/ | Nettoyage |
| `fix_` | utils/ | Corrections |
| `repair_` | utils/ | Réparations |
| `generate_` | utils/ | Génération |
| `optimize_` | utils/ | Optimisations |
| `*.sh` | utils/ | Scripts shell |
| Autres | utils/ | Utilitaires divers |

## 📝 Types de Scripts

### 🧪 Tests (`tests/`)
- Tests unitaires de modules
- Tests d'intégration API
- Tests de performance
- Tests de synchronisation
- Tests bash de déploiement

### 🎨 Enrichissement (`enrichment/`)
- Enrichissement à partir d'APIs (Spotify, MusicBrainz, etc.)
- Auto-enrichissement IA
- Enrichissement d'images
- Enrichissement de descriptions

### 🔄 Synchronisation (`sync/`)
- Sync Discogs complet
- Sync Discogs optimisé
- Sync partielle
- Sync par étapes

### 📥 Import (`import/`)
1. **step1**: Fetch depuis Discogs
2. **step2**: Enrichissement des données
3. **step3**: Import en base de données
4. **step4**: Rafraîchissement des albums

### ✅ Vérification (`verification/`)
- Audit de la base de données
- Vérification d'enrichissement
- Validation de données
- Vérification de qualité
- Vérification LastFM
- Vérification d'images

### 🛠️ Utilitaires (`utils/`)
- **Services**: start, stop, health-check
- **Nettoyage**: cleanup duplicates, bad data
- **Fixation**: fix artists, formats
- **Génération**: rapports, audits
- **Optimisation**: scheduler, tracker
- **Déploiement**: production deployment
- **Monitoring**: health checks, analytics
- **Divers**: import LastFM, trigger, publish

## 🔍 Découverte de Scripts

### Par fonction
```bash
grep -r "def main" scripts/*/  # Trouver tous les main scripts
grep -r "argparse" scripts/*/  # Scripts avec CLI
grep -r "async " scripts/*/    # Scripts asynchrones
```

### Par dépendance
```bash
grep -r "import requests" scripts/*/  # API calls
grep -r "from sqlalchemy" scripts/*/  # BD access
grep -r "FastAPI\|starlette" scripts/*/  # Web
```

## ⚙️ Configuration

Chaque catégorie de scripts peut avoir une configuration spécifique:
- Variables d'environnement: voir `config/.env.example`
- Clés API: voir `config/api_keys.json`
- Config BD: voir `config/database.yml`

## 🔐 Notes de Sécurité

- Ne pas commiter les fichiers `.env` ou `config/api_keys.json`
- Gitignore déjà configuré pour ignorer ces fichiers
- Utiliser les templates `.example` pour la configuration

## 📚 Voir Aussi

- [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) - Structure globale du projet
- [README.md](./README.md) - Documentation des scripts
- [backend/](../backend/) - Code de l'API
- [frontend/](../frontend/) - Code du frontend
- [docs/](../docs/) - Documentation complète

---

**Dernière mise à jour**: 6 février 2026
