# Guide Utilisateur : Configuration du Tracker

## 📻 Gestion des Stations de Radio

### Vue d'ensemble

Les trackers d'écoute (Last.fm et Roon) détectent automatiquement les **stations de radio** et les **ignorent** pour éviter de polluer votre collection musicale avec des lectures de radio.

**Objectif:** Enregistrer uniquement la musique réelle écoutée, pas les émissions radio.

### Pourquoi ignorer les stations de radio ?

Les stations de radio ont souvent :
- Des métadonnées incomplètes ou inconsistantes
- Des artistes et titres parsés différemment selon la station
- Des doublons dans votre historique (même chanson lue plusieurs fois)
- Une qualité variable de données

En les ignorant, vous gardez votre collection musicale **propre et organisée**.

---

## ⚙️ Configuration

### Localisation du fichier de configuration

```
config/app.json
```

### Structure de configuration

Voici la section pertinente dans `config/app.json` :

```json
{
  "roon_tracker": {
    "enabled": true,
    "interval_seconds": 120,
    "listen_start_hour": 8,
    "listen_end_hour": 22,
    "radio_stations": [
      "RTS La Première",
      "RTS Couleur 3",
      "RTS Espace 2",
      "RTS Option Musique",
      "Radio Meuh",
      "Radio Nova"
    ]
  }
}
```

### Paramètres disponibles

| Paramètre | Type | Description | Exemple |
|-----------|------|-------------|---------|
| `enabled` | bool | Active/désactive le tracker Roon | `true` |
| `interval_seconds` | int | Intervalle de polling en secondes | `120` |
| `listen_start_hour` | int | Heure de début du suivi | `8` |
| `listen_end_hour` | int | Heure de fin du suivi | `22` |
| `radio_stations` | array | Liste des stations à ignorer | `["RTS La Première"]` |

---

## 🎯 Ajouter une nouvelle station de radio

### Étape 1 : Ouvrir le fichier de configuration

```bash
# Avec votre éditeur préféré
code config/app.json
```

### Étape 2 : Localiser la section `radio_stations`

Cherchez cette section dans `roon_tracker` :

```json
"radio_stations": [
  "RTS La Première",
  "RTS Couleur 3"
  // ... autres stations
]
```

### Étape 3 : Ajouter la nouvelle station

```json
"radio_stations": [
  "RTS La Première",
  "RTS Couleur 3",
  "RTS Espace 2",
  "RTS Option Musique",
  "Radio Meuh",
  "Radio Nova",
  "Ma Station Radio"  // ← Nouvelle station
]
```

### Étape 4 : Sauvegarder et redémarrer

```bash
# Redémarrer le backend pour appliquer les changements
cd backend
# Arrêter le backend (Ctrl+C)
# Puis relancer le service
```

---

## 📝 Format des noms de stations

### Règles de détection

La détection des stations de radio se fait par correspondance **case-insensitive** sur :

1. **Correspondance exacte** (même nom, minuscules/majuscules ignorées)
   ```
   Configured: "RTS La Première"
   Detected: "rts la première" → ✅ Ignorée
   ```

2. **Correspondance partielle en préfixe**
   ```
   Configured: "RTS"
   Detected: "RTS La Première" → ✅ Ignorée
   ```

3. **Correspondance dans format "Artiste - Titre"** (Last.fm/Roon)
   ```
   Configured: "RTS La Première"
   Detected: "RTS La Première - Jazz Émission" → ✅ Ignorée
   Detected: "Jazz Émission - RTS La Première" → ✅ Ignorée
   ```

### Exemples de noms recommandés

| Station | Nom à utiliser | Raison |
|---------|---|---|
| RTS La Première | `"RTS La Première"` | Nom officiel exact |
| Couleur 3 | `"Couleur 3"` ou `"RTS Couleur 3"` | Nom court sans "RTS" et nom long |
| Radio Meuh | `"Radio Meuh"` | Nom officiel court |
| France Inter | `"France Inter"` | Nom officiel |
| BBC Radio 1 | `"BBC Radio 1"` | Nom avec numéro |

---

## 🔍 Monitorer les stations détectées

### Dans les logs de l'application

Quand une station de radio est détectée et ignorée, vous verrez :

```
📻 Station de radio détectée dans le champ 'artist': RTS La Première
📻 Station de radio ignorée: RTS La Première - Émission musicale
```

### Vérifier quelle station a été ignorée

```bash
# Voir les logs en temps réel
tail -f /tmp/aime_backend.log | grep "📻"
```

### Exemple de sortie

