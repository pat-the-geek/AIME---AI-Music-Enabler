# Tracker Roon - Documentation

## 🎵 Vue d'ensemble

Le tracker Roon fonctionne en parallèle du tracker Last.fm et permet de capturer automatiquement vos écoutes depuis Roon. Les deux trackers peuvent fonctionner simultanément sans conflit.

## 📋 Caractéristiques

### Fonctionnement Parallèle
- ✅ Fonctionne indépendamment du tracker Last.fm
- ✅ Peut être démarré/arrêté séparément
- ✅ Configuration indépendante (intervalle, plage horaire)
- ✅ Les écoutes sont marquées avec la source (`roon` vs `lastfm`)

### Détection Intelligente
- 🎵 Surveille toutes les zones Roon actives
- 🔄 Intervalle configurable (par défaut: 120 secondes)
- 🕐 Plage horaire active: 8h-22h
- 🎯 Détection des doublons automatique

### Enrichissement Automatique
Comme pour Last.fm, chaque écoute Roon déclenche :
- 🎨 Récupération des images depuis Spotify
- 🔗 Liens Spotify automatiques
- 📅 Années de sortie
- 🤖 Descriptions IA des albums

## 🔧 Configuration

### Fichiers de Configuration

**config/secrets.json**
```json
{
  "roon": {
    "server": "192.168.1.100",
    "token": null
  }
}
```

**config/app.json**
```json
{
  "roon_tracker": {
    "enabled": true,
    "interval_seconds": 120,
    "listen_start_hour": 8,
    "listen_end_hour": 22
  }
}
```

### Paramètres

| Paramètre | Description | Valeur par défaut |
|-----------|-------------|-------------------|
| `server` | Adresse IP du serveur Roon | `192.168.1.100` |
| `token` | Token d'authentification (généré automatiquement) | `null` |
| `interval_seconds` | Fréquence de polling (secondes) | `120` |
| `listen_start_hour` | Heure de début (0-23) | `8` |
| `listen_end_hour` | Heure de fin (0-23) | `22` |

## 🚀 Installation et Configuration

### 1. Trouver l'adresse IP de votre serveur Roon

```bash
# Sur macOS/Linux
arp -a | grep -i "roon"

# Ou utilisez l'app Roon pour vérifier dans Settings > About
```

### 2. Configurer l'adresse du serveur

Éditez `config/secrets.json` :
```json
{
  "roon": {
    "server": "VOTRE_IP_ROON",
    "token": null
  }
}
```

### 3. Premier démarrage et autorisation

1. Démarrez le backend
2. Allez dans Settings > Tracker Roon
3. Cliquez sur "Démarrer le Tracker"
4. **Important** : Dans l'application Roon, allez dans Settings > Extensions
5. Autorisez l'extension "AIME - AI Music Enabler"
6. Le tracker se connectera automatiquement

### 4. Sauvegarde du token

Le token d'authentification est généré lors de la première connexion. Il est recommandé de le sauvegarder :

```python
# Le token peut être sauvegardé dans secrets.json
# Il sera utilisé automatiquement aux prochains démarrages
```

## 📊 API Endpoints

### Statut du tracker Roon
```http
GET /api/v1/services/roon-tracker/status
```

Réponse :
```json
{
  "running": true,
  "connected": true,
  "last_track": "Artist|Title|Album",
  "interval_seconds": 120,
  "last_poll_time": "2026-01-31T10:00:00+00:00",
  "server": "192.168.1.100",
  "zones_count": 2
}
```

### Démarrer le tracker
```http
POST /api/v1/services/roon-tracker/start
```

### Arrêter le tracker
```http
POST /api/v1/services/roon-tracker/stop
```

### Statut global (tous les services)
```http
GET /api/v1/services/status/all
```

## 🎯 Utilisation

### Démarrage
1. Allez dans **Settings** (⚙️)
2. Section "Tracker Roon"
3. Cliquez sur "Démarrer le Tracker"
4. Le voyant passe au vert ✅

### Vérification du fonctionnement
- **Dernière vérification** : Affiche quand le tracker a interrogé Roon pour la dernière fois
- **Dernier morceau détecté** : Affiche le dernier track capturé
- **Zones disponibles** : Nombre de zones Roon actives

### Comparaison des Sources

Dans l'historique d'écoute, vous pouvez voir la source de chaque track :
- 🎵 **Roon** : Écoute capturée depuis Roon
- 📻 **Last.fm** : Écoute capturée depuis Last.fm

## 🔄 Fonctionnement Technique

