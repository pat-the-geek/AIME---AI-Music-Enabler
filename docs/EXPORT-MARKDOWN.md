# 📄 Export Markdown - Collection Discogs

## Vue d'ensemble

La collection Discogs peut maintenant être exportée en markdown avec formatage enrichi, incluant toutes les informations et résumés IA.

## ✨ Fonctionnalités

### 1. Export Complet de la Collection
Exporte tous les 235 albums Discogs triés par artiste et album.

**Format:**
```
# 🎵 Collection Discogs

## Artiste 1
- Album 1
- Album 2

## Artiste 2
- Album 1
```

### 2. Export par Artiste
Exporte la discographie d'un artiste spécifique.

### 3. Export par Support
Exporte tous les albums d'un support (Vinyle, CD, Digital).

## 🔗 Endpoints API

### Export Complet
```bash
GET /api/v1/collection/export/markdown
```

**Réponse:** Fichier `collection-discogs.md` en téléchargement

**Exemple:**
```bash
curl -o collection.md http://localhost:8000/api/v1/collection/export/markdown
```

### Export par Artiste
```bash
GET /api/v1/collection/export/markdown/{artist_id}
```

**Paramètres:**
- `artist_id` (int, requis) : ID de l'artiste

**Réponse:** Fichier `collection-{artist-name}.md` en téléchargement

**Exemple:**
```bash
curl -o air.md http://localhost:8000/api/v1/collection/export/markdown/42
```

### Export par Support
```bash
GET /api/v1/collection/export/markdown/support/{support}
```

**Paramètres:**
- `support` (string, requis) : Support (`Vinyle`, `CD`, `Digital`, `Cassette`)

**Réponse:** Fichier `collection-{support}.md` en téléchargement

**Exemple:**
```bash
curl -o vinyl.md http://localhost:8000/api/v1/collection/export/markdown/support/Vinyle
```

## 📋 Format Markdown

### Structure Générale

```markdown
# 🎵 Collection Discogs

**Exportée le:** 31/01/2026 à 17:30
**Total:** 235 albums

---

## Table des matières

- [AIR](air) (5)
- [Björk](björk) (3)
...

---

# AIR

*5 albums*

---

## Album Title

**Artiste:** AIR

- **Année:** 2000
- **Labels:** Virgin Music
- **Support:** CD
- **Discogs ID:** 123456

**Résumé:**

Résumé IA généré...

**Liens:** [Spotify](url) | [Discogs](url)

![Album Art](image-url)

---
```

### Éléments Inclus

**Par Album:**
- ✅ Titre
- ✅ Artistes
- ✅ Année
- ✅ Labels
- ✅ Support (Vinyle/CD/Digital)
- ✅ Discogs ID
- ✅ Résumé IA complet
- ✅ Lien Spotify
- ✅ Lien Discogs
- ✅ Image de couverture

**Organisation:**
- ✅ Table des matières
- ✅ Groupement par artiste
- ✅ Tri par année puis titre
- ✅ Date d'export
- ✅ Compte total d'albums

## 💾 Fichiers Générés

| Export | Nom Fichier | Contenu |
|--------|-------------|---------|
| Complet | `collection-discogs.md` | 235 albums |
| Artiste | `collection-{artist-name}.md` | Albums de l'artiste |
| Support | `collection-{support}.md` | Albums du support |

## 🎨 Formatage

### Typographie
```markdown
# Titre principal (Artiste)
## Titre secondaire (Album)
**Gras** pour les champs
*Italique* pour les compléments
[Liens](url) pour les URLs
- Listes à puces pour les infos
```

### Séparation
```markdown
---  # Ligne de séparation entre albums
```

### Images
```markdown
![Titre](url)  # Images de couverture
```

## 📊 Exemple d'Export

### Export Complet (Extrait)

```markdown
# 🎵 Collection Discogs

**Exportée le:** 31/01/2026 à 17:30
**Total:** 235 albums

---

## Table des matières

- [AIR](#air) (5)
- [Björk](#björk) (3)
- [The National](#the-national) (2)

---

# AIR

*5 albums*

---

## Moon Safari

**Artiste:** AIR

- **Année:** 1998
- **Labels:** Virgin Music
- **Support:** CD
- **Discogs ID:** 12345

**Résumé:**

*Moon Safari* (1998) est le premier album d'**AIR**, une collaboration entre Nicolas Godin et Jean-Benoît Dunckel. Cet album révolutionnaire marque l'émergence de la **French Touch**...

**Liens:** [Spotify](https://spotify.com/...) | [Discogs](https://discogs.com/...)

![Moon Safari](image-url)

---

## La Femme d'Argent

**Artiste:** AIR

- **Année:** 1998
- **Labels:** Virgin Music
- **Support:** CD
- **Discogs ID:** 12346

**Résumé:**

*La Femme d'Argent* est une composition majeure de *Moon Safari*...

...
```

## 🚀 Cas d'Usage

### 1. Documentation Complète
Générer une documentation complète de la collection à consulter hors ligne.

```bash
curl http://localhost:8000/api/v1/collection/export/markdown > collection.md
```

### 2. Portfolio d'Artiste
Exporter la discographie d'un artiste pour partage ou présentation.

```bash
curl http://localhost:8000/api/v1/collection/export/markdown/12 > artist-discography.md
```

### 3. Catalogue par Format
Générer un catalogue de tous les vinyles disponibles.

```bash
curl http://localhost:8000/api/v1/collection/export/markdown/support/Vinyle > vinyls.md
```

### 4. Partage sur GitHub
Publier la collection sur GitHub comme README enrichi.

## 📝 Notes

- Les exports incluent **toutes les informations disponibles**
- Les résumés IA sont **inclus intégralement** si disponibles
- Les images de couverture sont **directement intégrées** via URLs
- Le tri est **alphabétique par artiste**, puis chronologique par album
- La date d'export est **automatiquement ajoutée**
- Les fichiers sont en **UTF-8** pour support unicode

## 🔧 Améliorations Futures

- [ ] Export PDF avec formatage avancé
- [ ] Export JSON-LD pour SEO
- [ ] Export multi-formats (HTML, DOCX)
- [ ] Pagination automatique pour larges collections
- [ ] Filtres additionnels (année, genre)
- [ ] Intégration de playlists Spotify

---

**Status:** ✅ Disponible en production
**Créé:** 31 janvier 2026
