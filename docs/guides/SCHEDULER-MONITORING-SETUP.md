# 🔧 Configuration de la Surveillance Automatique du Scheduler

## Objectif

Mettre en place une surveillance automatique du scheduler pour s'assurer qu'il reste actif et que les tâches s'exécutent correctement.

---

## 📋 Scripts Disponibles

### 1. `monitor_scheduler.py` - Surveillance Rapide
**Usage :** Vérification ponctuelle de l'état du scheduler

```bash
python3 backend/monitor_scheduler.py
```

**Ce qu'il fait :**
- ✅ Vérifie l'état du scheduler via l'API
- ✅ Affiche l'état de la tâche haïku
- ✅ Redémarre le scheduler si nécessaire

### 2. `diagnose_haiku_scheduler.py` - Diagnostic Complet
**Usage :** Analyse approfondie en cas de problème

```bash
python3 backend/diagnose_haiku_scheduler.py
```

**Ce qu'il fait :**
- ✅ Analyse la base de données
- ✅ Inspecte l'instance du scheduler
- ✅ Teste le trigger cron
- ✅ Permet l'exécution manuelle

### 3. `ensure_scheduler_running.py` - Démarrage Forcé
**Usage :** Démarrer le scheduler manuellement

```bash
python3 backend/ensure_scheduler_running.py
```

**Ce qu'il fait :**
- ✅ Démarre le scheduler s'il est arrêté
- ✅ Met à jour la base de données
- ✅ Affiche le statut complet

---

## 🤖 Automatisation avec Cron (macOS/Linux)

### Configuration Recommandée

Ajouter une tâche cron pour surveiller le scheduler toutes les heures :

```bash
# Éditer le crontab
crontab -e
```

Ajouter cette ligne :
```bash
# Surveillance du scheduler AIME toutes les heures
0 * * * * cd /Users/patrickostertag/Documents/DataForIA/AIME\ -\ AI\ Music\ Enabler/backend && /usr/local/bin/python3 monitor_scheduler.py >> /tmp/scheduler-monitor.log 2>&1
```

**Adaptation nécessaire :**
- Remplacer `/Users/patrickostertag/...` par le chemin absolu de votre projet
- Remplacer `/usr/local/bin/python3` par le chemin de votre Python (trouver avec `which python3`)

### Vérifier les Logs

```bash
# Voir les dernières vérifications
tail -f /tmp/scheduler-monitor.log

# Voir l'historique complet
cat /tmp/scheduler-monitor.log
```

---

## 🔔 Notifications Optionnelles

### Via Email (nécessite configuration SMTP)

Modifier `monitor_scheduler.py` pour ajouter :

```python
def send_alert_email(subject, message):
    """Envoyer une alerte par email."""
    import smtplib
    from email.mime.text import MIMEText
    
    # Configuration à adapter
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "votre-email@gmail.com"
    receiver_email = "votre-email@gmail.com"
    password = "votre-mot-de-passe"
    
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
    except Exception as e:
        print(f"Erreur envoi email: {e}")
```

Appeler dans `main()` si le scheduler est arrêté :
```python
if not is_running:
    send_alert_email(
        "⚠️ AIME Scheduler Arrêté",
        f"Le scheduler AIME s'est arrêté à {datetime.now()}"
    )
```

### Via Système de Notification macOS

```bash
# Dans le script monitor_scheduler.py, ajouter :
osascript -e 'display notification "Le scheduler AIME s\'est arrêté" with title "Alerte AIME"'
```

---

## 🚀 Configuration au Démarrage du Système

### Option 1 : LaunchAgent (macOS)

Créer `/Users/patrickostertag/Library/LaunchAgents/com.aime.scheduler-monitor.plist` :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aime.scheduler-monitor</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend/monitor_scheduler.py</string>
    </array>
    
    <key>StartInterval</key>
    <integer>3600</integer> <!-- Toutes les heures -->
    
    <key>StandardOutPath</key>
    <string>/tmp/scheduler-monitor.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/scheduler-monitor-error.log</string>
    
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Charger le LaunchAgent :
```bash
launchctl load ~/Library/LaunchAgents/com.aime.scheduler-monitor.plist
```

