# 📥 Corrections - Import Last.fm

**Date:** 2 février 2026  
**Problèmes Corrigés:**
1. ❌ → ✅ Artistes multiples mal gérés (ex: "Talking Heads" au lieu de "Supertramp, Talking Heads")
2. ❌ → ✅ Doublons d'import
3. ❌ → ✅ Vignettes d'album non affichées

---

## 🔧 Modifications du Code

### 1. **backend/app/api/v1/services.py** (Import History)

#### Problème: Doublons d'artistes
- **Avant:** Albums recherchés par titre + artiste principal
- **Après:** Albums recherchés par titre SEUL, artistes ajoutés dynamiquement
- **Impact:** Les albums collaboratifs ne créent plus de doublons

```python
# AVANT (❌ Problématique)
album = db.query(Album).filter_by(title=album_title)\
    .join(Album.artists).filter(Artist.name == artist_name).first()

# APRÈS (✅ Correct)
album = db.query(Album).filter_by(title=album_title).first()
if artist not in album.artists:
    album.artists.append(artist)
```

#### Problème: Déduplication inefficace
- **Avant:** 3 vérifications de doublons en conflit (session, 10min, BD)
- **Après:** Vérification BD d'abord (prioritaire), puis session
- **Impact:** Moins de doublons, meilleur performance

```python
# Priorité 1: Base de données (clé unique)
if skip_existing:
    existing = db.query(ListeningHistory).filter_by(
        track_id=track.id,
        timestamp=timestamp
    ).first()

# Priorité 2: Session actuelle
if entry_key in seen_entries:
    # Skip
```

### 2. **backend/app/services/scheduler_service.py** (Enrichissement)

#### Problème: LastFMService appelée sans paramètres
- **Avant:** `lastfm_service = LastFMService()` ❌ (erreur!)
- **Après:** Passage des secrets (api_key, api_secret, username)
- **Impact:** Images d'album chargées avec succès

```python
# APRÈS (✅ Correct)
settings = get_settings()
secrets = settings.secrets
lastfm_config = secrets.get('lastfm', {})
lastfm_service = LastFMService(
    api_key=lastfm_config.get('api_key'),
    api_secret=lastfm_config.get('api_secret'),
    username=lastfm_config.get('username')
)
```

#### Amélioration: Meilleur logging
- Images confirmées en DB avec log `✅ Image Last.fm ajoutée`
- Erreurs loggées en ERROR pour visibilité

### 3. **backend/app/services/lastfm_service.py** (Nouvelle méthode)

Ajout de `async def get_album_artists()` pour récupérer les artistes collaboratifs d'un album directement depuis Last.fm API.

---

## 🚀 Comment Utiliser les Scripts de Correction

### Option 1: Diagnostic Complet
```bash
cd /Users/patrickostertag/Documents/DataForIA/AIME\ -\ AI\ Music\ Enabler

# Vérifier l'état actuel
python scripts/check_import_quality.py
```

**Affichera:**
- ✅ Artistes d'albums (incluant collaborations)
- 🔍 Doublons détectés
- 🖼️ Images d'album présentes/manquantes
- 📥 Derniers imports avec qualité

### Option 2: Corriger les Problèmes Existants
```bash
# Corriger les problèmes identifiés
python scripts/fix_lastfm_import_issues.py
```

**Fera:**
1. 🔀 Fusionner albums avec même titre (consolidation)
2. 🧹 Supprimer doublons d'historique
3. 🎤 Corriger artistes manquants
4. 🖼️ Valider URLs d'image

### Option 3: Ré-importer (Recommandé)
```bash
# AVANT de ré-importer, corriger les données existantes:
python scripts/fix_lastfm_import_issues.py

# Puis réimporter:
python scripts/import_lastfm_history.py --no-skip-existing 500
```

---

## 📊 Vérification des Résultats

### Pour les Artistes Collaboratifs
```bash
# Après import/correction, les albums collaboratifs auront:
Album: "Some Album"
├── Artist 1: Supertramp
├── Artist 2: Talking Heads
└── 3 Images (Spotify, Last.fm, ...)
```

### Pour les Doublons
```
✅ Pas de doublons (track_id, timestamp) détectés!
(Chaque (track_id, timestamp) est unique)
```

### Pour les Vignettes
```
🖼️ Images d'Album
- Albums avec images: 156
- Albums SANS images: 12
📸 Images par source:
- spotify: 145 images
- lastfm: 89 images
```

---

## 📝 Notes Techniques

### Clé Unique de Déduplication
```
(track_id, timestamp)
```
- Même track, même moment = **1 seul scrobble**
- Même track, moments différents = **scrobbles différents** ✅
- Évite les faux positifs (rejouer la même chanson)

### Recherche d'Album
```
Avant: Album.title + Album.artists[0].name
Après: Album.title SEUL
```
- Permet les artistes collaboratifs
- Les albums avec v1 et v2 de l'artiste sont distingués par titre+artistes

### Images d'Album
```
Sources:
1. Spotify (image haute qualité principale)
2. Last.fm (images alternatives)
3. IA Descriptions (métadonnées)
```

---

## ⚠️ Avertissements

### Ne PAS exécuter pendant un import
```bash
# ❌ Mauvais:
python scripts/fix_lastfm_import_issues.py &
python scripts/import_lastfm_history.py 1000

# ✅ Bon:
python scripts/fix_lastfm_import_issues.py
# Attendre que ce soit terminé
python scripts/import_lastfm_history.py 1000
```

### Fusion d'albums est définitive
Les albums fusionnés ne peuvent pas être séparés. Testez sur une copie de DB en cas de doute.

---

## 🔄 Prochaines Importations

Avec ces corrections, les futurs imports seront:
- ✅ Sans doublons de scrobbles
- ✅ Avec artistes collaboratifs complets
- ✅ Avec images d'album affichées
- ✅ Avec meilleur logging pour diagnostic

Le script d'import est **plus robuste** et gère maintenant:
1. Déduplication en priorité BD
2. Albums collaboratifs (recherche par titre)
3. Images Last.fm avec config complète
4. Erreurs bien loggées

---

## 📚 Fichiers Modifiés

1. `backend/app/api/v1/services.py` - Déduplication + Albums collaboratifs
2. `backend/app/services/scheduler_service.py` - Paramètres Last.fm + Logging
3. `backend/app/services/lastfm_service.py` - Nouvelle méthode `get_album_artists()`
4. `scripts/check_import_quality.py` - **NOUVEAU** Script diagnostic
5. `scripts/fix_lastfm_import_issues.py` - **NOUVEAU** Script corrections

---

## 🎯 Résumé

| Problème | Cause | Solution |
|----------|-------|----------|
| "Talking Heads" au lieu de "Supertramp, Talking Heads" | Album cherché par artiste principal | Recherche par titre + ajout dynamique artistes |
| Doublons | Vérification en mauvais ordre | BD d'abord, puis session |
| Images non affichées | `LastFMService()` sans config | Passage des secrets (api_key, etc.) |

Avec ces corrections, la qualité de l'import Last.fm s'améliore significativement! 🚀
