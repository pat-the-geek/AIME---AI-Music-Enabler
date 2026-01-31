#!/bin/bash
# Script de migration manuelle pour ajouter la colonne 'source' à la table albums

# Récupérer le chemin de la base de données
DB_PATH="${1:-data/music_tracker.db}"

if [ ! -f "$DB_PATH" ]; then
    echo "❌ Base de données non trouvée: $DB_PATH"
    exit 1
fi

echo "📝 Début de la migration..."
echo "Base de données: $DB_PATH"

# Appliquer les migrations
sqlite3 "$DB_PATH" << 'EOF'

-- 1. Ajouter la colonne source si elle n'existe pas
ALTER TABLE albums ADD COLUMN source TEXT DEFAULT 'manual' NOT NULL;

-- 2. Créer l'index sur la colonne source
CREATE INDEX IF NOT EXISTS idx_albums_source ON albums(source);

-- 3. Mettre à jour les albums existants:
--    - Albums avec discogs_id -> discogs
UPDATE albums 
SET source = 'discogs' 
WHERE discogs_id IS NOT NULL AND source = 'manual';

--    - Albums avec support="Roon" -> roon
UPDATE albums 
SET source = 'roon' 
WHERE support = 'Roon' AND source = 'manual';

-- 4. Corriger les supports invalides pour les albums Discogs
--    Albums avec support autre que Vinyle/CD/Digital -> NULL (nettoyage)
UPDATE albums 
SET support = NULL
WHERE source = 'discogs'
AND support IS NOT NULL
AND support NOT IN ('Vinyle', 'Vinyl', 'CD', 'Digital', 'Cassette', 'Unknown');

-- Afficher les résumés
SELECT 'Albums par source:' as info;
SELECT source, COUNT(*) as count FROM albums GROUP BY source;

SELECT '' as blank;
SELECT 'Albums Discogs par support:' as info;
SELECT support, COUNT(*) as count FROM albums WHERE source = 'discogs' GROUP BY support;

SELECT '' as blank;
SELECT '✅ Migration complétée avec succès!' as status;

EOF

echo "✅ Migration terminée!"