Décharger (si besoin) :
```bash
launchctl unload ~/Library/LaunchAgents/com.aime.scheduler-monitor.plist
```

### Option 2 : Systemd (Linux)

Créer `/etc/systemd/system/aime-scheduler-monitor.service` :

```ini
[Unit]
Description=AIME Scheduler Monitor
After=network.target

[Service]
Type=simple
User=patrickostertag
WorkingDirectory=/path/to/AIME/backend
ExecStart=/usr/bin/python3 monitor_scheduler.py
Restart=always
RestartSec=3600

[Install]
WantedBy=multi-user.target
```

Activer et démarrer :
```bash
sudo systemctl enable aime-scheduler-monitor
sudo systemctl start aime-scheduler-monitor
sudo systemctl status aime-scheduler-monitor
```

---

## 📊 Monitoring Dashboard (Optionnel)

Créer un endpoint d'API pour le monitoring externe :

Dans `backend/app/api/v1/tracking/services.py` :

```python
@router.get("/scheduler/health")
async def scheduler_health():
    """Health check pour monitoring externe."""
    scheduler = get_scheduler()
    
    if not scheduler.is_running:
        raise HTTPException(status_code=503, detail="Scheduler not running")
    
    status = scheduler.get_status()
    
    # Vérifier la tâche haiku
    haiku_task = next(
        (job for job in status['jobs'] if job['id'] == 'generate_haiku_scheduled'), 
        None
    )
    
    if not haiku_task:
        raise HTTPException(status_code=503, detail="Haiku task not found")
    
    return {
        "status": "healthy",
        "scheduler_running": True,
        "job_count": status['job_count'],
        "haiku_task": {
            "next_run": haiku_task['next_run'],
            "last_execution": haiku_task['last_execution'],
            "last_status": haiku_task['last_status']
        }
    }
```

Utiliser avec un service de monitoring (UptimeRobot, Pingdom, etc.) :
```
GET http://localhost:8000/api/v1/services/scheduler/health
```

---

## ✅ Checklist de Vérification

Avant de considérer la surveillance comme configurée :

- [ ] Les scripts de monitoring fonctionnent correctement
- [ ] Le cron ou LaunchAgent est configuré
- [ ] Les logs sont accessibles et lisibles
- [ ] Une notification est testée (si configurée)
- [ ] Le scheduler redémarre automatiquement si arrêté
- [ ] La tâche haïku s'exécute quotidiennement (vérifier après 24h)

---

## 🔍 Commandes de Vérification Rapide

```bash
# Vérifier l'état via l'API
curl -s http://localhost:8000/api/v1/services/scheduler/status | python3 -m json.tool

# Vérifier le backend
ps aux | grep uvicorn

# Voir les logs du monitoring
tail -f /tmp/scheduler-monitor.log

# Exécuter manuellement la surveillance
python3 backend/monitor_scheduler.py

# Vérifier le cron
crontab -l

# Vérifier le LaunchAgent (macOS)
launchctl list | grep aime
```

---

## 📞 En Cas de Problème

1. **Le scheduler ne redémarre pas automatiquement**
   - Vérifier que le backend est en cours d'exécution
   - Consulter les logs : `/tmp/scheduler-monitor-error.log`
   - Redémarrer manuellement : `python3 backend/ensure_scheduler_running.py`

2. **Les notifications ne fonctionnent pas**
   - Vérifier la configuration SMTP
   - Tester l'envoi d'email manuellement
   - Vérifier les permissions sur macOS (Notifications)

3. **Le cron ne s'exécute pas**
   - Vérifier les chemins absolus
   - Vérifier les permissions d'exécution : `chmod +x backend/*.py`
   - Consulter les logs système : `/var/log/cron` (Linux) ou `log show --predicate 'process == "cron"' --last 1h` (macOS)

---

## 🎯 Résumé

Avec cette configuration :
- ✅ Le scheduler est surveillé automatiquement
- ✅ Le redémarrage automatique est assuré
- ✅ Les problèmes sont détectés rapidement
- ✅ La tâche haïku s'exécutera quotidiennement sans intervention
