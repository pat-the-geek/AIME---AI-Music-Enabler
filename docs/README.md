# 📚 Documentation - AIME - AI Music Enabler

Bienvenue dans la documentation du projet AIME - AI Music Enabler !

## � Structure de la documentation

### 📖 Documentation principale (ce dossier)
- **API.md** - Documentation complète de l'API REST
- **ARCHITECTURE.md** - Architecture technique du système
- **QUICKSTART.md** - Guide de démarrage rapide
- **TROUBLESHOOTING.md** - Résolution des problèmes courants
- **GITHUB-REPO-INFO.md** - Informations pour GitHub (description, topics, SEO)

### 📝 Historique des modifications (`/changelogs`)
- **CHANGELOG.md** - Journal principal des modifications
- **CHANGELOG-UI-ENRICHMENT.md** - Améliorations de l'interface utilisateur
- **CHANGELOG-UNIFIED-ALBUM-DISPLAY.md** - Unification de l'affichage des albums

### 🎵 Documentation des fonctionnalités (`/features`)
- **NOUVELLES-FONCTIONNALITES.md** - Dernières fonctionnalités ajoutées (v4.0.0)
- **JOURNAL-TIMELINE-DOC.md** - Documentation de la vue Journal/Timeline
- **LASTFM-IMPORT-TRACKER-DOC.md** - Tracker Last.fm et import d'historique
- **ROON-TRACKER-DOC.md** - Tracker Roon et configuration

### 🔧 Configuration (`/config`)
- **TRACKER-CONFIG-OPTIMALE.md** - Configuration optimale du tracker d'écoute

### 🐛 Debug et corrections (`/debug`)
- **DEBUG-DISCOGS.md** - Debug de l'intégration Discogs
- **EXPLICATION-404-DISCOGS.md** - Gestion des erreurs 404 Discogs
- **CORRECTIONS-SYNC-DISCOGS.md** - Corrections de synchronisation
- **AMELIORATIONS-SYNC-ENRICHIE.md** - Améliorations de la synchronisation
- **ENRICHISSEMENT-RETROACTIF.md** - Enrichissement rétroactif des données

### 🏗️ Spécifications techniques (`/specs`)
- **SPECIFICATION-REACT-REBUILD.md** - Spécifications du rebuild React/TypeScript

---

## 🚀 Démarrage Rapide

**Nouveau sur le projet ?** Commencez ici :

1. 📖 [Guide de Démarrage Rapide](guides/utilisateur/QUICKSTART.md) - Installation et premier lancement (5 min)
2. 🏗️ [Architecture du Projet](architecture/ARCHITECTURE.md) - Comprendre la structure technique
3. 🔧 [Guide de Dépannage](guides/troubleshooting/TROUBLESHOOTING.md) - Solutions aux problèmes courants ⭐ **Important!**

## 📋 Documentation Complète

### Pour les Utilisateurs

- **[README Principal](../README.md)** - Vue d'ensemble du projet
- **[Guide de Démarrage Rapide](guides/utilisateur/QUICKSTART.md)** - Installation pas à pas
- **[STATUS](archive/STATUS.md)** - État actuel de l'application
- **[Historique des modifications](changelogs/CHANGELOG.md)** - Toutes les versions

### Pour les Développeurs

- **[Documentation API](api/API.md)** - Référence complète des endpoints REST
- **[Architecture](architecture/ARCHITECTURE.md)** - Structure technique détaillée
- **[Spécifications](specs/)** - Cahiers des charges et specs techniques
- **[Résumé du Projet](archive/PROJECT-SUMMARY.md)** - Ce qui a été créé et pourquoi
- **[Nouvelles Fonctionnalités](features/NOUVELLES-FONCTIONNALITES.md)** - Version 4.0.0

### Résolution de Problèmes

- **[Guide de Dépannage](guides/troubleshooting/TROUBLESHOOTING.md)** ⭐ **Consultez d'abord ce document!**
  - Python 3.14 incompatibilité
  - Erreurs de base de données
  - Problèmes de configuration
  - Reloads infinis du serveur
  - Et 7 autres problèmes documentés
