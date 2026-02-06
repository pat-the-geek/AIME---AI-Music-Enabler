# 🤖 GUIDE AUTO-ENRICHISSEMENT - DESCRIPTIONS & IMAGES

## Vue d'ensemble

L'option **Automatisation** fournit 3 niveaux d'enrichissement :

```
Niveau 1 (GRATUIT)
└─ Templates locaux + Last.fm (images)
   ├─ Aucune clé API requise
   ├─ Descriptions basiques
   └─ Images artiste de good quality

Niveau 2 (GRATUIT + PAYANT)
├─ OpenAI (descriptions générées par IA)
├─ Spotify (images haute résolution)
└─ Last.fm (images de fallback)

Niveau 3 (PERSONNALISÉ)
├─ API Euria (si disponible)
├─ Hugging Face (génération local)
└─ Custom pipeline
```

## Installation et Configuration

### Option 1: Démarrage rapide (sans API)

```bash
# Lancer l'enrichissement avec templates locaux
python3 auto_enrich_from_api.py --no-refresh

# Appliquer les données
python3 refresh_complete.py

# Valider
python3 verify_enrichment.py
```

**Résultat**: Descriptions basiques + Aucune image artiste

---

### Option 2: Avec Last.fm (RECOMMANDÉ - GRATUIT)

#### 1. Créer un compte et API key

```
1. Aller sur: https://www.last.fm/api/account/create
2. S'identifier ou créer un compte
3. Remplir le formulaire (Application name, description, etc.)
4. Copier votre API Key
```

#### 2. Configurer l'API key

```bash
python3 setup_automation.py
# Sélectionner l'option Last.fm et coller votre clé
```

#### 3. Lancer l'enrichissement

```bash
python3 auto_enrich_integrated.py
# → Récupère les images depuis Last.fm
# → Lance refresh_complete.py automatiquement
```

**Résultat**: Descriptions basiques + Images artiste de qualité

---

### Option 3: Avec OpenAI (MEILLEUR RÉSULTAT - PAYANT)

#### 1. Obtenir une clé OpenAI

```
1. Créer compte: https://platform.openai.com
2. Créer une clé API: https://platform.openai.com/account/api-keys
3. Ajouter une méthode de paiement
4. Fixer un budget (par défaut $5/mois)
```

**Coût estimé**: ~$0.50-$2 pour 236 descriptions

#### 2. Installer la librairie

```bash
pip install openai
```

#### 3. Configurer

```bash
python3 setup_automation.py
# Sélectionner OpenAI et coller votre clé
# (Optionnellement: Last.fm pour les images)
```

#### 4. Lancer

```bash
python3 auto_enrich_integrated.py
# → Génère descriptions avec GPT-3.5
# → Récupère images avec Last.fm (si configuré)
# → Lance refresh_complete.py automatiquement
```

**Résultat**: Descriptions en IA + Images artiste

---

### Option 4: Avec Spotify (IMAGES HAUTE RÉSOLUTION)

#### 1. Créer une Spotify Developer App

```
1. Créer compte: https://developer.spotify.com/dashboard
2. Créer une application
3. Accepter les conditions
4. Copier Client ID et Client Secret
```

#### 2. Installer la librairie

```bash
pip install spotipy
```

#### 3. Configurer

```bash
python3 setup_automation.py
# Sélectionner Spotify et coller Client ID + Secret
```

#### 4. Lancer

```bash
python3 auto_enrich_integrated.py
# → Récupère images depuis Spotify (meilleure qualité)
# → Fallback vers Last.fm si pas trouvé
```

**Résultat**: Images artiste haute résolution

---

## Architecture du Système

### Scripts Principaux

```
setup_automation.py
├─ Configure les clés API
├─ Crée config/enrichment_api_keys.json
└─ Teste les connexions

auto_enrich_from_api.py
├─ Enrichissement basique (templates)
├─ Récupère Last.fm si configuré
└─ Sauvegarde en JSON

auto_enrich_integrated.py
├─ Enrichissement multi-source
├─ Essaie OpenAI → Last.fm → Template
├─ Essaie Spotify → Last.fm
└─ Lance refresh_complete.py auto.

workflow_auto_enrich.py
├─ Orchestration complète (4 étapes)
├─ Menu interactif
└─ Validation finale
```

### Flux de données

```
Albums Discogs (236)
        ↓
[Generate Descriptions]
├─ OpenAI (si configuré)
├─ Last.fm enrichment (si configuré)
└─ Template local (fallback)
        ↓
data/euria_descriptions.json
        ↓
[Generate Artist Images]
├─ Spotify (si configuré)
├─ Last.fm (si configuré)
└─ (Skip si aucun API)
        ↓
data/artist_images.json
        ↓
refresh_complete.py
├─ Charge les JSON
├─ Filtre les templates invalides
├─ Normalise les noms
└─ Update Album.ai_description + Artist images
        ↓
Database (236 albums enrichis)
```

---

## Cas d'usage pratiques

### Scénario 1: Démarrage rapide (5 minutes)

```bash
# Sans API requise
python3 auto_enrich_from_api.py

# Résultat: descriptions basiques
# Temps: ~30 secondes
```

### Scénario 2: Qualité en priorité (15 minutes)

```bash
# Avec Last.fm
python3 setup_automation.py
# → Seulement configurer Last.fm
python3 auto_enrich_integrated.py

# Résultat: descriptions + images artiste
# Temps: ~2-3 minutes
```

### Scénario 3: Résultat optimal (30 minutes)

