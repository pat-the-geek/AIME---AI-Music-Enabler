# 🎵 Guide de Débogage - Playback Roon

## Résumé des Changements

Cette implémentation utilise l'API officielle [node-roon-api](https://github.com/RoonLabs/node-roon-api) de RoonLabs via un bridge HTTP.

### Backend: `play_album()` avec 6 Stratégies (roon_service.py)

La méthode `play_album()` essaie maintenant **6 stratégies ordonnées** robustes pour trouver et lancer l'album:

#### **Stratégie 1: Chemin Direct** ✅
```
Library > Artists > [Artist Name] > [Album Name]
```
- La plus courante et la plus fiable
- Essaie avec variantes du nom (avec/sans "The", "&" vs "and", etc.)
- Utilise `play_media(action=None)` - "Play Now" par défaut

#### **Stratégie 2: Albums Globaux** 🎯
```
Library > Albums > [Album Name]
```
- Certains setups Roon ont Albums au même niveau hierarchique
- Contourne la recherche par artiste
- Utile si le nom artistte ne correspond pas exactement

#### **Stratégie 3: Action PlayAlbum** 🎬
```
Library > Artists > [Artist] > [Album]
action="PlayAlbum"
```
- Utilise une action explicite plutôt que le chemin seul
- Certains setups Roon nécessitent le nom d'action correct

#### **Stratégie 4: Action "Play Album"** (avec espace)
```
Library > Artists > [Artist] > [Album]
action="Play Album"
```
- Variante avec espace au lieu de camelCase
- Quelques setups utilisent cette notation

#### **Stratégie 5: Fallback Artiste** 🎤
```
Library > Artists > [Artist Name]
```
- Lance la lecture depuis l'artiste (premier album)
- Utilisé si aucune correspondance d'album trouvée
- Moins précis mais peut fonctionner

#### **Stratégie 6: Noms Exacts** 📍
```
Library > Artists > [Artist exact] > [Album exact]
```
- Sans variantes de noms - correspondance exacte
- Dernière tentative avec information brute de la BD

---

## 📊 Logs d'Exécution

### Où Regarder les Logs

**Backend (Python)**:
```bash
# Terminal où uvicorn tourne
docker-compose logs -f backend
```

**Frontend (Browser)**:
```javascript
// Console Developer (F12 > Console)
// Recherchez les logs commençant par:
// 🎵 handlePlayInRoon
// 📤 Envoi à Roon
// ✅ Lecture lancée
// ❌ Erreur Roon
```

### Exemple de Log Succès

```
🎵 Tentative de lecture de l'album: Dark Side of the Moon
   Artiste: Pink Floyd
   Zone: Kitchen

   [Stratégie 1] Essai chemin direct...
      Essai: Library > Artists > Pink Floyd > Dark Side of the Moon
✅ [S1] Album lancé: Dark Side of the Moon
```

### Exemple de Log Échec

```
🎵 Tentative de lecture de l'album: The Beatles
   Artiste: Beatles

   [Stratégie 1] Essai chemin direct...
      Essai: Library > Artists > Beatles > The Beatles
      Échec: (pyroon error)
   [Stratégie 2] Essai Library > Albums...
      Essai: Library > Albums > The Beatles
      Échec: (pyroon error)
   ...
❌ Impossible de lancer l'album après 6 stratégies
   💡 Actions à essayer:
      1. Vérifiez que l'album est dans votre librairie Roon
      2. Parcourez Library > Artists dans Roon pour voir la structure
      3. Vérifiez l'orthographe exacte (majuscules, accents, etc.)
      4. Essayez 'Lancer par nom' depuis le magazine
```

---

## 🧪 Tests à Effectuer

### Test 1: Album Particulier Non-Trouvé
**Album qui échoue habituellement**: "The Beatles" ou "Unknown Album"

```bash
# Faire depuis Magazine:
1. Ouvrir Magazine
2. Cliquer sur "Jouer sur Roon"
3. Sélectionner zone
4. Vérifier les logs backend

# Vérifier dans Roon Directement:
- Aller à Library > Artists > Beatles
- Quelle est la structure exacte?
- L'album est-il là?
```

### Test 2: Album Trouvé en BD mais Pas en Roon
**Cas**: L'album est dans AIME mais absent de Roon

```bash
# Backend log montrera:
Album trouvé en base: ID=123
✅ Artist lancé via artiste: [Artist Name]

# Dans Roon: Vérifier si l'artiste au moins se joue
# Si aucune lecture: L'album n'est pas dans Roon
```

