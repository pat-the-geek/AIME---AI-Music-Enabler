# 🚀 Guide d'Implémentation - Correction Discogs

## Résumé de la Correction

La collection Discogs contenait 235 albums mélangés avec 160 albums provenant des écoutes (Last.fm, Roon). Cette correction sépare complètement ces deux sources.

### État Final
- ✅ **235 albums Discogs** - Collection physique (Vinyle/CD/Digital)
- ✅ **160 albums d'écoutes** - Last.fm, Roon, Manual
- ✅ **100% validé** - Tous les supports corrects

---

## 📦 Fichiers à Déployer

### Code (Backend - CRITICAL)
```
backend/app/models/album.py                 ← MODIFIÉ
backend/app/api/v1/services.py              ← MODIFIÉ
backend/app/api/v1/collection.py            ← MODIFIÉ
backend/app/services/tracker_service.py     ← MODIFIÉ
backend/app/services/roon_tracker_service.py ← MODIFIÉ
```

### Scripts d'Installation
```
backend/migrate_add_source.py               ← À EXÉCUTER
backend/validate_correction.py              ← VALIDATION
backend/cleanup_check.py                    ← OPTIONAL
backend/init_db.py                          ← Si BD vierge
```

### Documentation
```
docs/CORRECTION-DISCOGS-SOURCE.md
docs/TYPES-SUPPORT.md
RAPPORT-CORRECTION-DISCOGS.md
CORRECTION-COMPLETE.md
CHECKLIST-CORRECTION.txt
```

---

## 🔧 Étapes d'Installation

### 1. Sauvegarder la BD (CRITIQUE)
```bash
cp data/musique.db data/musique.db.backup-$(date +%Y%m%d)
```

### 2. Déployer le code Python
```bash
# Copier les fichiers modifiés
cp app/models/album.py <destination>/
cp app/api/v1/services.py <destination>/
cp app/api/v1/collection.py <destination>/
cp app/services/tracker_service.py <destination>/
cp app/services/roon_tracker_service.py <destination>/
```

### 3. Exécuter la Migration
```bash
cd backend
python3 migrate_add_source.py ../data/musique.db
```

### 4. Valider le Résultat
```bash
python3 validate_correction.py ../data/musique.db
```

### 5. Redémarrer les Services
```bash
# Redémarrer le backend
docker-compose restart backend

# ou

systemctl restart aime-backend
```

---

## 🧪 Vérification Post-Installation

### 1. Vérifier les Endpoints
```bash
# Doit retourner UNIQUEMENT 235 albums Discogs
curl http://localhost:8000/api/v1/collection/albums

# Doit retourner 160 albums d'écoutes
curl http://localhost:8000/api/v1/collection/listenings

# Doit retourner les stats par source
curl http://localhost:8000/api/v1/collection/source-stats
```

### 2. Vérifier la BD
```bash
python3 validate_correction.py ../data/musique.db
# Doit afficher: ✅ Validation complétée avec succès!
```

### 3. Vérifier les Logs
```bash
# Chercher les logs de synchronisation Discogs
grep "source='discogs'" logs/backend.log

# Doit y avoir des entrées avec source='discogs'
```

---

## ⚠️ Points Critiques

### DO ✅
- ✅ Sauvegarder la BD avant migration
- ✅ Valider après migration
- ✅ Redémarrer le backend
- ✅ Tester les endpoints
- ✅ Vérifier les logs

### DON'T ❌
- ❌ Ne pas exécuter la migration deux fois
- ❌ Ne pas modifier les fichiers .py directement
- ❌ Ne pas supprimer album.py avant de copier le nouveau
- ❌ Ne pas faire de rollback sans restaurer la sauvegarde

---

## 🔄 Rollback (En Cas de Problème)

### Option 1: Restaurer la Sauvegarde
```bash
# Si l'installation a échoué
cp data/musique.db.backup-20260131 data/musique.db

# Restaurer les fichiers Python originaux
git checkout backend/app/models/album.py
git checkout backend/app/api/v1/services.py
# ... etc
```

