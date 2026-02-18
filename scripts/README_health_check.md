# Health Check du déploiement Docker

Ce script permet de vérifier automatiquement la santé du déploiement AIME - AI Music Enabler sur Docker.

## Utilisation

1. Rendez le script exécutable :
   ```bash
   chmod +x scripts/health_check.sh
   ```
2. Lancez le check :
   ```bash
   ./scripts/health_check.sh
   ```

## Vérifications effectuées
- État des conteneurs Docker (backend et frontend)
- Présence des variables d'environnement essentielles dans le backend
- Fonctionnement de l'API backend (endpoint /health)
- Création d'une collection IA (simulation)
- Association d'albums à la collection

## Résultat
- Si tous les checks sont OK, le déploiement est validé.
- En cas d'échec, le script affiche le détail du problème.

## À intégrer dans la CI/CD
- Ce script peut être utilisé dans un pipeline CI/CD pour valider automatiquement chaque déploiement.

---

Pour toute question ou amélioration, contactez l'équipe technique.