```
2026-02-09 14:25:30 INFO     app.services.roon_tracker_service - 📻 Station de radio détectée dans le champ 'artist': RTS Couleur 3
2026-02-09 14:25:30 INFO     app.services.roon_tracker_service - 📻 Station de radio ignorée: RTS Couleur 3 - Matinale
```

---

## 🛠️ Cas d'Usage Avancés

### Stations multiples avec variantes

Si une station a plusieurs noms ou variantes :

```json
"radio_stations": [
  "RTS La Première",
  "RTS 1",
  "RTS",
  "Radio Meuh",
  "Meuh FM"
]
```

### Ignorer toutes les stations avec un motif

Par exemple, pour ignorer toutes les stations "RTS" :

```json
"radio_stations": [
  "RTS"  // Ignorera "RTS La Première", "RTS Couleur 3", "RTS Espace 2", etc.
]
```

### Désactiver complètement la détection

```json
"radio_stations": []  // Liste vide → traite tous les tracks
```

---

## ⏰ Horaires de suivi

### Configuration horaire

Le tracker peut être configuré pour fonctionner selon vos heures d'écoute :

```json
{
  "roon_tracker": {
    "listen_start_hour": 8,    // Commence à 8h du matin
    "listen_end_hour": 22       // S'arrête à 22h du soir
  },
  "tracker": {
    "listen_start_hour": 8,
    "listen_end_hour": 22
  }
}
```

**Note:** Même si une station est détectée hors de ces horaires, elle sera toujours ignorée.

---

## 🔄 Récupérer les valeurs par défaut

Si vous avez modifié le fichier et voulez restaurer la configuration par défaut :

```json
{
  "roon_tracker": {
    "enabled": true,
    "interval_seconds": 120,
    "listen_start_hour": 8,
    "listen_end_hour": 22,
    "radio_stations": [
      "RTS La Première",
      "RTS Couleur 3",
      "RTS Espace 2",
      "RTS Option Musique",
      "Radio Meuh",
      "Radio Nova"
    ]
  }
}
```

---

## 📊 Exemples de Configuration Complète

### Configuration minimale (une seule station)

```json
{
  "roon_tracker": {
    "enabled": true,
    "interval_seconds": 120,
    "radio_stations": [
      "RTS La Première"
    ]
  }
}
```

### Configuration complète (toutes les options)

```json
{
  "roon_tracker": {
    "enabled": true,
    "interval_seconds": 120,
    "listen_start_hour": 6,
    "listen_end_hour": 23,
    "radio_stations": [
      "RTS La Première",
      "RTS Couleur 3",
      "RTS Espace 2",
      "Couleur Directe",
      "Radio Meuh",
      "Radio Nova",
      "France Inter",
      "Fun Radio",
      "NRJ"
    ]
  },
  "tracker": {
    "enabled": true,
    "interval_seconds": 150,
    "listen_start_hour": 6,
    "listen_end_hour": 23
  }
}
```

---

## 🐛 Dépannage

### Une station n'est pas détectée

**Problème:** Vous écoutez une station mais elle n'est pas ignorée.

**Solution:**
1. Vérifier le nom exact de la station dans les logs
2. Ajouter exactement ce nom dans `radio_stations`
3. Relancer le backend
4. Vérifier les logs pour voir si elle est détectée

### Trop de stations ignorées

**Problème:** Des tracks réels sont ignorés par erreur.

**Solution:**
1. Utiliser des noms plus spécifiques (éviter "Radio", "FM")
2. Exemple : Au lieu de `"Radio"`, utiliser `"RTS La Première"`
3. Tester avec un logs avant/après

---

## 📚 Documentation Connexe

- [QUICKSTART.md](QUICKSTART.md) - Guide de démarrage rapide
- [DISCOVER-GUIDE.md](DISCOVER-GUIDE.md) - Guide de découverte complète
- [GUIDE-UTILISATEUR-ROON-PLAYLISTS.md](GUIDE-UTILISATEUR-ROON-PLAYLISTS.md) - Configuration Roon

---

## ❓ Questions Fréquentes

### Q: La modification de `radio_stations` est-elle prise en compte immédiatement ?

**A:** Non, vous devez redémarrer le backend pour que la nouvelle configuration soit appliquée.

### Q: Quels sont les impacts de l'ignorance des stations sur mes données ?

**A:** 
- Les tracks actualmente enregistrés resteront en base
- Seuls les nouveaux tracks détectés après la modification seront ignorés

### Q: Comment savoir si une station est correctement configurée ?

**A:** Vérifiez les logs quand la station est lue. Vous devriez voir un message `📻 Station de radio détectée...` dans les logs.

### Q: Puis-je ajouter des stations pour Last.fm aussi ?

**A:** Oui, les mêmes stations configurées pour Roon sont automatiquement appliquées au tracker Last.fm.
