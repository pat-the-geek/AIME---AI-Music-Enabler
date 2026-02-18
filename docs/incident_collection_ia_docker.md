# Incident : Collections IA vides après déploiement Docker

## Symptômes
- La création de collections d'albums par IA fonctionne côté logs backend (albums créés, enrichis, descriptions générées).
- Les collections apparaissent vides côté API et frontend (album_count = 0, aucune image).
- Aucun message d'erreur bloquant dans les logs backend.

## Diagnostic
- Les albums étaient bien créés, mais non associés à la collection (problème d'ID lors de l'appel à add_albums_to_collection).
- Les IDs d'albums n'étaient pas toujours disponibles (flush manquant avant récupération des IDs).
- Erreurs SQLAlchemy sur objets supprimés ou expirés lors du flush.
- Timeout frontend (nginx) lors de requêtes longues.

## Correctifs appliqués
1. Ajout d'un flush systématique avant récupération des IDs d'albums.
2. Correction de l'indentation du bloc environment dans docker-compose.yml pour garantir la prise en compte des variables d'environnement.
3. Augmentation du proxy_read_timeout nginx à 300s pour éviter les timeouts frontend.
4. Sécurisation de l'affichage des artistes pour éviter les erreurs sur objets supprimés.

## Vérification post-correction
- Les albums sont bien associés à la collection (album_count > 0, images présentes).
- Les collections sont visibles et complètes côté API et frontend.
- Les logs backend ne montrent plus d'erreurs critiques.
- Les variables d'environnement sont bien présentes dans le conteneur.

## Recommandations pour le futur déploiement
- Toujours vérifier la présence des variables d'environnement dans le conteneur (printenv).
- Tester la création de collection IA après chaque déploiement.
- Vérifier les logs backend et frontend pour tout incident.
- Documenter toute modification de la logique SQLAlchemy (flush, commit, refresh).
- S'assurer que le proxy nginx a un timeout adapté.

## Publication
- Ce document peut être publié sur GitHub dans le dossier docs/ ou dans un README technique.
- Il servira de référence pour les futures migrations et déploiements.

---

**Incident résolu le 18 février 2026.**
