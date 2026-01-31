# 📅 AIME Scheduler Tasks - Guide Complet

## Vue d'Ensemble

Le système de scheduler AIME automatise les tâches critiques de génération et d'export de contenu. Trois nouvelles tâches ont été ajoutées pour une gestion intelligente et planifiée de votre collection musicale.

## ✨ Nouvelles Tâches Ajoutées

### 1. 🎋 Génération de Haikus pour 5 Albums Aléatoires
**ID:** `generate_haiku_scheduled`  
**Fréquence:** Quotidiennement à 6h00  
**Fichier:** `backend/app/services/scheduler_service.py` (ligne 318-364)

#### Fonctionnalités
- Sélection de 5 albums aléatoires de votre collection
- Génération automatique de haikus pour chaque album via Euria AI
- Export en markdown avec formatage élégant
- Nom du fichier: `generate-haiku-YYYYMMDD-HHMMSS.md`

#### Exemple de Sortie
```markdown
# 🎵 Haikus Générés - Sélection Aléatoire
Généré: 31/01/2026 06:00:15

## 1. Abbey Road - The Beatles
```
Synergy of sound,
Harmonies traverse time,
Culture's heartbeat.
```
```

---

### 2. 📝 Exportation Collection en Markdown
**ID:** `export_collection_markdown`  
**Fréquence:** Quotidiennement à 8h00  
**Fichier:** `backend/app/services/scheduler_service.py` (ligne 367-410)

#### Fonctionnalités
- Export complet de votre collection en markdown
- Regroupement par artiste alphabétique
- Inclut titre, année, descriptions brèves
- Sauvegarder comme sauvegarde lisible
- Nom du fichier: `export-markdown-YYYYMMDD-HHMMSS.md`

#### Exemple de Sortie
```markdown
# 📚 Collection Complète
Exporté: 31/01/2026 08:00:15
Total albums: 247

## 🎤 The Beatles
- **Abbey Road** (1969)
  - Abbey Road is the seventeenth and final studio album...
- **Rubber Soul** (1965)
  - Rubber Soul is the third studio album...

## 🎤 Pink Floyd
- **The Wall** (1979)
  - The Wall is a double album...
```

---

### 3. 📊 Exportation Collection en JSON
**ID:** `export_collection_json`  
**Fréquence:** Quotidiennement à 10h00  
**Fichier:** `backend/app/services/scheduler_service.py` (ligne 413-462)

#### Fonctionnalités
- Export complet de votre collection en JSON structuré
- Inclusion de toutes les métadonnées (ID, titre, année, genre, etc.)
- Format machine-lisible pour intégrations tierces
- Inclut le nombre de pistes par album
- Nom du fichier: `export-json-YYYYMMDD-HHMMSS.json`

#### Exemple de Sortie
```json
{
  "export_date": "2026-01-31T10:00:15.123456",
  "total_albums": 247,
  "albums": [
    {
      "id": 1,
      "title": "Abbey Road",
      "year": 1969,
      "genre": "Rock",
      "artists": ["The Beatles"],
      "tracks_count": 17,
      "spotify_url": "https://open.spotify.com/album/..."
    }
  ]
}
```

---

## 📂 Répertoire de Sortie

Tous les fichiers générés sont sauvegardés dans:
```
AIME - AI Music Enabler/
└── Scheduled Output/
    ├── generate-haiku-20260131-060000.md
    ├── export-markdown-20260131-080000.md
    └── export-json-20260131-100000.json
```

### Format des Noms de Fichiers
- **Pattern:** `{task-name}-YYYYMMDD-HHMMSS.{extension}`
- **Exemple:** `generate-haiku-20260131-143022.md`
- **Avantages:**
  - Unicité garantie (date + heure précises)
  - Facile à trier chronologiquement
  - Identifie clairement le type de tâche

---

## 🎯 Configuration et Personnalisation

