# 📋 SETTINGS - Informations Scheduler

**Créé:** 2 février 2026  
**État:** ✅ Production Ready

---

## 🔑 Éléments Planifiés Visibles

### ✅ Configuration Centralisée

**Fichier:** `config/app.json` → Section `scheduler`

Tous les éléments du scheduler sont désormais visibles et documentés dans **app.json**:

```
✓ enrichment_scheduler (pipeline principal à 02:00)
  ├─ audit_database
  ├─ fix_malformed_artists
  ├─ enrich_musicbrainz_images
  └─ auto_enrichment (avec 4 features)

✓ tasks (6 tâches supplémentaires)
  ├─ daily_enrichment (02:00)
  ├─ generate_haiku_scheduled (06:00)
  ├─ export_collection_markdown (08:00)
  ├─ export_collection_json (10:00)
  ├─ weekly_haiku (dimanche 20:00)
  ├─ monthly_analysis (03:00)
  └─ optimize_ai_descriptions (toutes les 6h)
```

---

## 📁 Fichiers de Settings Disponibles

### 1. **config/app.json** (3.9K)
- ✅ Scheduler général et enrichissement détaillés
- ✅ Configuration serveur, database
- ✅ API keys et tokens
- ✅ Tous les services et tâches

**À Consulter Pour:** Configuration globale, état des tâches

### 2. **config/scheduler_config.json** (177B)
- ✅ Services du pipeline d'enrichissement
- ✅ Timing (daily_02:00)

**À Consulter Pour:** Liste simple des services actifs

### 3. **config/enrichment_config.json** (822B)
- ✅ Features d'enrichissement détaillées
- ✅ Rate limits par API
- ✅ Configuration data quality

**À Consulter Pour:** Paramètres d'enrichissement, limites API

### 4. **config/SCHEDULER-SETTINGS.md** (6.0K) ⭐ NOUVEAU
- ✅ Documentation complète du scheduler
- ✅ Vue d'ensemble et descriptions détaillées
- ✅ État actuel et améliorations attendues
- ✅ Commandes de contrôle

**À Consulter Pour:** Guide détaillé, monitoring, contrôle

### 5. **config/secrets.json** (755B)
- ✅ Clés API (LastFM, Spotify, Discogs)
- ✅ Credentials EURIA

**À Consulter Pour:** Vérifier les API keys (ne pas copier publiquement)

### 6. **config/deployment_config.json** (633B)
- ✅ Configuration de déploiement

---

## 🎯 Vue Rapide - 02:00 Daily Pipeline

**Tous les éléments visibles dans `config/app.json`:**

```json
{
  "enrichment_scheduler": {
    "enabled": true,
    "schedule": "daily_02:00",
    "description": "Pipeline automatique d'enrichissement et correction de données",
    "services": [
      {
        "name": "audit_database",
        "description": "Audit complet de la base de données",
        "enabled": true
      },
      {
        "name": "fix_malformed_artists",
        "items_fixed": 5,  // ← Déjà complété
        "enabled": true
      },
      {
        "name": "enrich_musicbrainz_images",
        "target_albums": 545,
        "batch_size": 50,
        "enabled": true
      },
      {
        "name": "auto_enrichment",
        "features": {
          "enrich_images": true,
          "generate_descriptions": true,
          "detect_genres": true,
          "fix_artist_formatting": true
        },
        "enabled": true
      }
    ]
  }
}
```

---

## 📊 Résumé État Actuel

| Élément | Statut | Détails |
|---------|--------|---------|
| **Scheduler Principal** | ✅ Enabled | 02:00 daily |
| **Audit Database** | ✅ Actif | Quotidien |
| **Fix Artists** | ✅ Complété | 5 albums corrigés |
| **Enrich Images** | ✅ Actif | 545 albums cibles |
| **Auto Enrichment** | ✅ 4 features | Images, descriptions, genres, artistes |
| **Generate Haikus** | ✅ Actif | 06:00 daily |
| **Export Markdown** | ✅ Actif | 08:00 daily |
| **Export JSON** | ✅ Actif | 10:00 daily |
| **Weekly Haiku** | ✅ Actif | Dimanche 20:00 |
| **Monthly Analysis** | ✅ Actif | 03:00 monthly |
| **Optimize AI** | ✅ Actif | Toutes les 6h |

---

## 🔍 Comment Vérifier

### Voir tous les éléments planifiés:
```bash
cat config/app.json | grep -A 200 "scheduler"
```

### Voir la configuration d'enrichissement:
```bash
cat config/enrichment_config.json
```

### Lire la documentation complète:
```bash
cat config/SCHEDULER-SETTINGS.md
```

### Vérifier l'état en JSON:
```bash
python3 -c "import json; print(json.dumps(json.load(open('config/app.json'))['scheduler'], indent=2))"
```

---

## ⚙️ Gestion des Éléments

### Désactiver l'enrichissement:
```bash
# Dans config/app.json, changer:
"enabled": false  // sous enrichment_scheduler
```

### Désactiver une feature:
```bash
# Dans config/enrichment_config.json, changer:
"enrich_images": false  // sous features
```

### Changer l'heure d'exécution:
```bash
# Dans config/app.json, changer:
"schedule": "daily_03:00"  // nouveau créneau
"time": "03:00"  // nouvelle heure
```

---

## 📚 Documentation Complète

| Document | Contenu |
|----------|---------|
| [config/SCHEDULER-SETTINGS.md](SCHEDULER-SETTINGS.md) | Guide détaillé scheduler et monitoring |
| [docs/PRODUCTION.md](../docs/PRODUCTION.md) | Guide production complet |
| [docs/IMPROVEMENTS.md](../docs/IMPROVEMENTS.md) | Détails des améliorations |
| [docs/AUDIT-2026-02-02.md](../docs/AUDIT-2026-02-02.md) | Audit initial |
| [docs/DEPLOYMENT_REPORT.json](../docs/DEPLOYMENT_REPORT.json) | Rapport déploiement |

---

## ✅ Vérification - Tous les Éléments Schedulés Sont Visibles

**Locations où vérifier:**

1. ✅ **config/app.json** → scheduler.enrichment_scheduler (4 services)
2. ✅ **config/app.json** → scheduler.tasks (7 tâches)
3. ✅ **config/scheduler_config.json** → services array
4. ✅ **config/enrichment_config.json** → features et rate_limits
5. ✅ **config/SCHEDULER-SETTINGS.md** → Documentation complète

---

**État:** 🟢 TOUS LES ÉLÉMENTS SCHEDULÉS SONT VISIBLES DANS SETTINGS

**Last Update:** 2 février 2026, 18:15