```bash
# Configurer OpenAI + Spotify
python3 setup_automation.py
# → OpenAI (descriptions IA)
# → Spotify (images haute res)
# → Last.fm (fallback)

python3 auto_enrich_integrated.py

# Résultat: descriptions IA + images haute résolution
# Coût: ~$2-5 pour 236 descriptions
# Temps: ~5-10 minutes
```

### Scénario 4: Orchestration complète

```bash
# Menu interactif avec validation
python3 workflow_auto_enrich.py

# Choix:
# 1. Configuration (optional)
# 2. Enrichissement (menu)
# 3. Refresh & Application
# 4. Validation
```

---

## Configuration Avancée

### Personnaliser le prompt OpenAI

Modifier `auto_enrich_integrated.py`, ligne ~80:

```python
@staticmethod
def _openai(album: Album) -> Optional[str]:
    # Adapter le prompt ici
    prompt = f"""
    Write a 100-word review for '{album.title}'
    by {artists}{year}.
    
    Focus on: [votre spécialité]
    """
```

### Utiliser Hugging Face (modèles locaux)

```bash
pip install transformers torch

# Modifier auto_enrich_from_api.py pour:
DESCRIPTION_SOURCE = "huggingface"
```

Voir `enrichment_api_examples.py` pour les détails.

### Filter personnalisé

Dans `refresh_complete.py`, adapter les lignes 100-130 pour:
- Valider descriptions
- Nettoyer URLs d'images
- Appliquer business rules

---

## Validation et Qualité

### Vérifier les résultats

```bash
# Rapport de vérification
python3 verify_enrichment.py

# Output:
# Tame Impala albums: 5/5 found
# Descriptions: 5/5 ✓
# Artist images: 5/5 ✓
# Global stats: 236 albums enrichis
```

### Auditer les données

```bash
# Charger et vérifier les JSON
python3 -c "
import json
data = json.load(open('data/euria_descriptions.json'))
# Compter non-vides
filled = len([v for v in data['data'].values() if v and not v.startswith('[')])
total = len(data['data'])
print(f'Descriptions: {filled}/{total}')
"
```

### Nettoyer les données invalides

```bash
python3 cleanup_bad_enrichment.py
# Supprime les templates mal formés de la BD
```

---

## Troubleshooting

### Erreur: "API key invalid"

```
Vérifier:
1. La clé est copiée complètement (sans espaces)
2. La clé correspond au bon service
3. Le compte API est actif
4. Rate limits pas atteints
```

### Erreur: "No results found"

```
Pour Last.fm: Le nom de l'artiste peut être mal orthographié
Pour Spotify: Vérifier les credentials Client ID/Secret

Solution: Ajouter fallback ou skip:
python3 auto_enrich_integrated.py --skip-missing
```

### Images ne se trouvent pas

```
1. Vérifier config (Spotify ou Last.fm activé ?)
2. Vérifier les logs: python3 auto_enrich_integrated.py --verbose
3. Utiliser fallback: configurer 2e source

Exemple:
- Primary: Spotify (haute résolution)
- Fallback: Last.fm (fallback)
```

### Refresh ne s'applique pas

```
Vérifier:
1. refresh_complete.py s'exécute sans erreur
2. Les JSON sont bien formés: python3 -m json.tool data/*.json
3. La base de données est accessible: python3 test_db_simple.py
```

---

## Optimisations

### Performance

```python
# Réduire le nombre de requêtes
python3 auto_enrich_from_api.py --skip-existing
# Skip les albums déjà enrichis

# Batch size
# Modifier le batch size dans refresh_complete.py (ligne 160)
# Défaut: 50 albums → Augmenter à 100-200
```

### Coût API OpenAI

```python
# Utiliser modèle moins cher
# Modifier setup_automation.py:
config["openai"]["model"] = "gpt-3.5-turbo"  # Moins cher
# vs
config["openai"]["model"] = "gpt-4"          # Plus cher

# Estimé:
# gpt-3.5-turbo: $0.0015 / 1K tokens
# gpt-4: $0.03 / 1K tokens
# 236 albums × 120 tokens = 28,320 tokens
# Coût: ~$0.04 (gpt-3.5) vs ~$0.85 (gpt-4)
```

### Rate Limiting

```python
# Last.fm: 5 req/sec (défaut: 0.2s delay)
# OpenAI: 3 req/sec (défaut: auto)
# Spotify: 1 req/sec (défaut: auto)

# Modifier dans auto_enrich_integrated.py:
time.sleep(0.1)  # Réduire pour plus rapide
# vs
time.sleep(0.5)  # Augmenter pour respecter limites
```

---

## Prochaines étapes

1. **Démarrer**: `python3 setup_automation.py`
2. **Enrichir**: `python3 auto_enrich_integrated.py`
3. **Valider**: `python3 verify_enrichment.py`
4. **Compléter**: Éditer manuellement les descriptions reste non-remplies
5. **Itérer**: Ajouter d'autres sources (Euria, propriété API, etc.)

---

## Support & Ressources

### APIs

- Last.fm: https://www.last.fm/api/
- OpenAI: https://platform.openai.com/docs
- Spotify: https://developer.spotify.com/documentation
- Hugging Face: https://huggingface.co/docs

### Fichiers

- Configuration: `config/enrichment_api_keys.json`
- Descriptions: `data/euria_descriptions.json`
- Images: `data/artist_images.json`
- Exemples: `enrichment_api_examples.py`

### Documentation

- Ce fichier: Guide complet
- `PHASE4-ENRICHMENT-GUIDE.md`: Architecture technique
- `PHASE4-COMPLETION-SUMMARY.md`: Résumé des modifications

---

*Dernière mise à jour: 2026-02-06*
*version 1.0 - AUTO-ENRICHISSEMENT INTÉGRÉ*