### Architecture

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   Serveur   │◄────────│  RoonService │◄────────│ RoonTracker  │
│    Roon     │ WebSocket│              │ Polling │   Service    │
└─────────────┘         └──────────────┘         └──────────────┘
                                │                        │
                                │                        │
                                ▼                        ▼
                        ┌──────────────┐         ┌──────────────┐
                        │   Spotify    │         │  AI Service  │
                        │   Service    │         │   (Euria)    │
                        └──────────────┘         └──────────────┘
                                │                        │
                                └────────┬───────────────┘
                                         ▼
                                  ┌─────────────┐
                                  │  Database   │
                                  │ (SQLite)    │
                                  └─────────────┘
```

### Flux de Détection

1. **Polling** : Le tracker interroge Roon toutes les N secondes
2. **Récupération** : Via l'API Roon, récupère les zones et leur état
3. **Filtrage** : Identifie les zones en état "playing"
4. **Extraction** : Récupère titre, artiste, album de la zone active
5. **Déduplication** : Compare avec le dernier track enregistré
6. **Enrichissement** : Récupère infos Spotify + description IA
7. **Sauvegarde** : Enregistre dans la base avec `source='roon'`

### Gestion des Doublons

Le tracker utilise une clé composite pour éviter les doublons :
```python
track_key = f"{artist}|{title}|{album}"
```

Si la même clé est détectée deux fois de suite, le tracker ignore le second poll.

## 🐛 Dépannage

### Le tracker ne se connecte pas

**Problème** : "❌ Non connecté au serveur Roon"

**Solutions** :
1. Vérifiez que le serveur Roon est allumé et accessible
2. Vérifiez l'adresse IP dans `secrets.json`
3. Vérifiez que vous êtes sur le même réseau que Roon
4. Testez la connexion : `ping VOTRE_IP_ROON`

### Extension non autorisée

**Problème** : Le tracker se connecte mais ne capte rien

**Solutions** :
1. Ouvrez l'app Roon
2. Allez dans Settings > Extensions
3. Trouvez "AIME - AI Music Enabler"
4. Cliquez sur "Enable" ou "Authorize"

### Aucun track détecté

**Problème** : Le tracker tourne mais n'enregistre rien

**Solutions** :
1. Vérifiez qu'une zone Roon est active et en lecture
2. Vérifiez les logs : `tail -f /tmp/backend.log | grep -i roon`
3. Vérifiez la plage horaire (8h-22h par défaut)
4. Vérifiez le statut : zones_count doit être > 0

### Logs utiles

```bash
# Tous les logs Roon
tail -f /tmp/backend.log | grep -i roon

# Dernières écoutes Roon
curl http://localhost:8000/api/v1/history/tracks?source=roon

# Statut détaillé
curl http://localhost:8000/api/v1/services/roon-tracker/status | python3 -m json.tool
```

## 📈 Performances et Recommandations

### Intervalle de Polling

| Intervalle | Avantages | Inconvénients |
|------------|-----------|---------------|
| 60s | Réactivité maximale | Plus de charge réseau |
| **120s** | ✅ Équilibre optimal | Délai acceptable |
| 180s | Économie réseau | Peut manquer des tracks courts |

### Réseau et Latence

- Roon utilise **RAAT** (Roon Advanced Audio Transport)
- Latence typique : < 1ms sur réseau local
- Le tracker fonctionne sur le même réseau que Roon
- Aucun impact sur la qualité audio

## 🔐 Sécurité

- Le token Roon est stocké localement dans `secrets.json`
- Aucune donnée n'est envoyée à l'extérieur (sauf Spotify/IA pour enrichissement)
- Connexion locale uniquement (pas d'accès internet requis pour Roon)

## 🆚 Comparaison Last.fm vs Roon

| Aspect | Last.fm | Roon |
|--------|---------|------|
| **Source** | Service en ligne | Serveur local |
| **Réseau** | Internet requis | Local uniquement |
| **Latence** | Variable (API) | Très faible (< 1ms) |
| **Fiabilité** | Dépend du service | Très haute |
| **Configuration** | API Key + Username | IP + Autorisation |
| **Coût** | Gratuit | Abonnement Roon requis |

## 🎉 Utilisation Combinée

Les deux trackers peuvent fonctionner ensemble :

- **Roon** : Capture les écoutes locales (streaming, fichiers locaux)
- **Last.fm** : Capture TOUT (Spotify mobile, autres apps, etc.)
- **Déduplication automatique** : Pas de doublons grâce à la détection intelligente
- **Source tracking** : Chaque écoute garde sa source d'origine

## 📚 Ressources

- [Roon Labs Official](https://roonlabs.com/)
- [pyroon GitHub](https://github.com/pavoni/pyroon)
- [Roon API Documentation](https://github.com/RoonLabs/roon-api)
- [AIME Project](/)

---

**Version** : 4.0.0  
**Date** : 31 janvier 2026  
**Statut** : ✅ Production Ready
