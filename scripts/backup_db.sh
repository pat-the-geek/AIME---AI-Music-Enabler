#!/bin/bash
# Sauvegarde automatique de la base musique.db avec horodatage
# À placer dans ./scripts/backup_db.sh

BACKUP_DIR="$(dirname "$0")/../data/db_backups"
DB_FILE="$(dirname "$0")/../data/db/musique.db"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/musique.db.$DATE.bak"

mkdir -p "$BACKUP_DIR"
if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_FILE"
    echo "Sauvegarde créée : $BACKUP_FILE"
else
    echo "Fichier $DB_FILE introuvable. Sauvegarde annulée."
    exit 1
fi
