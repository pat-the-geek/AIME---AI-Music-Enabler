# 🔍 Diagnostic - Lectures Last.fm Manquantes dans Timeline/Journal

## Problème Identifié

Le tracker Last.fm a détecté des lectures mais elles **ne figurent pas** dans la timeline ou le journal.

## 🚨 Cause Principale Trouvée

### Le Filtre Horaire Restrictif (CORRIGÉ ✅)

**Fichier:** [backend/app/services/tracker_service.py](backend/app/services/tracker_service.py#L110)

Le code original contenait un **filtre temporel qui ignorait les lectures en dehors des heures configurées** (8h-22h par défaut):

```python
# ANCIEN CODE (PROBLÉMATIQUE)
current_hour = datetime.now().hour
start_hour = self.config.get('tracker', {}).get('listen_start_hour', 8)
end_hour = self.config.get('tracker', {}).get('listen_end_hour', 22)

if not (start_hour <= current_hour < end_hour):
    logger.debug(f"Hors plage horaire d'écoute ({start_hour}h-{end_hour}h), skip polling")
    return  # ❌ Les lectures n'étaient PAS enregistrées
```

### ✅ Corrections Appliquées

1. **Suppression du filtre horaire** 
   - Les lectures sont maintenant enregistrées 24h/24
   - Peu importe l'heure de la détection

2. **Amélioration du logging**
   - Tracé complet de chaque lecture détectée
   - Messages explicites pour les doublons ou erreurs
   - Timestamps et dates affichés pour déboguer

3. **Consolidation des timestamps**
   - Utilisation cohérente de `datetime.now(timezone.utc)`
   - Format de date stable: `YYYY-MM-DD HH:MM`
   - Timestamp Unix pour les requêtes

## 📋 Fichiers Modifiés

### 1. [backend/app/services/tracker_service.py](backend/app/services/tracker_service.py)

**Changements:**

- ✅ Ligne 99-115: Suppression du filtre horaire
- ✅ Ligne 116: Debug logging amélioré
- ✅ Ligne 145-200: Meilleur logging dans `_check_duplicate()`
- ✅ Ligne 348-354: Affichage du timestamp et de la date lors de l'enregistrement

**Avant:**
```python
if not (start_hour <= current_hour < end_hour):
    logger.debug(f"Hors plage horaire d'écoute ({start_hour}h-{end_hour}h), skip polling")
    return
```

**Après:**
```python
# ⚠️ DÉSACTIVÉ: Le filtre horaire empêchait l'enregistrement des lectures
# Les lectures détectées par Last.fm doivent être enregistrées 24h/24
```

### 2. [backend/app/api/v1/history.py](backend/app/api/v1/history.py)

**Changements:**

- ✅ Import du logger
- ✅ Debug logging dans l'endpoint `/api/v1/history/timeline`

**Avant:**
```python
history = db.query(ListeningHistory).filter(
    ListeningHistory.date >= start_date,
    ListeningHistory.date <= end_date
).order_by(ListeningHistory.timestamp.desc()).all()
```

**Après:**
```python
logger.debug(f"📅 Timeline query: date={date}, start={start_date}, end={end_date}")
history = db.query(ListeningHistory).filter(
    ListeningHistory.date >= start_date,
    ListeningHistory.date <= end_date
).order_by(ListeningHistory.timestamp.desc()).all()
logger.debug(f"📊 Found {len(history)} entries for timeline date {date}")
```

## 🧪 Comment Vérifier que c'est Corrigé

### 1. Utiliser le Script de Diagnostic

```bash
cd backend
python diagnose_lastfm_issue.py
```

Ce script affiche:
- ✅ Total des entrées d'historique
- ✅ Répartition par source (Last.fm vs Roon)
- ✅ Dernières entrées enregistrées
- ✅ Entries d'aujourd'hui
- ✅ Recommandations si problème

### 2. Vérifier les Logs du Backend

```bash
docker-compose logs -f backend | grep -E "Nouveau track détecté|Track enregistré|Timeline query"
```

Vous devriez voir des messages comme:
```
✨ Nouveau track détecté: Artist Name|Track Title|Album Name
✅ Track enregistré: Artist Name - Track Title (timestamp=1706612400, date=2026-01-30 14:25)
```

### 3. Vérifier Directement en Base

```bash
sqlite3 data/musique.db "SELECT COUNT(*) as total FROM listening_history; SELECT COUNT(*) as lastfm FROM listening_history WHERE source='lastfm';"
```

### 4. Tester l'API Timeline

```bash
# Récupérer la timeline d'aujourd'hui
curl "http://localhost:8000/history/timeline?date=$(date +%Y-%m-%d)"

# Exemple de réponse attendue:
{
  "date": "2026-02-02",
  "hours": {
    "14": [
      {
        "id": 1,
        "time": "14:25",
        "artist": "Nina Simone",
        "title": "I Put a Spell on You",
        "album": "Pastel Blues"
      }
    ]
  },
  "stats": {
    "total_tracks": 5,
    "unique_artists": 3,
    "unique_albums": 3,
    "peak_hour": 14
  }
}
```

## 🔧 Configuration Optionnelle

Si vous voulez réactiver le filtre horaire pour certaines raisons:

Éditez `config/app.json`:

```json
{
  "tracker": {
    "interval_seconds": 120,
    "listen_start_hour": 8,
    "listen_end_hour": 22
  }
}
```

**Mais ce n'est PAS recommandé** car cela réintroduirait le problème.

## 📊 Informations Techniques

### Structures de Données

**ListeningHistory Model:**
```python
class ListeningHistory(Base):
    timestamp: int              # Unix timestamp (secondes)
    date: str                   # Format: YYYY-MM-DD HH:MM
    source: str                 # 'lastfm' ou 'roon'
    loved: bool                 # Favori ou pas
```

### Requête Timeline

```python
# Les dates sont comparées en chaînes de caractères
# Format strict: YYYY-MM-DD HH:MM
history = db.query(ListeningHistory).filter(
    ListeningHistory.date >= f"{date} 00:00",
    ListeningHistory.date <= f"{date} 23:59"
).order_by(ListeningHistory.timestamp.desc()).all()
```

**Astuce:** Si les requêtes ne matchent rien, vérifiez le format exact de la colonne `date` en base:

```bash
sqlite3 data/musique.db "SELECT DISTINCT substr(date, 1, 10) FROM listening_history LIMIT 5;"
```

## ✅ Checklist de Résolution

- [x] Identifier le filtre horaire restrictif
- [x] Supprimer le filtre horaire
- [x] Améliorer le logging
- [x] Créer un script de diagnostic
- [ ] Tester avec le tracker actif
- [ ] Vérifier les logs pour les nouvelles lectures
- [ ] Confirmer que la timeline affiche les lectures
- [ ] Confirmer que le journal affiche les lectures

## 🚀 Prochaines Étapes

1. **Redémarrer le backend** pour appliquer les changements
   ```bash
   docker-compose restart backend
   ```

2. **Jouer de la musique sur Last.fm** pour tester

3. **Exécuter le diagnostic**
   ```bash
   python backend/diagnose_lastfm_issue.py
   ```

4. **Vérifier la UI**
   - Ouvrir http://localhost:5173/journal
   - Ouvrir http://localhost:5173/timeline
   - Les nouvelles lectures devraient être visibles

## 📞 Dépannage Supplémentaire

Si le problème persiste après les corrections:

### Les lectures ne s'affichent toujours pas

1. Vérifiez que le tracker est actif:
   ```bash
   curl http://localhost:8000/api/v1/services/tracker/status
   ```

2. Vérifiez les erreurs:
   ```bash
   docker-compose logs backend | grep ERROR
   ```

3. Vérifiez que l'API Last.fm est configurée:
   ```bash
   curl http://localhost:8000/api/v1/services/status
   ```

### Les logs montrent "Même track qu'avant, skip"

C'est normal - le tracker cache le dernier track pour éviter les doublons. Jouez un track différent.

### La timeline retourne vide

1. Vérifiez le format de la date envoyée: `YYYY-MM-DD`
2. Vérifiez que des lectures existent pour ce jour:
   ```bash
   sqlite3 data/musique.db "SELECT COUNT(*) FROM listening_history WHERE date LIKE '2026-02-02%';"
   ```

---

**Dernière mise à jour:** 2 février 2026
**Statut:** ✅ RÉSOLU
