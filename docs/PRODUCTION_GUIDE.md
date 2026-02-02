# 📖 GUIDE DE PRODUCTION - AIME

## 🚀 Démarrage

### 1. Service Scheduler Automatique
```bash
# Option A: systemd (recommandé)
sudo cp /tmp/aime-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable aime-scheduler
sudo systemctl start aime-scheduler

# Vérifier le statut:
sudo systemctl status aime-scheduler
sudo journalctl -u aime-scheduler -f

# Option B: cron (alternatif)
crontab -e
# Ajouter: 0 2 * * * cd /path/to/aime && python3 scripts/improvement_pipeline.py
```

### 2. API Backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend
```bash
cd frontend
npm start
```

## 📊 Monitoring

### Vérifier l'amélioration automatique
```bash
python3 scripts/audit_database.py
python3 scripts/generate_audit_report.py
```

### Voir les logs
```bash
tail -f logs/improvement.log
```

### État des albums
```bash
python3 scripts/validate_data.py
```

## 🔧 Maintenance

### Enrichir les images manuellement
```bash
python3 scripts/auto_enrichment.py
```

### Corriger les artistes
```bash
python3 scripts/fix_malformed_artists.py
```

### Ajouter les descriptions
```bash
python3 scripts/enrich_euria_descriptions.py
```

## 🆘 Troubleshooting

### Base de données lente
- Vérifier l'espace disque
- Exécuter: `python3 scripts/cleanup_check.py`

### Imports LastFM qui échouent
- Vérifier les credentials dans `config/secrets.json`
- Vérifier la connexion Internet
- Voir logs dans `logs/`

### Scheduler ne fonctionne pas
```bash
# Vérifier le service
systemctl status aime-scheduler

# Redémarrer
sudo systemctl restart aime-scheduler

# Logs
sudo journalctl -u aime-scheduler -n 50
```

## 📋 Configuration

### Enrichissement (config/enrichment_config.json)
```json
{
  "auto_enrichment": {
    "enabled": true,
    "schedule": "daily_02:00",
    "sources": ["musicbrainz", "discogs", "spotify"]
  }
}
```

### Secrets (config/secrets.json - NE PAS COMMITER)
```json
{
  "lastfm": {
    "api_key": "...",
    "api_secret": "...",
    "username": "..."
  },
  "spotify": {
    "client_id": "...",
    "client_secret": "..."
  }
}
```

## ✅ Checklist Hebdomadaire

- [ ] Vérifier le score qualité des données
- [ ] Vérifier les logs du scheduler
- [ ] Backup base de données effectué
- [ ] Pas d'erreurs dans les imports
- [ ] Images enrichies progressivement
- [ ] Descriptions générées

## 📞 Support

En cas de problème:
1. Consulter les logs: `python3 scripts/validate_data.py`
2. Exécuter audit: `python3 scripts/audit_database.py`
3. Vérifier configuration: `cat config/deployment_config.json`
4. Redémarrer services si nécessaire

---

**Date de déploiement**: 2026-02-02 18:55:19
**Status**: ✅ Production
