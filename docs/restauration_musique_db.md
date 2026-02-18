# Procédure de restauration de la base musique.db depuis une sauvegarde

1. Arrêtez l’application (backend) pour éviter tout accès concurrent à la base :
   
   docker-compose stop backend

2. Repérez le fichier de sauvegarde à restaurer dans le dossier data/db_backups/ (exemple : musique.db.2026-02-18_02-00-00.bak)

3. Sauvegardez la base actuelle (par précaution) :
   
   cp data/db/musique.db data/db/musique.db.sauvegarde_avant_restauration

4. Restaurez la sauvegarde choisie :
   
   cp data/db_backups/musique.db.<DATE>.bak data/db/musique.db

5. Redémarrez l’application :
   
   docker-compose start backend

6. Vérifiez le bon fonctionnement de l’application et l’intégrité des données.

**Remarque** : Cette procédure peut être adaptée pour d’autres environnements (Docker, local, serveur distant). Toujours vérifier les droits d’accès sur les fichiers.
