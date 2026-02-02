# Scheduler Settings - Configuration Complète

## 📅 Vue d'ensemble du Scheduler

Tous les éléments schedulés sont configurés dans:
- **config/app.json** → `scheduler` section
- **config/scheduler_config.json** → Configuration d'enrichissement
- **config/enrichment_config.json** → Détails API et features

---

## 🔄 Pipeline d'Enrichissement Quotidien (02:00)

**Localisation:** `config/app.json` → `scheduler.enrichment_scheduler`

### Services Exécutés

#### 1. **audit_database**
- **Description:** Audit complet de la base de données
- **Fonction:** Compte albums, artistes, pistes, évalue qualité
- **Fréquence:** Quotidienne à 02:00
- **Script:** `scripts/audit_database.py`

#### 2. **fix_malformed_artists**
- **Description:** Correction des artistes collaboratifs mal formatés
- **Fonction:** Sépare les noms d'artistes combinés (ex: "John & Jane" → 2 artistes)
- **Statut:** 5 albums déjà corrigés
- **Fréquence:** Quotidienne à 02:00
- **Script:** `scripts/fix_malformed_artists.py`

#### 3. **enrich_musicbrainz_images**
- **Description:** Enrichissement d'images via MusicBrainz
- **Cible:** 545 albums sans images
- **Batch Size:** 50 albums/exécution
- **Rate Limit:** 60 requêtes/minute
- **Source:** MusicBrainz API → Cover Art Archive
- **Expected Gain:** ~450 images (de 58% → 10% sans images)
- **Fréquence:** Quotidienne à 02:00
- **Script:** `scripts/enrich_musicbrainz_images.py`

#### 4. **auto_enrichment**
- **Description:** Enrichissement automatique complet
- **Features Activées:**
  - ✅ `enrich_images` - Images intelligentes (MusicBrainz → Discogs → Spotify)
  - ✅ `generate_descriptions` - Descriptions automatiques
  - ✅ `detect_genres` - Détection de genres
  - ✅ `fix_artist_formatting` - Formatage artistes
- **Sources:** MusicBrainz, Discogs, Spotify
- **Rate Limits:**
  - MusicBrainz: 60/min
  - Discogs: 120/min
  - Spotify: 60/min
- **Fréquence:** Quotidienne à 02:00
- **Script:** `scripts/auto_enrichment.py`

---

## 📋 Autres Tâches Planifiées

### 06:00 - Génération Haikus
```json
{
  "name": "generate_haiku_scheduled",
  "time": "06:00",
  "frequency": "quotidienne",
  "description": "Génération haikus pour 5 albums aléatoires"
}
```

### 08:00 - Export Markdown
```json
{
  "name": "export_collection_markdown",
  "time": "08:00",
  "frequency": "quotidienne",
  "description": "Export collection en markdown"
}
```

### 10:00 - Export JSON
```json
{
  "name": "export_collection_json",
  "time": "10:00",
  "frequency": "quotidienne",
  "description": "Export collection en JSON"
}
```

### 20:00 (Dimanche) - Haiku Hebdomadaire
```json
{
  "name": "weekly_haiku",
  "frequency": 1,
  "unit": "week",
  "day": "sunday",
  "time": "20:00"
}
```

### 03:00 - Analyse Mensuelle
```json
{
  "name": "monthly_analysis",
  "frequency": 1,
  "unit": "month",
  "time": "03:00"
}
```

### Toutes les 6 heures - Optimisation Descriptions IA
```json
{
  "name": "optimize_ai_descriptions",
  "frequency": 6,
  "unit": "hour"
}
```

---

## 🔧 Configuration Détaillée

### enrichment_config.json
**Chemin:** `config/enrichment_config.json`

```json
{
  "auto_enrichment": {
    "enabled": true,
    "schedule": "daily_02:00",
    "sources": ["musicbrainz", "discogs", "spotify"],
    "features": {
      "enrich_images": true,
      "generate_descriptions": true,
      "detect_genres": true,
      "fix_artist_formatting": true
    },
    "batch_size": 50,
    "timeout_seconds": 10
  },
  "data_quality": {
    "min_completion_pct": 80,
    "image_priority": ["spotify", "lastfm", "musicbrainz", "discogs"],
    "validate_artists": true,
    "remove_duplicates": true
  }
}
```

### scheduler_config.json
**Chemin:** `config/scheduler_config.json`

```json
{
  "enabled": true,
  "schedule": "daily_02:00",
  "services": [
    "audit_database",
    "fix_malformed_artists",
    "enrich_musicbrainz_images",
    "auto_enrichment"
  ]
}
```

---

## 📊 État Actuel (02 Février 2026)

### Base de Données
- **Albums:** 940
- **Artistes:** 645 (5 corrigés)
- **Pistes:** 1,836
- **Scrobbles:** 2,113
- **Images:** 395/940 (42% avec images, 58% sans)
- **Quality Score:** 85/100

### Améliorations Attendues (4 semaines)
- Images: 58% → 10% sans (gain ~450 images)
- Genres: ~150-200 albums détectés
- Descriptions: 100% couverts
- Quality Score: 85 → 92/100

---

## 🚀 Commandes de Contrôle

### Vérifier l'état du scheduler
```bash
cat config/app.json | grep -A 50 "scheduler"
```

### Exécuter le pipeline manuellement
```bash
python3 scripts/improvement_pipeline.py
```

### Démarrer le scheduler
```bash
python3 scripts/data_improvement_scheduler.py &
```

### Vérifier les logs récents
```bash
tail -f backend/logs/* 2>/dev/null | head -100
```

### Générer un rapport d'audit
```bash
python3 scripts/generate_audit_report.py
```

---

## ⚙️ Activation/Désactivation

### Désactiver l'enrichissement complet
Modifier dans `config/app.json`:
```json
"enrichment_scheduler": {
  "enabled": false,
  ...
}
```

### Désactiver une feature spécifique
Modifier dans `config/enrichment_config.json`:
```json
"features": {
  "enrich_images": false,
  "generate_descriptions": true,
  ...
}
```

### Désactiver un service du pipeline
Modifier dans `config/scheduler_config.json`:
```json
"services": [
  "audit_database",
  "fix_malformed_artists",
  // "enrich_musicbrainz_images",  <- Commenté
  "auto_enrichment"
]
```

---

## 📝 Documentation Complète

- [PRODUCTION.md](../docs/PRODUCTION.md) - Guide de production complet
- [IMPROVEMENTS.md](../docs/IMPROVEMENTS.md) - Détails des améliorations
- [AUDIT-2026-02-02.md](../docs/AUDIT-2026-02-02.md) - Rapport d'audit initial
- [DEPLOYMENT_REPORT.json](../docs/DEPLOYMENT_REPORT.json) - Rapport de déploiement

---

## 🔍 Monitoring

Tous les événements du scheduler sont loggés. Pour surveiller:

1. **Vérifiez app.json** pour l'état de configuration
2. **Consultez les logs** pour exécution réelle
3. **Générez un audit** pour vérifier l'impact

✅ **SYSTÈME PRÊT POUR PRODUCTION**
