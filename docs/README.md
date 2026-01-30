# 📚 Documentation - AIME - AI Music Enabler

Bienvenue dans la documentation du projet AIME - AI Music Enabler !

## 🚀 Démarrage Rapide

**Nouveau sur le projet ?** Commencez ici :

1. 📖 [Guide de Démarrage Rapide](QUICKSTART.md) - Installation et premier lancement (5 min)
2. 🏗️ [Architecture du Projet](ARCHITECTURE.md) - Comprendre la structure technique
3. 🔧 [Guide de Dépannage](TROUBLESHOOTING.md) - Solutions aux problèmes courants ⭐ **Important!**

## 📋 Documentation Complète

### Pour les Utilisateurs

- **[README Principal](../README.md)** - Vue d'ensemble du projet
- **[Guide de Démarrage Rapide](QUICKSTART.md)** - Installation pas à pas
- **[STATUS](../STATUS.md)** - État actuel de l'application
- **[CHANGELOG](../CHANGELOG.md)** - Historique des modifications

### Pour les Développeurs

- **[Documentation API](API.md)** - Référence complète des endpoints REST
- **[Architecture](ARCHITECTURE.md)** - Structure technique détaillée
- **[Spécification](../SPECIFICATION-REACT-REBUILD.md)** - Cahier des charges complet
- **[Résumé du Projet](../PROJECT-SUMMARY.md)** - Ce qui a été créé et pourquoi

### Résolution de Problèmes

- **[Guide de Dépannage](TROUBLESHOOTING.md)** ⭐ **Consultez d'abord ce document!**
  - Python 3.14 incompatibilité
  - Erreurs de base de données
  - Problèmes de configuration
  - Reloads infinis du serveur
  - Et 7 autres problèmes documentés

## 🎯 Navigation par Besoin

### "Je veux installer l'application"
→ [QUICKSTART.md](QUICKSTART.md)

### "J'ai une erreur au démarrage"
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### "Je veux comprendre l'architecture"
→ [ARCHITECTURE.md](ARCHITECTURE.md)

### "Je veux utiliser l'API"
→ [API.md](API.md)

### "Je veux voir ce qui a été fait"
→ [PROJECT-SUMMARY.md](../PROJECT-SUMMARY.md)

### "Je veux savoir ce qui a changé"
→ [CHANGELOG.md](../CHANGELOG.md)

## 🐛 Problèmes Connus (Tous Résolus ✅)

Les problèmes suivants ont été identifiés et corrigés dans la version 4.0.1 :

1. ✅ **Python 3.14 Incompatibilité** - SQLAlchemy dev version requise
2. ✅ **Attribut "metadata" Réservé** - Renommé en album_metadata
3. ✅ **Import ForeignKey Manquant** - Ajouté dans playlist.py
4. ✅ **Chemin Base de Données** - Variable PROJECT_ROOT ajoutée
5. ✅ **Reloads Infinis Uvicorn** - Option --reload-dir app

Voir [TROUBLESHOOTING.md](TROUBLESHOOTING.md) pour les détails et solutions.

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
3. ✅ Lisez le [QUICKSTART.md](QUICKSTART.md)

### Si Vous Avez un Problème

1. 🔍 Consultez [TROUBLESHOOTING.md](TROUBLESHOOTING.md) en premier
2. 📝 Vérifiez les logs dans le terminal
3. 🧪 Testez le health endpoint: `curl http://localhost:8000/health`
4. 🗄️ Vérifiez que la base existe: `ls -lh data/musique.db`

### Pour Contribuer

1. Lisez l'[ARCHITECTURE.md](ARCHITECTURE.md) pour comprendre le code
2. Consultez l'[API.md](API.md) pour les endpoints
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

**Note**: Si vous lisez ce document pour la première fois, nous vous recommandons fortement de commencer par le [Guide de Démarrage Rapide](QUICKSTART.md) puis de consulter le [Guide de Dépannage](TROUBLESHOOTING.md) pour éviter les problèmes courants.
