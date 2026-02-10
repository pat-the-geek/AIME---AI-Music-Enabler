# 🔧 Diagnostic : Génération de Haïkus Quotidienne

**Date :** 10 février 2026  
**Problème :** La tâche de génération de haïkus quotidienne n'a jamais été exécutée

---

## 🔍 Diagnostic

### Symptômes
- ✅ Tâche planifiée pour 06:00 quotidiennement
- ❌ Statut : "Jamais exécutée"
- ❌ Aucune entrée en base de données pour cette tâche

### Cause Racine
**Le scheduler n'était pas en cours d'exécution.**

Bien que le scheduler soit marqué comme "actif" en base de données (`ServiceState.is_active = True`), l'instance APScheduler n'était pas démarrée. Cela signifie qu'aucune tâche ne pouvait s'exécuter.

### Vérifications Effectuées

1. **Base de Données** ✅
   - Scheduler marqué comme actif
   - Autres tâches ont des exécutions enregistrées
   - Tâche `generate_haiku_scheduled` : aucune exécution

2. **Configuration de la Tâche** ✅
   - Trigger correctement configuré : `cron[hour='6', minute='0']`
   - Timezone : Europe/Zurich (UTC+1)
   - Prochaine exécution calculée : 11/02/2026 06:00:00+01:00
   - Fonction liée : `_generate_random_haikus()`

3. **Test Manuel** ✅
   - La fonction s'exécute correctement
   - Génération de fichier réussie
   - Enregistrement en base de données OK

4. **Scheduler APScheduler** ❌ → ✅
   - État initial : `is_running = False`
   - **Problème identifié** : Le scheduler n'était pas démarré
   - Après démarrage : Tout fonctionne correctement

---

## ✅ Solution Appliquée

Le scheduler a été démarré manuellement via le script de diagnostic. La tâche devrait maintenant s'exécuter normalement.

**Prochaine exécution prévue :** 11/02/2026 à 06:00:00

---

## 🛠️ Comment Éviter ce Problème

### 1. Vérifier Régulièrement l'État du Scheduler

**Via l'API :**
```bash
curl http://localhost:8000/api/v1/services/scheduler/status | python3 -m json.tool
```

Vérifier que : `"running": true`

### 2. S'Assurer que le Backend Reste Actif

Le scheduler est géré par l'application backend (FastAPI/Uvicorn). Il ne fonctionne QUE si :
- ✅ L'application backend est en cours d'exécution
- ✅ Le scheduler a été démarré via `restore_active_services()`
- ✅ Aucune erreur n'a arrêté le scheduler

**Commande pour vérifier le backend :**
```bash
ps aux | grep uvicorn
```

### 3. Démarrer le Scheduler Automatiquement

Le scheduler devrait se démarrer automatiquement au lancement de l'application grâce à la fonction `restore_active_services()` appelée dans le lifecycle de FastAPI.

**Si ce n'est pas le cas :**
```bash
python3 backend/ensure_scheduler_running.py
```

### 4. Logs à Surveiller

Au démarrage de l'application, vérifier ces messages :
```
✅ Scheduler démarré avec tâches optimisées
✅ Services restaurés
```

Si le scheduler ne démarre pas :
```
❌ Erreur démarrage scheduler: [message d'erreur]
⏱️ Scheduler timeout après 15s - continuant
```

---

## 📊 État Actuel (Après Correction)

```json
{
    "scheduler": {
        "running": true,
        "job_count": 9
    },
    "generate_haiku_scheduled": {
        "id": "generate_haiku_scheduled",
        "name": "🎋 Génération de haïkus",
        "next_run": "2026-02-11T06:00:00+01:00",
        "last_execution": "2026-02-10T07:48:09.157479",
        "last_status": "success"
    }
}
```

**Tâches Planifiées :**
- 02:00 - Enrichissement quotidien
- 03:00 - Génération de magazines
- 04:00 - Sync Discogs
- **06:00 - Génération de haïkus** ✅
- 08:00 - Export Markdown
- 10:00 - Export JSON
- 12:00, 18:00, 00:00 - Optimisation IA (toutes les 6h)
- 20:00 Dimanche - Haïku hebdomadaire
- 03:00 (1er du mois) - Analyse mensuelle

---

## 🔧 Scripts Utiles

### Diagnostic Complet
```bash
python3 backend/diagnose_haiku_scheduler.py
```

**Effectue :**
- Vérification de la base de données
- Analyse de l'instance du scheduler
- Test du trigger cron
- Possibilité d'exécution manuelle

### S'Assurer que le Scheduler est Démarré
```bash
python3 backend/ensure_scheduler_running.py
```

**Effectue :**
- Vérification de l'état du scheduler
- Démarrage si nécessaire
- Mise à jour de la base de données
- Affichage du statut

---

## 📝 Recommandations

1. **Ne jamais arrêter le backend pendant la journée** si vous voulez que les tâches s'exécutent

2. **Surveiller les logs** pour détecter les erreurs de scheduler

3. **Vérifier l'API régulièrement** pour confirmer que `"running": true`

4. **En cas de redémarrage du système**, vérifier que le scheduler redémarre correctement

5. **Considérer l'utilisation d'un process manager** (systemd, pm2, supervisord) pour :
   - Redémarrer automatiquement le backend en cas de crash
   - Démarrer le backend au boot du système
   - Gérer les logs automatiquement

---

## ✅ Conclusion

**Problème résolu** : Le scheduler est maintenant démarré et la tâche de génération de haïkus devrait s'exécuter quotidiennement à 06:00.

**Prochaine action** : Vérifier demain matin (11/02/2026) que la tâche s'est bien exécutée en consultant :
- Les fichiers générés dans `data/scheduled-output/`
- Le statut via l'API : `/api/v1/services/scheduler/status`
- Les logs de l'application backend
