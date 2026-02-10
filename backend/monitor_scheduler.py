#!/usr/bin/env python3
"""
Script de surveillance du scheduler - À exécuter régulièrement (via cron par exemple)
pour s'assurer que le scheduler reste actif.
"""
import asyncio
import sys
import requests
from pathlib import Path
from datetime import datetime

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def check_scheduler_via_api():
    """Vérifier l'état du scheduler via l'API."""
    try:
        response = requests.get('http://localhost:8000/api/v1/services/scheduler/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('running', False), data
        else:
            print(f"❌ Erreur API: Status code {response.status_code}")
            return False, None
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter à l'API (backend probablement arrêté)")
        return False, None
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False, None

async def restart_scheduler_if_needed():
    """Redémarrer le scheduler si nécessaire."""
    from app.core.config import get_settings
    from app.services.scheduler_service import SchedulerService
    from app.database import SessionLocal
    from app.models import ServiceState
    from datetime import timezone
    
    settings = get_settings()
    config = {**settings.secrets, **settings.app_config}
    scheduler = SchedulerService(config)
    
    if not scheduler.is_running:
        print("⚠️  Scheduler arrêté - tentative de redémarrage...")
        try:
            await scheduler.start()
            
            # Mettre à jour la base
            db = SessionLocal()
            try:
                scheduler_state = db.query(ServiceState).filter_by(service_name='scheduler').first()
                if scheduler_state is None:
                    scheduler_state = ServiceState(service_name='scheduler')
                    db.add(scheduler_state)
                scheduler_state.is_active = True
                scheduler_state.last_updated = datetime.now(timezone.utc)
                db.commit()
                print("✅ Scheduler redémarré avec succès")
                return True
            finally:
                db.close()
        except Exception as e:
            print(f"❌ Erreur lors du redémarrage: {e}")
            return False
    else:
        print("✅ Scheduler déjà actif")
        return True

def main():
    """Point d'entrée principal."""
    print(f"\n{'='*80}")
    print(f"  🔍 Surveillance Scheduler - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # 1. Vérifier via l'API d'abord
    print("1️⃣  Vérification via l'API...")
    is_running, data = check_scheduler_via_api()
    
    if is_running:
        print("✅ Scheduler actif via l'API")
        
        # Vérifier la tâche haiku spécifiquement
        for job in data.get('jobs', []):
            if job['id'] == 'generate_haiku_scheduled':
                print(f"\n🎋 Tâche Génération de Haïkus:")
                print(f"   - Prochaine exécution: {job['next_run']}")
                print(f"   - Dernière exécution: {job['last_execution'] or 'Jamais'}")
                print(f"   - Statut: {job['last_status']}")
                
                if job['last_execution'] is None:
                    print("   ⚠️  Attention: La tâche n'a jamais été exécutée")
                break
        
        print("\n✅ Tout va bien - Aucune action nécessaire")
        return 0
    else:
        print("⚠️  Scheduler non actif ou API inaccessible")
        print("\n2️⃣  Tentative de redémarrage direct...")
        
        # Essayer de redémarrer directement
        success = asyncio.run(restart_scheduler_if_needed())
        
        if success:
            print("\n✅ Problème résolu")
            return 0
        else:
            print("\n❌ Impossible de redémarrer le scheduler")
            print("   Actions possibles:")
            print("   1. Vérifier que le backend est en cours d'exécution")
            print("   2. Consulter les logs de l'application")
            print("   3. Redémarrer manuellement le backend")
            return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
