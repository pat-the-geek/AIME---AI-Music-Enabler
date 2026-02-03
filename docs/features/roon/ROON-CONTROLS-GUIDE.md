# Guide Roon Controls - Contrôles de Lecture Roon

## 🎵 Vue d'ensemble

AIME intègre maintenant des contrôles de lecture Roon avancés, permettant de contrôler la musique directement depuis l'application avec un widget flottant et des commandes dans les playlists.

## 🎮 Fonctionnalités

### 1. **Contrôleur Flottant Roon** 📻

Un widget flottant affiche en temps réel:
- ✅ **Titre du track** en cours de lecture
- ✅ **Artiste** et **Album**
- ✅ **Zone Roon** active
- ✅ **Boutons de contrôle** (pause, play, next, previous, stop)

#### Caractéristiques du Widget:
- 📍 **Position**: Coin inférieur droit de l'écran
- 🔄 **Mise à jour**: Tous les 3 secondes
- 🔕 **Minimisable**: Cliquez sur l'en-tête pour réduire/développer
- ✕ **Cachable**: Bouton X pour masquer temporairement
- 🎨 **Design**: Fond transparent avec effet glassmorphism

### 2. **Contrôles dans les Playlists** 🎵

Sur chaque carte de playlist:

#### Boutons de Contrôle Rapides:
- ⏮️ **Piste Précédente**: Sautez au track précédent
- ⏸️ **Pause/Play**: Contrôlez la lecture (visible uniquement si Roon est disponible)
- ⏭️ **Piste Suivante**: Sautez au prochain track

#### Info en Temps Réel:
- 🟢 **Indicateur live**: Affiche le track actuellement joué
- Mise à jour automatique toutes les 3 secondes
- Le track actif s'affiche en haut de la playlist

## 🎛️ Contrôles Disponibles

### Commandes de Lecture:

| Bouton | Fonction | Raccourci |
|--------|----------|-----------|
| **Play** | Reprendre la lecture | ▶️ |
| **Pause** | Mettre en pause | ⏸️ |
| **Next** | Piste suivante | ⏭️ |
| **Previous** | Piste précédente | ⏮️ |
| **Stop** | Arrêter la lecture | ⏹️ |

### Feedback Utilisateur:

- 🟢 **Indicateur pulsant** vert = Lecture en cours
- ⚪ **Zone inactive** = Aucune lecture
- 📋 **Compteur** = Nombre de tracks en queue

## 📱 Interface

### Contrôleur Flottant - Vue Détaillée:

```
┌─────────────────────────────────┐
│ 🟢 EN COURS DE LECTURE  ✕ ▲    │  <- En-tête pulsant
├─────────────────────────────────┤
│                                 │
│ Shine on You Crazy Diamond...   │  <- Titre
│ Pink Floyd                      │  <- Artiste
│ Wish You Were Here              │  <- Album
│ 📻 Sonos Move 2                 │  <- Zone
│                                 │
│  ⏮️   ⏸️   ⏭️   ⏹️              │  <- Contrôles
│                                 │
└─────────────────────────────────┘
```

### Playlists - Contrôles:

```
[Playlist Card]
├─ Titre & Infos
├─ 🟢 En cours de lecture
│  ├─ Track actuellement joué
│  └─ Artiste
├─ Boutons principaux
│  ├─ [Voir les Tracks]
│  ├─ [▶ Roon]
│  └─ [🗑️]
└─ Contrôles rapides
   ├─ [⏮️ Précédent]
   ├─ [⏸️ Pause]
   └─ [⏭️ Suivant]
```

## 🚀 Utilisation

### Lancer une Playlist:

1. Naviguez vers **Playlists** 📋
2. Sélectionnez la zone Roon (dialog)
3. Cliquez **▶ Roon** pour démarrer
4. Les contrôles deviennent actifs immédiatement

### Contrôler la Lecture:

**Option 1 - Widget Flottant:**
- Utilisez les 5 boutons de contrôle
- Le widget est toujours visible et accessible

**Option 2 - Contrôles des Playlists:**
- Cliquez directement sur les boutons ⏮️ ⏸️ ⏭️
- Disponibles sur toutes les cartes de playlist

### Minimiser/Afficher le Widget:

- 🖱️ Cliquez sur l'en-tête pour plier/déplier
- ✕ Cliquez sur ✕ pour masquer (réapparaîtra au refresh)

## ⚙️ Configuration Requise

### Prérequis:
- ✅ Roon Server actif et configuré
- ✅ Extension Roon approuvée
- ✅ Zone Roon disponible et connectée
- ✅ Au moins 1 track dans votre bibliothèque

### Vérification du Statut:
1. Allez à **Paramètres** ⚙️
2. Vérifiez que **Roon est actif** ✅
3. Confirmez la **Zone sélectionnée** 📻

## 🔍 Dépannage

### Le widget n'apparaît pas:
- ❌ Roon n'est pas activé
- ❌ Aucun track n'est en cours de lecture
- **Solution**: Démarrez une playlist avec `▶ Roon`

### Les contrôles ne répondent pas:
- ❌ Zone non sélectionnée
- ❌ Connexion Roon perdue
- **Solution**: Relancez la lecture, sélectionnez la zone

### Pas de mise à jour du track:
- ❌ Polling désactivé
- **Solution**: Rechargez la page ou cliquez sur le widget

## 💡 Astuce Utilisateur

- 🎯 Le widget reste visible en bas à droite
- ⌨️ Utilisez les boutons rapides des playlists pour contrôler sans scroller
- 📊 Consultez l'info en temps réel pour savoir ce qui joue
- 🔊 Les contrôles fonctionnent sur **TOUTES les zones** - gérez plusieurs espaces

## 🆚 Comparaison Anciennes vs Nouvelles Fonctionnalités

| Fonctionnalité | Avant | Après |
|---|---|---|
| Contrôle de lecture | ❌ Non | ✅ Oui |
| Widget flottant | ❌ Non | ✅ Oui |
| Info en temps réel | ❌ Non | ✅ 3s |
| Contrôles dans playlists | ❌ Non | ✅ Oui |
| Pause/Play direct | ❌ Non | ✅ Oui |

## 📝 Notes Techniques

### Endpoints Utilisés:
- `GET /api/v1/roon/now-playing` - Récupère le track en cours
- `POST /api/v1/roon/control` - Envoie les commandes (pause, play, next, etc.)
- `GET /api/v1/roon/status` - Vérifie la disponibilité de Roon

### Polling:
- **now-playing**: 3 secondes (quand Roon est actif)
- **status**: 10 secondes (permanent)

### Performance:
- ⚡ Léger impact (requêtes minimes)
- 🔄 Polling optimisé avec localStorage
- 📊 Aucun ralentissement observé

---

**Dernière mise à jour**: 1er Février 2026 | Version 1.0