### Configuration Actuelle (config/app.json)
```json
{
  "scheduler": {
    "output_dir": "Scheduled Output",
    "tasks": [
      {
        "name": "generate_haiku",
        "enabled": true,
        "frequency": 1,
        "unit": "day"
      },
      {
        "name": "export_collection_markdown",
        "enabled": true,
        "frequency": 1,
        "unit": "day"
      },
      {
        "name": "export_collection_json",
        "enabled": true,
        "frequency": 1,
        "unit": "day"
      }
    ]
  }
}
```

### Personnaliser la Fréquence
Pour changer la fréquence d'une tâche:
1. Modifiez `frequency` et `unit` dans `config/app.json`
2. Redémarrez le backend
3. Les tâches s'ajusteront automatiquement

Exemple pour exécuter tous les 2 jours:
```json
{
  "name": "generate_haiku",
  "frequency": 2,
  "unit": "day"
}
```

Options supportées:
- `unit`: `"day"`, `"week"`, `"month"`
- `frequency`: nombre entier positif

---

## 🚀 Utilisation des Tâches

### Déclencher Manuellement via API

```bash
# Générer haikus
curl -X POST http://localhost:8000/api/v1/services/scheduler/trigger/generate_haiku_scheduled

# Exporter en markdown
curl -X POST http://localhost:8000/api/v1/services/scheduler/trigger/export_collection_markdown

# Exporter en JSON
curl -X POST http://localhost:8000/api/v1/services/scheduler/trigger/export_collection_json
```

### Vérifier l'État du Scheduler

```bash
curl http://localhost:8000/api/v1/services/scheduler/status
```

Réponse:
```json
{
  "running": true,
  "jobs": [
    {
      "id": "generate_haiku_scheduled",
      "name": "generate_haiku_scheduled",
      "next_run": "2026-02-01T06:00:00+00:00",
      "last_execution": "2026-01-31T06:00:15.123456"
    }
  ],
  "job_count": 7
}
```

---

## 📝 Tâches Existantes (Inchangées)

### Autres Tâches du Scheduler

| Tâche | Fréquence | Heure | Description |
|-------|-----------|-------|-------------|
| `daily_enrichment` | Quotidien | 2h | Enrichit 50 albums sans Spotify URL |
| `weekly_haiku` | Hebdomadaire | Dim 20h | Génère haiku basé sur écoutes 7 jours |
| `monthly_analysis` | Mensuel | 1er du mois 3h | Analyse patterns écoutes 30 jours |
| `optimize_ai_descriptions` | Toutes les 6h | - | Génère descriptions IA pour albums populaires |

---

## 🔧 Architecture Technique

### Fichiers Modifiés
- `backend/app/services/scheduler_service.py` (+250 lignes)
  - Ajout de 3 nouvelles méthodes async
  - Enregistrement des tâches avec CronTrigger
  - Mise à jour de la méthode `trigger_task()`

- `backend/app/api/v1/services.py` (documentation mise à jour)
  - Docstring du endpoint `/scheduler/trigger/{task_name}` enrichie

- `backend/__init__.py` (créé)
  - Package marker pour imports Python

### Nouvelles Dépendances
- `random` (lib std) - Sélection aléatoire
- `json` (lib std) - Sérialisation JSON
- `os` (lib std) - Gestion répertoires
- `datetime.timezone` (lib std) - Gestion timezone UTC

### Intégrations Existantes
- `APScheduler` - Scheduling des tâches
- Euria AI - Génération haikus
- SQLAlchemy - Requêtes base de données
- FastAPI - Endpoints manuels

---

## ⚙️ Horaires des Tâches Automatiques

### Timeline Quotidien Complet
```
02:00 → daily_enrichment
06:00 → generate_haiku_scheduled ✨ NOUVEAU
08:00 → export_collection_markdown ✨ NOUVEAU
10:00 → export_collection_json ✨ NOUVEAU
00:00, 06:00, 12:00, 18:00 → optimize_ai_descriptions

+ Schedules spécialisées:
- Dimanche 20h → weekly_haiku
- 1er du mois 3h → monthly_analysis
```

