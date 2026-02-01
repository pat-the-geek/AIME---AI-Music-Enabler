# 🛡️ Robustness Improvements - Quick Start

L'application AIME a reçu des améliorations majeures de robustesse. Voici comment les utiliser.

## ⚡ Quick Overview

### Backend
- ✅ **Retry Logic**: Auto-retry 3x avec backoff exponentiel
- ✅ **Circuit Breaker**: Protège les services externes
- ✅ **Exception Handling**: Global, typé, avec messages clairs
- ✅ **Timeouts**: Evite les requêtes infinies
- ✅ **Rate Limiting**: Respecte les limites d'API

### Frontend
- ✅ **Auto Retry**: 3x sur erreurs réseau/timeout/5xx
- ✅ **Error Boundary**: Capture les erreurs non gérées
- ✅ **User Feedback**: Snackbars + messages explicites
- ✅ **Network Resilience**: Gère connexions flaky

---

## 📂 Fichiers Clés

### Backend
```
backend/app/core/
├── exceptions.py        # Exceptions typées
├── retry.py            # Retry + Circuit Breaker
└── exception_handler.py # Exception handlers globaux
```

### Frontend
```
frontend/src/
├── api/client.ts       # Client avec retry auto
├── components/ErrorBoundary.tsx
├── hooks/useApiError.ts
└── hooks/useSnackbar.ts
```

---

## 🔧 Configuration

### Backend Timeouts
```python
# Services AI
timeout = 45.0  # 45 secondes

# Autres services
timeout = 30.0  # 30 secondes

# Database
# Utilise timeout de SQLAlchemy par défaut
```

### Frontend Timeouts
```typescript
// HTTP requests
timeout: 30000,  // 30 secondes

// Retry config
MAX_RETRIES = 3
RETRY_DELAY = 1000  // 1s, puis 2s, 4s...
```

---

## 🧪 Tester les Améliorations

### 1. Tester Network Resilience
```bash
# Terminal 1: Démarrer l'app
./scripts/start-dev.sh

# Terminal 2: Simuler erreur réseau
sudo ifconfig en0 down  # Couper le réseau

# Frontend devrait afficher: "Erreur réseau. Vérification..."
# Après réactivation du réseau, devrait retry automatiquement

sudo ifconfig en0 up   # Rétablir le réseau
```

### 2. Tester Timeout Handling
```bash
# Ajouter delay dans un endpoint (dans app/api/v1/history.py)
import time
time.sleep(35)  # Plus que le timeout de 30s

# Frontend devrait afficher timeout + retry auto
```

### 3. Tester Circuit Breaker
```bash
# Arrêter un service (ex: EurIA API)
# Essayer de générer descriptions IA

# Après 5+ failures:
# - Circuit breaker s'ouvre
# - Service retourne message par défaut
# - Tentatives bloquées pendant 5 minutes
# - Puis essai en HALF_OPEN
```

### 4. Exécuter les Tests
```bash
cd "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"
python3 scripts/test_robustness.py
```

---

## 📊 Scénarios Gérés

| Scénario | Comportement |
|----------|--------------|
| Network down | Retry auto 3x, message utilisateur |
| API timeout (>30s) | Fail, retry 3x avec backoff |
| 503 Service Unavailable | Retry 3x puis circuit breaker |
| Rate limiting (429) | Retry 3x avec délai exponentiel |
| Invalid data | Skip + log, ne pas bloquer |
| Unhandled exception | Error Boundary affiche message |
| Request validation error | 422 avec détails des erreurs |

---

## 🎯 Best Practices pour les Développeurs

### Nouvelle API Endpoint
```python
# ✅ Bon
@router.post("/my-endpoint")
async def my_endpoint():
    try:
        result = await external_service()
        return result
    except HTTPException:
        raise  # FastAPI gère
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        raise HTTPException(status_code=500)

# ❌ Mauvais
@router.post("/my-endpoint")
async def my_endpoint():
    result = external_service()  # Peut crash
    return result
```

### Nouveau Service Externe
```python
# ✅ Bon - avec retry et circuit breaker
from app.core.retry import CircuitBreaker, retry_with_backoff

my_breaker = CircuitBreaker("MyService")

@retry_with_backoff(max_attempts=3)
async def call_external_service():
    try:
        result = await my_breaker.call_async(api_call)
        return result
    except CircuitBreakerOpen:
        return fallback_value
```

### Frontend Mutation
```typescript
// ✅ Bon - avec gestion d'erreur
const mutation = useMutation({
  mutationFn: async () => await apiClient.post('/api/...'),
  onSuccess: (data) => {
    showSuccess('✅ Success')
  },
  onError: (error: AxiosError) => {
    const message = getErrorMessage(error)
    showError(`❌ ${message}`)
  }
})
```

---

## 🔍 Debugging

### Backend Logging
```python
# Activer debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Chercher les patterns:
# "❌" = Erreur
# "⚠️" = Warning
# "✅" = Succès
# "🔴" = Circuit breaker ouvert
# "🟡" = Circuit breaker HALF_OPEN
# "🟢" = Circuit breaker fermé
```

### Frontend Logging
```typescript
// Dans DevTools console
// Chercher "Retry X/3" pour voir les tentatives
console.log("Appel API échoué, retry automatique...")
```

---

## 📈 Monitoring

### Endpoints de Santé
```bash
# Health check simple
curl http://localhost:8000/health

# Readiness (prêt pour trafic)
curl http://localhost:8000/ready

# Réponse type:
{
  "status": "ok",
  "version": "4.0.0",
  "database": "connected",
  "external_services": {
    "discogs": "ok",
    "spotify": "ok",
    "euria": "circuit_open"  // Problème
  }
}
```

---

## 🚨 Troubleshooting

### "Circuit breaker ouvert"
**Cause**: 5+ erreurs d'affilée  
**Solution**: 
1. Vérifier la connection/santé du service
2. Attendre 5 minutes pour recovery timeout
3. Vérifier les logs pour détails

### "Timeout après 30s"
**Cause**: Requête trop lente  
**Solution**:
1. Vérifier performance du backend
2. Vérifier réseau
3. Augmenter timeout si nécessaire (code)

### "Error Boundary affiche erreur"
**Cause**: Erreur non gérée dans React  
**Solution**:
1. Vérifier console pour stack trace
2. Créer issue avec détails
3. Cliquer "Réessayer" pour continuer

---

## 📚 Documentation Complète

Pour la documentation détaillée, voir:
- **`docs/ROBUSTNESS-IMPROVEMENTS.md`**: Guide complet
- **`ROBUSTNESS-SUMMARY.md`**: Résumé des changements
- **Code docstrings**: Voir code source

---

## 🎓 Ressources

- [Circuit Breaker Pattern](https://en.wikipedia.org/wiki/Circuit_breaker)
- [Exponential Backoff](https://en.wikipedia.org/wiki/Exponential_backoff)
- [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
- [Axios Interceptors](https://axios-http.com/docs/interceptors)

---

## ✅ Vérification

Avant de déployer, vérifier:
- [ ] `python3 scripts/test_robustness.py` passe
- [ ] Backend démarre sans erreurs
- [ ] Frontend compile (npm run build)
- [ ] Health check retourne status "ok"
- [ ] Tester un appel API en offline mode

---

**Version**: 4.0.0+robustness  
**Date**: 31 janvier 2026  
**Status**: ✅ Production Ready