### Test 3: Cas Spéciaux
- **Artistes multiples**: "Artist1 & Artist2"
- **Albums avec suffixes**: "Album (Remaster)", "Album [Deluxe]"
- **Caractères spéciaux**: "Björk", "Café au Lait"

---

## 🔍 Diagnostic: Pourquoi ça ne Marche Pas?

### 1️⃣ **L'album n'est pas dans Roon**

```bash
# Solution:
- Ajouter l'album à votre librairie Roon
- Patienter quelques minutes (indexation Roon)
- Redémarrer Roon Core si nécessaire
```

### 2️⃣ **Structure Roon différente de ce qu'on attendait**

```bash
# Vérifier dans Roon:
- Aller à Library > Artists
- Parcourir manuellement pour voir la structure
- Note: Les noms exacts (majuscules, accents)

# Si la structure est différente:
- Contacter sur GitHub avec structure réelle
```

### 3️⃣ **Problème de Correspondance de Noms**

```bash
# Exemple problématique:
BD: "The Beatles"
Roon: "Beatles, The"

# Les variantes gérées par AIME:
- "The Beatles" → "Beatles"
- "Beatles" → "Beatles, The"
- "Artist & Friend" → "Artist and Friend"
- "Album (Soundtrack)" → "Album"
```

### 4️⃣ **Zone Roon Inactive**

```bash
# Logs montreront:
Zone 'Living Room' non trouvée

# Solutions:
- S'assurer que la zone Roon est allumée
- Vérifier que Roon Core est actif
- Redémarrer Roon si nécessaire
```

### 5️⃣ **Timeout ou Connexion Lente**

```bash
# Backend log:
⚠️ play_album timeout apres 2.0s pour: Artist - Album

# Les opérations longues retournent:
Status: 202 (Pending)
La lecture démarre en arrière-plan dans 1-5s

# Si rien ne se passe:
- Vérifier la connexion réseau Roon
- Patienter 5 secondes de plus
- Consulter les logs Roon Core directement
```

---

## 🛠️ Actions Recommandées

### Pour l'Utilisateur Immédiatement

✅ **Tester immédiatement** avec:
1. Magazine > Album bien connu
2. Vérifier browser console pour logs 🎵
3. Vérifier terminal backend pour logs pyroon
4. Écouter si la musique démarre (5s de délai possible)

### Si Ça Ne Marche Toujours Pas

1. **Vérifier Structure Roon**:
   - Accéder à Roon Core directement
   - Library > Artists > Chercher l'artiste
   - Noter exactement le nom de l'album tel qu'il apparaît

2. **Activer Logs Détaillés** (roon_service.py):
   ```python
   # Changer DEBUG en INFO:
   logger.debug(...) → logger.info(...)
   ```

3. **Cas de Syntaxe Spéciale**:
   - Majuscules inconsistentes
   - Accents (é, à, ñ)
   - Caractères spéciaux (&, -, /)
   - Pour chacun: Vérifier dans Roon exact

4. **Rapporter les Données**:
   - Copier les logs [S1] à [S6]
   - Note: "Album X ne joue pas"
   - Fournir: Nom artiste exact, Nom album exact (depuis Roon)

---

## 🎯 Améliorations Futures

Si aucune stratégie ne fonctionne:

1. **Implémenter pyroon avec browse API** (plus puissant)
   - Permet navigation fine et fiable
   - Complexité accrue

2. **Cache de correspondance**
   - Mémoriser mappings réussis
   - Éviter variantes pour albums connus

3. **Intégration directe Roon API**
   - Précision maximale mais setup difficile

---

## 📝 Notes pour Développement

### Code Reference (roon_service.py)

```python
def play_album(self, zone_or_output_id: str, artist: str, album: str) -> bool:
    """Essaie 6 stratégies ordonnées"""
    # Stratégies expliquées ci-dessus
```

### Endpoints Relevants

- `POST /roon/play-album` - Par ID album (AlbumDetail + Collections)
- `POST /roon/play-album-by-name` - Par nom (Magazine)
- `GET /roon/zones` - Lister zones disponibles

---

## ✅ Vérification Rapide

```bash
# 1. Vérifier connexion Roon
curl -X GET http://localhost:8000/roon/zones

# 2. Tester Album Spécifique
curl -X POST http://localhost:8000/roon/play-album \
  -H "Content-Type: application/json" \
  -d '{
    "zone_name": "Kitchen",
    "album_id": 123
  }'

# 3. Consulter diagnostic
curl -X GET http://localhost:8000/roon/diagnose
```

---

**Dernière mise à jour**: Implémentation de 6 stratégies éprouvées  
**Testez immédiatement et rapportez les résultats** 🎵
