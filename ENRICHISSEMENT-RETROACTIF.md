# Enrichissement rétroactif des albums Last.fm

## Objectif

Mettre à jour tous les albums déjà importés depuis Last.fm avec les informations Spotify (URLs) qui manquent.

## Contexte

Après les modifications récentes, le tracker Last.fm enrichit automatiquement les nouveaux albums avec :
- ✅ URL Spotify
- ✅ Images Spotify
- ✅ Images Last.fm
- ✅ Description IA Euria

Cependant, les albums importés **avant** ces modifications n'ont pas ces enrichissements. Ce guide explique comment les ajouter rétroactivement.

## Méthodes disponibles

### Méthode 1 : Script Python (Recommandé)

Le script `enrich_spotify.py` permet d'enrichir tous les albums par lots.

#### Utilisation de base

```bash
# Depuis le dossier du projet
cd /Users/patrickostertag/Documents/DataForIA/AIME\ -\ AI\ Music\ Enabler

# Enrichir par lots de 20, pause 1s, maximum 5 lots (100 albums)
python scripts/enrich_spotify.py

# Enrichir par lots de 50, pause 2s, maximum 10 lots
python scripts/enrich_spotify.py 50 2 10

# Enrichir TOUS les albums sans limite (lots de 50, pause 2s)
python scripts/enrich_spotify.py 50 2 0
```

#### Arguments du script

```
python scripts/enrich_spotify.py [batch_size] [pause_seconds] [max_batches]
```

- **batch_size** : Nombre d'albums par lot (défaut: 20)
- **pause_seconds** : Pause entre les lots en secondes (défaut: 1)
- **max_batches** : Nombre maximum de lots (défaut: 5, 0 = illimité)

#### Exemples

```bash
# Enrichissement rapide de 100 albums (5 lots de 20)
python scripts/enrich_spotify.py

# Enrichissement de tous les albums, lots de 30, pause 1.5s
python scripts/enrich_spotify.py 30 1.5 0

# Test sur 2 lots seulement
python scripts/enrich_spotify.py 10 1 2
```

#### Sortie du script

```
============================================================
🎵 ENRICHISSEMENT SPOTIFY
============================================================

📊 Total albums dans la base: 487

📦 Traitement par lots de 50 albums
⏸️  Pause de 2s entre les lots
♾️  Sans limite de lots (tous les albums)

Démarrage de l'enrichissement Spotify...

📦 Lot #1
   ✅ 50 albums traités
   🎵 45 Spotify ajoutés | ❌ 5 erreurs
   💤 Pause de 2s...

📦 Lot #2
   ✅ 50 albums traités
   🎵 48 Spotify ajoutés | ❌ 2 erreurs
   ...

============================================================
📊 RÉSULTATS FINAUX
============================================================
🎵 Spotify URLs ajoutées: 423
❌ Erreurs totales: 12
📦 Lots traités: 10
============================================================
```

### Méthode 2 : API directe

Vous pouvez aussi utiliser l'endpoint API directement.

```bash
# Enrichir 20 albums
curl -X POST "http://localhost:8000/api/v1/services/spotify/enrich-all?limit=20"

# Enrichir 100 albums
curl -X POST "http://localhost:8000/api/v1/services/spotify/enrich-all?limit=100"

# Enrichir TOUS les albums (attention, peut être long!)
curl -X POST "http://localhost:8000/api/v1/services/spotify/enrich-all?limit=0"
```

## Recommandations

### Pour un enrichissement complet

Si vous avez beaucoup d'albums (> 500), procédez par étapes :

1. **Test initial** (vérifier que tout fonctionne) :
   ```bash
   python scripts/enrich_spotify.py 10 1 2
   ```

2. **Enrichissement progressif** :
   ```bash
   # Premier lot de 200 albums
   python scripts/enrich_spotify.py 50 2 4
   
   # Vérifier les résultats, puis continuer
   python scripts/enrich_spotify.py 50 2 0
   ```

3. **Enrichissement complet d'un coup** (si vous êtes sûr) :
   ```bash
   python scripts/enrich_spotify.py 50 2 0
   ```

### Gestion des erreurs

Certains albums peuvent ne pas être trouvés sur Spotify pour diverses raisons :
- Nom d'artiste ou d'album trop différent
- Album non disponible sur Spotify
- Erreurs de recherche temporaires

C'est normal d'avoir quelques erreurs. Le script continue malgré les erreurs.

### Optimisation

- **batch_size** : Plus grand = plus rapide, mais plus de risques de rate limiting
  - Recommandé : 20-50
- **pause_seconds** : Plus long = plus respectueux de l'API
  - Recommandé : 1-2 secondes

## Vérification des résultats

Après l'enrichissement, vérifiez dans l'interface :

1. **Journal** : Les badges 🎵 devraient apparaître sur les écoutes
2. **Timeline** : Idem, badges 🎵 et 📀 visibles
3. **Collection** : Ouvrir un album → vérifier le bouton "🎵 Écouter sur Spotify"

Vous pouvez aussi vérifier en base de données :

```bash
# Ouvrir la console SQLite
sqlite3 backend/data/aime.db

# Compter les albums avec Spotify
SELECT COUNT(*) FROM albums WHERE spotify_url IS NOT NULL;

# Compter les albums sans Spotify
SELECT COUNT(*) FROM albums WHERE spotify_url IS NULL;

# Quitter
.quit
```

## Enrichissement automatique futur

Tous les **nouveaux** albums détectés via le tracker Last.fm seront automatiquement enrichis avec l'URL Spotify. Vous n'avez besoin de lancer ce script qu'une seule fois pour rattraper l'historique.

## Troubleshooting

### Le script ne trouve rien

- Vérifier que le backend est lancé : `http://localhost:8000`
- Vérifier les credentials Spotify dans `config/secrets.json`

### Beaucoup d'erreurs

- Certains albums ne sont vraiment pas sur Spotify
- Si > 50% d'erreurs, vérifier la configuration Spotify

### Le script est trop lent

- Augmenter `batch_size` : `python scripts/enrich_spotify.py 100 2 0`
- Réduire `pause_seconds` (attention au rate limiting)

### Le script s'arrête

- Vérifier les logs du backend
- Relancer le script, il reprendra où il s'est arrêté (seuls les albums sans URL sont traités)

## Note sur Discogs

Les URLs Discogs ne peuvent **pas** être récupérées automatiquement pour les albums Last.fm, car :
- Discogs n'est pas une source de streaming
- Les URLs Discogs proviennent uniquement de votre collection Discogs synchronisée
- Seuls les albums importés via la synchronisation Discogs auront une URL Discogs

Pour avoir les URLs Discogs, utilisez la synchronisation Discogs normale.