- **[Debug et Corrections](debug/)** - Historique des problèmes résolus

## 🎯 Navigation par Besoin

### "Je veux installer l'application"
→ [QUICKSTART.md](guides/utilisateur/QUICKSTART.md)

### "J'ai une erreur au démarrage"
→ [TROUBLESHOOTING.md](guides/troubleshooting/TROUBLESHOOTING.md)

### "Je veux comprendre l'architecture"
→ [ARCHITECTURE.md](architecture/ARCHITECTURE.md)

### "Je veux utiliser l'API"
→ [API.md](api/API.md)

### "Je veux voir les nouvelles fonctionnalités"
→ [features/NOUVELLES-FONCTIONNALITES.md](features/NOUVELLES-FONCTIONNALITES.md)

---

## 📸 Captures d'Écran

Voici un aperçu visuel de l'application :

### Collection & Albums
![Collection - Albums](../Screen%20captures/Collection%20-%20Albums.png)
![Détail Album](../Screen%20captures/Collection%20-%20Album%20-%20Detail.png)

### Journal d'Écoute
![Journal d'Écoute](../Screen%20captures/Journal.png)

### Timeline Horaire
![Timeline](../Screen%20captures/TimeLine.png)
![Détail Timeline](../Screen%20captures/TimeLine%20-%20Detail.png)

### Paramètres & Trackers
![Paramètres Trackers](../Screen%20captures/Settings%20-%20Roon%20-%20Lastfm%20-%20Trackers.png)

---

## ✍️ Conventions pour la documentation

### Placement des nouveaux fichiers

| Type de document | Emplacement | Exemple |
|------------------|-------------|---------|
| Changelog général | `/docs/changelogs/` | `CHANGELOG-FEATURE-X.md` |
| Nouvelle fonctionnalité | `/docs/features/` | `PLAYLIST-GENERATOR-DOC.md` |
| Configuration | `/docs/config/` | `SCHEDULER-CONFIG.md` |
| Debug/Correction | `/docs/debug/` | `FIX-SPOTIFY-API.md` |
| Spécification technique | `/docs/specs/` | `SPEC-MOBILE-APP.md` |
| Documentation API/Architecture | `/docs/` | `API-v2.md` |

### Nommage des fichiers
- Utiliser des MAJUSCULES pour les fichiers de documentation
- Séparer les mots par des tirets `-`
- Suffixer avec `-DOC` pour les documentations de fonctionnalités
- Suffixer avec `-SPEC` pour les spécifications
- Préfixer avec `CHANGELOG-` pour les historiques
- Préfixer avec `DEBUG-` ou `FIX-` pour les corrections

### Format recommandé
- Format : **Markdown** (`.md`)
- Encodage : **UTF-8**
- Langue : Français pour la doc interne, Anglais pour l'API publique
- Structure : Titre principal H1, sections H2-H3, emojis pour la navigation

---

## 🔄 Mise à jour de la documentation

### Lors de l'ajout d'une fonctionnalité
1. Créer un fichier dans `/docs/features/` avec description complète
2. Ajouter une entrée dans `/docs/changelogs/CHANGELOG.md`
3. Mettre à jour `/docs/API.md` si nouveaux endpoints
4. Mettre à jour le `README.md` principal si impact majeur

### Lors d'une correction de bug
1. Documenter dans `/docs/debug/` si le fix est complexe
2. Ajouter une note dans le changelog
3. Mettre à jour `/docs/TROUBLESHOOTING.md` si applicable

### Lors d'un changement de configuration
1. Mettre à jour `/docs/config/`
2. Documenter les migrations nécessaires
3. Ajouter des exemples de configuration

---

## 📊 Documentation vivante

Cette documentation est **vivante** et doit être mise à jour en continu :
- ✅ Toujours synchroniser avec le code
- ✅ Inclure des exemples concrets
- ✅ Maintenir les liens à jour
- ✅ Supprimer la documentation obsolète
- ✅ Versionner les changements majeurs

### "Je veux voir ce qui a été fait"
→ [PROJECT-SUMMARY.md](archive/PROJECT-SUMMARY.md)

### "Je veux savoir ce qui a changé"
→ [CHANGELOG.md](../CHANGELOG.md)

## 🐛 Problèmes Connus (Tous Résolus ✅)

Les problèmes suivants ont été identifiés et corrigés dans la version 4.0.1 :

1. ✅ **Python 3.14 Incompatibilité** - SQLAlchemy dev version requise
2. ✅ **Attribut "metadata" Réservé** - Renommé en album_metadata
3. ✅ **Import ForeignKey Manquant** - Ajouté dans playlist.py
4. ✅ **Chemin Base de Données** - Variable PROJECT_ROOT ajoutée
5. ✅ **Reloads Infinis Uvicorn** - Option --reload-dir app

Voir [TROUBLESHOOTING.md](guides/troubleshooting/TROUBLESHOOTING.md) pour les détails et solutions.

## 📊 Structure de la Documentation

```
docs/
├── README.md               # 👈 Vous êtes ici
├── QUICKSTART.md          # Guide d'installation rapide
├── API.md                 # Documentation des endpoints
├── ARCHITECTURE.md        # Architecture technique
└── TROUBLESHOOTING.md     # Guide de dépannage ⭐

Racine/
├── README.md              # Vue d'ensemble générale
├── STATUS.md              # État de l'application
├── CHANGELOG.md           # Historique des versions
├── PROJECT-SUMMARY.md     # Résumé du projet
└── SPECIFICATION-REACT-REBUILD.md  # Spécification complète
```

## 🔗 Liens Rapides

### URLs de l'Application (après démarrage)

- **Frontend**: http://localhost:5173
- **API Backend**: http://localhost:8000
- **Documentation API Interactive**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

### Commandes Utiles

```bash
# Installer
./scripts/setup.sh

# Démarrer
./scripts/start-dev.sh

# Tester le backend
curl http://localhost:8000/health

# Voir les logs
tail -f backend/logs/app.log  # si logs activés
```

## 💡 Conseils

### Avant de Commencer

1. ✅ Vérifiez que vous avez Python 3.10-3.13 (pas 3.14 sauf si prêt pour SQLAlchemy dev)
2. ✅ Vérifiez que vous avez Node.js 18+
3. ✅ Lisez le [QUICKSTART.md](guides/utilisateur/QUICKSTART.md)

### Si Vous Avez un Problème

1. 🔍 Consultez [TROUBLESHOOTING.md](guides/troubleshooting/TROUBLESHOOTING.md) en premier
2. 📝 Vérifiez les logs dans le terminal
3. 🧪 Testez le health endpoint: `curl http://localhost:8000/health`
4. 🗄️ Vérifiez que la base existe: `ls -lh data/musique.db`

### Pour Contribuer

1. Lisez l'[ARCHITECTURE.md](architecture/ARCHITECTURE.md) pour comprendre le code
2. Consultez l'[API.md](api/API.md) pour les endpoints
3. Suivez les conventions TypeScript/Python du projet
4. Documentez vos changements dans [CHANGELOG.md](../CHANGELOG.md)

## 📞 Support

Pour toute question non couverte dans la documentation :

1. Vérifiez que vous avez la dernière version
2. Consultez les [issues GitHub](#) si le projet est sur GitHub
3. Vérifiez les logs d'erreur complets
4. Créez une issue avec :
   - Version de Python et Node.js
   - Système d'exploitation
   - Message d'erreur complet
   - Étapes pour reproduire

---

**Dernière mise à jour**: 30 janvier 2026  
**Version**: 4.0.1  
**Statut**: ✅ Application Opérationnelle

**Note**: Si vous lisez ce document pour la première fois, nous vous recommandons fortement de commencer par le [Guide de Démarrage Rapide](guides/utilisateur/QUICKSTART.md) puis de consulter le [Guide de Dépannage](guides/troubleshooting/TROUBLESHOOTING.md) pour éviter les problèmes courants.
