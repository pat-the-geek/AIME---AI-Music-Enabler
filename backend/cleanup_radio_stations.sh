#!/bin/bash
# Clean up radio station data from listening history

DB_PATH="data/musique.db"

echo "🧹 Nettoyage des stations de radio dans la base de données..."
echo ""

# Stations à nettoyer
STATIONS=('RTS La Première' 'RTS Couleur 3' 'RTS Espace 2' 'RTS Option Musique' 'Radio Meuh' 'Radio Nova' 'Lofi Hip Hop Radio')

# Compter avant
BEFORE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM listening_history lh JOIN tracks t ON lh.track_id = t.id WHERE t.title IN ($(printf \"'%s'\" "${STATIONS[@]}" | sed 's/ /,/g'));")

echo "📊 Avant nettoyage: $BEFORE entrées"

# Supprimer les entrées
for station in "${STATIONS[@]}"; do
    echo "  ⏳ Suppression: '$station'"
    sqlite3 "$DB_PATH" "DELETE FROM listening_history WHERE track_id IN (SELECT id FROM tracks WHERE title = '$station');"
done

# Supprimer les tracks orphelines (pas d'écoute)
ORPHANED=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM tracks t WHERE NOT EXISTS (SELECT 1 FROM listening_history lh WHERE lh.track_id = t.id) AND t.title IN ($(printf \"'%s'\" "${STATIONS[@]}" | sed 's/ /,/g'));")
echo ""
echo "  ⏳ Suppression de $ORPHANED tracks orphelines"
sqlite3 "$DB_PATH" "DELETE FROM tracks WHERE NOT EXISTS (SELECT 1 FROM listening_history lh WHERE lh.track_id = t.id) AND title IN ($(printf \"'%s'\" "${STATIONS[@]}" | sed 's/ /,/g'));"

# Supprimer les albums vides (optionnel)
sqlite3 "$DB_PATH" "DELETE FROM albums WHERE NOT EXISTS (SELECT 1 FROM tracks t WHERE t.album_id = albums.id);"

# Compter après
AFTER=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM listening_history lh JOIN tracks t ON lh.track_id = t.id WHERE t.title IN ($(printf \"'%s'\" "${STATIONS[@]}" | sed 's/ /,/g'));")

echo ""
echo "✅ Nettoyage complété:"
echo "   Avant: $BEFORE entrées"
echo "   Après: $AFTER entrées"
echo ""
echo "📝 Exécution ANALYZE pour optimiser la base..."
sqlite3 "$DB_PATH" "ANALYZE;"
echo "✅ Optimisation complétée"
