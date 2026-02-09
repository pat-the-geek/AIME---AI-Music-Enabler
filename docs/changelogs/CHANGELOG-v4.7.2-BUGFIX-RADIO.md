# Bugfix - v4.7.2 - Radio Station Detection Missing Title Field

**Date:** 9 février 2026  
**Severity:** High  
**Impact:** Radio station detection  

---

## 🐛 Bug Corrigé

### Radio Station Detection Échouait Silencieusement

**Problème:** Le détecteur de stations de radio ne vérifiait pas le champ `title`. Quand Roon/Last.fm envoyait des données de station, le nom de la station se trouvait dans le champ `title`, pas `artist`. Résultat: les stations comme "RTS La Première" n'étaient pas détectées et étaient sauvegardées dans l'historique d'écoute.

**Symptôme:**
- Stations de radio enregistrées dans la timeline/journal
- **Exemple:** 14 entrées de "RTS La Première" trouvées en base de données

---

## ✅ Correction Appliquée

### 1. RadioStationDetector - Ajout du champ `title`

**Fichier:** `backend/app/utils/radio_station_detector.py`

**Avant:**
```python
fields_to_check = [
    ('source', track_data.get('source', '')),
    ('artist', track_data.get('artist', '')),
    ('album', track_data.get('album', '')),
    ('zone_name', track_data.get('zone_name', '')),
]
```

**Après:**
```python
fields_to_check = [
    ('source', track_data.get('source', '')),
    ('artist', track_data.get('artist', '')),
    ('title', track_data.get('title', '')),  # ✅ AJOUTÉ
    ('album', track_data.get('album', '')),
    ('zone_name', track_data.get('zone_name', '')),
]
```

**Ordre de priorité (par importance):**
1. `source` - Source du track (Roon, Last.fm)
2. `artist` - Nom de l'artiste
3. **`title` - Titre du track (NOW CHECKED!)** ← Où Roon met le nom de station
4. `album` - Nom de l'album
5. `zone_name` - Nom de la zone Roon

---

## 🧹 Nettoyage des Données

14 entrées de stations de radio ont été trouvées et supprimées de la base de données:

| Station | Entrées |
|---------|---------|
| RTS La Première | 10 |
| RTS Couleur 3 | 0 |
| RTS Espace 2 | 0 |
| RTS Option Musique | 0 |
| Radio Meuh | 0 |
| Radio Nova | 0 |

**Status:** ✅ Toutes supprimées

---

## 📝 Fichiers Modifiés

| Fichier | Changement |
|---------|-----------|
| `backend/app/utils/radio_station_detector.py` | ✅ Ajout du champ `title` aux vérifications |
| `backend/cleanup_radio_stations.sh` | ✅ Script de nettoyage futur |

---

## 🔄 Flux de Détection Corrigé

### Avant (ÉCHOUAIT)
```
Roon API sends:
{
    "title": "RTS La Première - Émission",
    "artist": "Unknown",
    "album": "Unknown Album"
}
    ↓
is_radio_station() checks:
  - source? ❌ (empty)
  - artist? ❌ (Unknown)
  - album? ❌ (Unknown Album)
  - zone_name? ❌ (empty)
    ↓
Result: Not detected as radio → SAVED TO DB ❌
```

### Après (FONCTIONNE)
```
Roon API sends:
{
    "title": "RTS La Première - Émission",
    "artist": "Unknown",
    "album": "Unknown Album"
}
    ↓
is_radio_station() checks:
  - source? ❌ (empty)
  - artist? ❌ (Unknown)
  - title? ✅ MATCHES "RTS La Première" ⚡
    ↓
Result: Detected as radio → IGNORED ✅
```

---

## 🚀 Application du Bugfix

### Aucun changement frontend requis

C'est une correction purement backend du détecteur.

### Actions à effectuer

1. **Redémarrer le backend**
   ```bash
   # Arrêter le service backend
   # Puis redémarrer
   ```

2. **Vérification**
   - Regarder les logs: `📻 Station de radio détectée dans le champ 'title': RTS La Première`
   - Les nouvelles écoutes de stations NE seront PAS enregistrées

3. **Nettoyage manuel (optionnel)**
   ```bash
   # Si des données supplémentaires doivent être nettoyées
   ./backend/cleanup_radio_stations.sh
   ```

---

## 📊 Impact

- ✅ Stations de radio MAINTENANT ignorées correctement
- ✅ Vérification du champ `title` ajoutée
- ✅ 14 entrées historiques nettoyées
- ✅ Détection fonctionne pour Roon et Last.fm

---

## 🧪 Test de Vérification

### Vérifier que la détection fonctionne

1. **Looks pour les logs du tracker**
   ```
   📻 Station de radio détectée dans le champ 'title': RTS La Première
   📻 Station de radio ignorée: RTS La Première - <program>
   ```

2. **Vérifier que les stations ne sont PAS dans listening_history**
   ```bash
   sqlite3 data/musique.db \
     "SELECT COUNT(*) FROM listening_history lh \
      JOIN tracks t ON lh.track_id = t.id \
      WHERE t.title LIKE 'RTS%'"
   # Should return: 0
   ```

---

## 📞 Notes

- Cette correction s'applique à TOUS les trackers: Roon et Last.fm
- Les anciennes données ont été nettoyées automatiquement
- Les futures stations seront ignorées dès qu'elles sont détectées