### Option 2: Migration Inverse (Avancé)
```bash
# Supprimer la colonne source (déconseillé)
sqlite3 data/musique.db "ALTER TABLE albums DROP COLUMN source;"
```

---

## 📊 Qu'est-ce qui a Changé?

### Modèle Album
```python
# AVANT
class Album:
    id, title, year, support, discogs_id, ...

# APRÈS
class Album:
    id, title, year, support, source, discogs_id, ...
    #                          ^^^^^^ NOUVEAU
```

### API Response (Collection)
```json
// AVANT (395 albums mélangés)
{
  "items": [...],
  "total": 395
}

// APRÈS (235 albums Discogs uniquement)
{
  "items": [...],
  "total": 235
}
```

### Création d'Albums

**Discogs:**
```python
Album(source='discogs', support='Vinyle', discogs_id='123')
```

**Last.fm:**
```python
Album(source='lastfm', support=None)
```

**Roon:**
```python
Album(source='roon', support='Roon')
```

---

## 📈 Métriques de Succès

| Métrique | Avant | Après | ✓ |
|----------|-------|-------|---|
| Albums Discogs clairs | ❌ | 235 | ✓ |
| Albums écoutes clairs | ❌ | 160 | ✓ |
| Supports Discogs valides | ❌ | 100% | ✓ |
| Source identifiée | ❌ | 100% | ✓ |
| API /albums retourne | 395 | 235 | ✓ |
| API /listenings retourne | N/A | 160 | ✓ |

---

## 🆘 Troubleshooting

### Migration échoue
```
Erreur: "no such table: albums"
Solution: Exécuter init_db.py d'abord
  python3 init_db.py
```

### Validation échoue
```
Erreur: "Supports invalides trouvés"
Solution: Vérifier les supports Discogs
  python3 cleanup_check.py ../data/musique.db check
```

### API retourne 395 albums
```
Problème: Collection.py n'a pas été mis à jour
Solution: Vérifier que le filtre source='discogs' est présent
```

### Albums Discogs manquants
```
Problème: Nouvelle synchronisation Discogs
Solution: Le code ajoute automatiquement source='discogs'
```

---

## 🔗 Documentation Complète

- **CORRECTION-DISCOGS-SOURCE.md** - Détails techniques complets
- **TYPES-SUPPORT.md** - Guide des types de support valides
- **RAPPORT-CORRECTION-DISCOGS.md** - Rapport technique détaillé
- **CORRECTION-COMPLETE.md** - Vue d'ensemble complète

---

## 📞 Support

### Problèmes Courants

**Q: Comment vérifier que la correction a été appliquée?**
```bash
python3 backend/validate_correction.py data/musique.db
```

**Q: Comment restaurer la BD d'avant?**
```bash
cp data/musique.db.backup-YYYYMMDD data/musique.db
```

**Q: Faut-il re-synchroniser Discogs?**
- Non, la colonne `source` est automatiquement ajoutée aux nouveaux albums

**Q: Les albums d'écoutes sont perdus?**
- Non, ils sont toujours dans la BD, juste marqués avec `source != 'discogs'`

**Q: Puis-je fusionner les doublons?**
- Oui, utiliser `cleanup_check.py move` pour déplacer des albums

---

## ✅ Checklist Finale

Avant de considérer l'installation complète:

- [ ] Sauvegarde créée: `data/musique.db.backup-*`
- [ ] Code déployé: fichiers Python copiés
- [ ] Migration exécutée: `migrate_add_source.py` lancé
- [ ] Validation passée: `validate_correction.py` OK
- [ ] Backend redémarré
- [ ] Endpoints testés: `/albums`, `/listenings`, `/source-stats`
- [ ] Logs vérifiés: pas d'erreurs
- [ ] Documentation archivée

---

**Installation Status: Prête à déployer** ✅
