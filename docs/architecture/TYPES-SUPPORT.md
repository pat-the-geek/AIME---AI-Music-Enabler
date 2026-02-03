# Types de Support par Source

## 📁 Discogs Collection (source='discogs')

**Types valides (physiques et numériques):**

| Support | Description | Exemple |
|---------|-------------|---------|
| `Vinyle` | Disques vinyle 33/45/78 tours | LP, EP, Single |
| `CD` | Disques compacts | CD-DA, CD-R |
| `Digital` | Fichiers numériques | MP3, FLAC, WAV |
| `Cassette` | Cassettes audio | Compact cassette |
| `NULL` | Format non spécifié | Inconnu |

**Types INVALIDES (rejetés lors de la synchronisation):**
- ❌ `Roon` (c'est une source, pas un support)
- ❌ `streaming` (non physique)
- ❌ `Unknown` en majuscules (normalisé en `Unknown`)
- ❌ N'importe quel autre format

---

## 🎵 Last.fm (source='lastfm')

**Types acceptés:**
- Tous les types (historique d'écoute, pas de contrainte)
- Support généralement `NULL` (non applicable)

---

## 🎧 Roon (source='roon')

**Types acceptés:**
- `Roon` (spécifique à la source Roon)
- Support généralement `Roon` ou `NULL`

---

## 📚 Manual (source='manual')

**Types acceptés:**
- Tous les types
- Utilisé pour les albums ajoutés manuellement

---

## 📊 Spotify (source='spotify')

**Types acceptés:**
- Tous les types (historique d'écoute potentiel)
- Support généralement `NULL` ou `Digital`

---

## 🔍 Validation au moment de la synchronisation Discogs

### Format de détection Discogs

```python
formats = [f.get('name', 'Unknown') for f in release_data.formats]

# Détection du support
if 'Vinyl' in format_name or 'LP' in format_name:
    support = "Vinyle"
elif 'CD' in format_name:
    support = "CD"
elif 'Digital' in format_name:
    support = "Digital"
else:
    support = "Unknown"
```

### Validation lors de la création

```python
def is_valid_support(self) -> bool:
    if self.source == "discogs":
        valid_supports = {None, "Vinyle", "Vinyl", "CD", "Digital", "Cassette"}
        return self.support in valid_supports
    return True  # Pas de validation pour les autres sources
```

---

## 💾 Historique de correction

- **Avant:** Albums Discogs pouvaient avoir n'importe quel support
- **Problème:** Albums Roon (support="Roon") mélangés avec albums Discogs
- **Solution:** Colonne `source` + validation stricte
- **État actuel:** ✅ Tous les albums Discogs ont un support valide

---

## 📝 Exemple SQL de validation

```sql
-- Vérifier les supports invalides pour Discogs
SELECT id, title, support 
FROM albums 
WHERE source = 'discogs' 
AND support NOT IN ('Vinyle', 'Vinyl', 'CD', 'Digital', 'Cassette')
AND support IS NOT NULL;

-- Résultat: 0 lignes (tous valides)
```

---

## 🔄 Migration de support existant

Si vous devez corriger un support existant:

```sql
-- Corriger un support invalide
UPDATE albums 
SET support = 'CD'
WHERE id = 123 AND source = 'discogs';
```

---

## 📖 Référence API

Lors de la création d'un album via API:

```json
{
  "title": "Rumours",
  "year": 1977,
  "support": "Vinyle",          // Pour Discogs
  "source": "discogs",          // Marque la source
  "discogs_id": "123456",       // ID Discogs
  "artists": ["Fleetwood Mac"]
}
```

---

**Dernière mise à jour:** 31 janvier 2026
