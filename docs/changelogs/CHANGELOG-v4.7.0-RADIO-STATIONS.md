# Changelog - v4.7.0 - Détection des Stations de Radio

**Date:** 9 février 2026  
**Type:** Nouvelle fonctionnalité  
**Impact:** Tracker Roon + Tracker Last.fm

---

## 🎯 Vue d'ensemble

Ajout d'une **détection automatique et configurable des stations de radio** pour les trackers d'écoute. Cette fonctionnalité permet d'ignorer automatiquement les lectures provenant de stations de radio, gardant votre collection musicale propre et organisée.

---

## ✨ Nouvelles Fonctionnalités

### 📻 Détection automatique des stations de radio

Une nouvelle section `radio_stations` dans le fichier de configuration `config/app.json` permet de définir une liste de stations de radio à **ignorer automatiquement** :

```json
{
  "roon_tracker": {
    "enabled": true,
    "interval_seconds": 120,
    "listen_start_hour": 8,
    "listen_end_hour": 22,
    "radio_stations": [
      "RTS La Première",
      "RTS Couleur 3",
      "RTS Espace 2",
      "RTS Option Musique",
      "Radio Meuh",
      "Radio Nova"
    ]
  }
}
```

### 🔍 Smart Detection

La détection fonctionne sur plusieurs champs et formats :

- ✅ Correspondance exacte (case-insensitive)
- ✅ Correspondance partielle en préfixe  
- ✅ Format "Artiste - Titre" (Last.fm/Roon)
- ✅ Support des variantes de noms

### 🛠️ Configuration flexible

- ✅ Ajouter/retirer des stations dynamiquement
- ✅ Support illimité de stations
- ✅ Configuration centralisée dans `app.json`

---

## 🏗️ Implémentation Technique

### Nouveaux Fichiers

```
backend/app/utils/radio_station_detector.py
```

**Classe:** `RadioStationDetector`

```python
from app.utils.radio_station_detector import RadioStationDetector

# Initialiser le détecteur
detector = RadioStationDetector([
    "RTS La Première",
    "Radio Meuh"
])

# Vérifier si un track est une station
if detector.is_radio_station(track_data):
    print("📻 Ignorer ce track")
```

### Méthodes disponibles

| Méthode | Description |
|---------|-------------|
| `is_radio_station(track_data)` | Vérifie si un track est une station |
| `get_configured_stations()` | Retourne la liste des stations |
| `add_station(name)` | Ajoute une station |
| `remove_station(name)` | Retire une station |

### Intégration dans les Trackers

#### Roon Tracker
**Fichier:** `backend/app/services/roon_tracker_service.py`

- Import du detectoreur
- Initialisation avec configuration
- Vérification dans `_poll_roon()` avant `_save_track()`

#### Last.fm Tracker  
**Fichier:** `backend/app/services/tracker_service.py`

- Import du detecteur
- Initialisation avec configuration
- Vérification dans `_poll_lastfm()` avant `_save_track()`

---

## 📝 Configuration par défaut

```json
{
  "roon_tracker": {
    "radio_stations": [
      "RTS La Première",
      "RTS Couleur 3",
      "RTS Espace 2",
      "RTS Option Musique",
      "Radio Meuh",
      "Radio Nova"
    ]
  }
}
```

---

## 📊 Logging

Quand une station est détectée :

```
📻 Station de radio détectée dans le champ 'artist': RTS La Première
📻 Station de radio ignorée: RTS La Première - Émission musicale
```

---

## 📚 Documentation

- **[GUIDE-UTILISATEUR-TRACKER-CONFIGURATION.md](docs/guides/utilisateur/GUIDE-UTILISATEUR-TRACKER-CONFIGURATION.md)** - Guide complet avec exemples
- Mise à jour de [INDEX.md](docs/INDEX.md)
- Mise à jour de [README.md](docs/README.md)

---

## 🔑 Points Clés

### Avantages

✅ **Données propres:** Élimine les métadonnées radio inconsistantes  
✅ **Flexible:** Configuration simple et modifiable  
✅ **Non-invasif:** Aucun impact sur les données existantes  
✅ **Transparent:** Logs clairs des stations ignorées  
✅ **Unified:** Fonctionnalité cohérente sur Roon et Last.fm

### Comportement

1. Détection automatique au polling
2. Vérification contre la liste configurée
3. Ignorance du track (pas d'enregistrement en DB)
4. Log informatif dans les traces d'exécution

---

## 🧪 Tests

```bash
# Vérifier la syntaxe
python -m py_compile backend/app/utils/radio_station_detector.py

# Tester l'importation
python -c "from app.utils.radio_station_detector import RadioStationDetector; print('✅ OK')"
```

---

## 🔄 Compatibilité

- ✅ Rétrocompatible : liste vide = tous les tracks enregistrés
- ✅ Sans impact sur les trackers existants
- ✅ Fonctionne avec les deux trackers (Roon + Last.fm)

---

## 📋 Récapitulatif des Changements

| Fichier | Type | Description |
|---------|------|-------------|
| `config/app.json` | Config | Ajout section `radio_stations` |
| `backend/app/utils/radio_station_detector.py` | Nouveau | Classe détecteur |
| `backend/app/services/roon_tracker_service.py` | Modifié | Import + intégration du détecteur |
| `backend/app/services/tracker_service.py` | Modifié | Import + intégration du détecteur |
| `docs/guides/utilisateur/GUIDE-UTILISATEUR-TRACKER-CONFIGURATION.md` | Nouveau | Guide complet utilisateur |
| `docs/INDEX.md` | Modifié | Référence au nouveau guide |
| `docs/README.md` | Modifié | Navigation et références |

---

## 🚀 Migration depuis v4.6.0

### Aucune action requise

The configuration is automatically initialized with the default list of Swiss radio stations (RTS, Radio Meuh, Radio Nova).

If you want to modify the station list:

```bash
# 1. Edit config/app.json
code config/app.json

# 2. Modify the radio_stations array

# 3. Restart the backend
```

---

## ❓ FAQ

**Q: Où configurer les stations?**  
A: Dans `config/app.json`, section `roon_tracker.radio_stations`

**Q: Comment savoir si une station est ignorée?**  
A: Vérifiez les logs, vous verrez un message `📻 Station de radio détectée...`

**Q: Puis-je gérer différentes listes pour Roon et Last.fm?**  
A: Non, actuellement la même liste est utilisée pour les deux. Support future possible.

**Q: Les changements sont-ils appliqués immédiatement?**  
A: Non, il faut redémarrer le backend.

---

## 📞 Support

Pour des questions ou des améliorations:
- Voir [GUIDE-UTILISATEUR-TRACKER-CONFIGURATION.md](docs/guides/utilisateur/GUIDE-UTILISATEUR-TRACKER-CONFIGURATION.md)
- Consulter la documentation INDEX.md