---

## 📊 Exemples de Fichiers Générés

### generate-haiku-20260131-060000.md
```markdown
# 🎵 Haikus Générés - Sélection Aléatoire

Généré: 31/01/2026 06:00:15

## 1. Thriller - Michael Jackson

```
Beats of the night call,
Darkness transforms to wonder,
Fear becomes feeling.
```

## 2. Hotel California - Eagles

```
Desert winds whisper,
Lost in luxury's embrace,
Check out never comes.
```
```

### export-markdown-20260131-080000.md
```markdown
# 📚 Collection Complète

Exporté: 31/01/2026 08:00:15
Total albums: 247

## 🎤 The Beatles
- **Abbey Road** (1969)
- **Rubber Soul** (1965)
- **Sgt. Pepper's Lonely Hearts Club Band** (1967)
```

### export-json-20260131-100000.json
```json
{
  "export_date": "2026-01-31T10:00:15.234567",
  "total_albums": 247,
  "albums": [
    {
      "id": 1,
      "title": "Abbey Road",
      "year": 1969,
      "genre": "Rock",
      "description": "Abbey Road is the seventeenth...",
      "spotify_url": "https://open.spotify.com/album/0ETFjACjubed9DA7PJ7Xp7",
      "artists": ["The Beatles"],
      "tracks_count": 17
    }
  ]
}
```

---

## 🐛 Dépannage

### Les fichiers ne sont pas générés
**Vérifications:**
1. Vérifier que le répertoire `Scheduled Output/` existe
2. Vérifier que la base de données contient des albums
3. Vérifier les logs du backend: `tail backend.log`
4. Vérifier que Euria AI est configuré pour les haikus

### Erreur: "Tâche inconnue"
**Solution:** Utiliser les ID exacts:
- `generate_haiku_scheduled` (pas `generate_haiku`)
- `export_collection_markdown`
- `export_collection_json`

### Les haikus ne génèrent pas
**Vérifications:**
1. Vérifier la configuration Euria AI dans `config/app.json`
2. Vérifier les variables d'env `EURIA_URL` et `EURIA_BEARER`
3. Tester l'API Euria directement

---

## 📈 Prochaines Améliorations Possibles

1. **Notifications** - Envoyer notifications au complétion des tâches
2. **Compression** - Zipper les fichiers après une certaine durée
3. **Fusion Périodique** - Fusionner les haikus de la semaine en un fichier unique
4. **Partage Cloud** - Uploade automatique vers cloud (Drive, OneDrive)
5. **Webhook** - Déclencher actions externes après génération
6. **Dashboard** - Afficher l'historique des exports générés

---

## 🎓 Notes de Développement

### Méthode `_generate_random_haikus()`
- Sélectionne 5 albums via `random.sample()`
- Génère haiku via `self.ai.generate_haiku()`
- Crée fichier markdown avec timestamp
- Gère les erreurs gracieusement avec fallback

### Méthode `_export_collection_markdown()`
- Récupère tous albums via `db.query(Album).all()`
- Groupe par artiste pour lisibilité
- Tronque descriptions à 100 caractères
- Format: # Titre, ## Artiste, - Album

### Méthode `_export_collection_json()`
- Structure JSON plate pour interopérabilité
- Inclut toutes les métadonnées essentielles
- Encodage UTF-8 avec indentation 2
- Supporte les caractères spéciaux français

### Timing CronTrigger
- `hour=6, minute=0` → 6h00 quotidien
- `hour=8, minute=0` → 8h00 quotidien  
- `hour=10, minute=0` → 10h00 quotidien

---

**Dernière mise à jour:** 31 Janvier 2026  
**Version:** AIME v4.2.0  
**Auteur:** AI Music Enabler Scheduler System  
