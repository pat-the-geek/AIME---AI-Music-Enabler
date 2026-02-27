# Procédure de restauration de la base musique.db depuis une sauvegarde

1. Arrêtez l’application (backend) pour éviter tout accès concurrent à la base :
   
   docker-compose stop backend

2. Repérez le fichier de sauvegarde à restaurer dans le dossier data/db_backups/ (exemple : musique.db.2026-02-18_02-00-00.bak)

3. Sauvegardez la base actuelle (par précaution) :
   
   cp data/db/musique.db data/db/musique.db.sauvegarde_avant_restauration

4. Supprimez les fichiers WAL et SHM éventuellement présents (évite les conflits de journal) :

   rm -f data/db/musique.db-wal data/db/musique.db-shm

5. Restaurez la sauvegarde choisie :
   
   cp data/db_backups/musique.db.<DATE>.bak data/db/musique.db

6. Redémarrez l'application :
   
   docker-compose start backend

7. Vérifiez le bon fonctionnement de l'application et l'intégrité des données :

   curl "http://localhost:8000/api/v1/collection/albums?page=1&page_size=1"

**Remarque** : Cette procédure peut être adaptée pour d'autres environnements (Docker, local, serveur distant). Toujours vérifier les droits d'accès sur les fichiers.

---

## ⚠️ Problème fréquent : décalage de schéma après restauration

Une sauvegarde ancienne peut manquer des colonnes ajoutées par des migrations récentes.  
**Symptôme :** L'API retourne une erreur `sqlite3.OperationalError: no such column: albums.xxx`.

**Solution :** Appliquer les colonnes manquantes manuellement (ou via Alembic).

### Colonnes connues ajoutées récemment

| Version | Table | Colonne | Commande SQL |
|---------|-------|---------|--------------|
| v4.7.0 | `albums` | `apple_music_url` | `ALTER TABLE albums ADD COLUMN apple_music_url VARCHAR(500);` |
| v4.7.5 | `albums` | `lastfm_url` | `ALTER TABLE albums ADD COLUMN lastfm_url VARCHAR(500);` |

**Exemple d'application via Docker :**
```bash
docker exec music-tracker-backend python -c "
import sqlite3
conn = sqlite3.connect('/app/data/db/musique.db')
cur = conn.cursor()
cur.execute(\"PRAGMA table_info(albums)\")
cols = [r[1] for r in cur.fetchall()]
if 'lastfm_url' not in cols:
    cur.execute('ALTER TABLE albums ADD COLUMN lastfm_url VARCHAR(500)')
    conn.commit()
    print('lastfm_url ajoutée')
else:
    print('lastfm_url déjà présente')
conn.close()
"
```
