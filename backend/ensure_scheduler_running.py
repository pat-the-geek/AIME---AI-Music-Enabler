#!/usr/bin/env python3
"""
Script pour s'assurer que le scheduler est démarré.
Peut être exécuté manuellement ou au démarrage du système.
"""
import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire backend au PYTHONPATH
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings
from app.services.scheduler_service import SchedulerService
from app.database import SessionLocal
from app.models import ServiceState
from datetime import datetime, timezone

async def ensure_scheduler_running():
    """S'assurer que le scheduler est démarré."""
    print("\n" + "="*80)
    print("  🔧 VÉRIFICATION DU SCHEDULER")
    print("="*80 + "\n")
    
    # Créer l'instance du scheduler
    settings = get_settings()
    config = {**settings.secrets, **settings.app_config}
    scheduler = SchedulerService(config)
    
    # Vérifier s'il est en cours d'exécution
    if scheduler.is_running:
        print("✅ Le scheduler est déjà en cours d'exécution")
        status = scheduler.get_status()
        print(f"   - Jobs actifs: {status['job_count']}")
        return 0
    
    # Démarrer le scheduler
    print("⚠️  Le scheduler n'est PAS en cours d'exécution")
    print("   Démarrage en cours...")
    
    try:
        await scheduler.start()
        print("✅ Scheduler démarré avec succès")
        
        # Mettre à jour l'état en base de données
        db = SessionLocal()
        try:
            scheduler_state = db.query(ServiceState).filter_by(service_name='scheduler').first()
            if scheduler_state is None:
                scheduler_state = ServiceState(service_name='scheduler')
                db.add(scheduler_state)
            scheduler_state.is_active = True
            scheduler_state.last_updated = datetime.now(timezone.utc)
            db.commit()
            print("✅ État enregistré en base de données")
        except Exception as e:
            print(f"⚠️  Erreur lors de l'enregistrement en base: {e}")
            db.rollback()
        finally:
            db.close()
        
        # Afficher le statut
        status = scheduler.get_status()
        print(f"\n📊 Statut du scheduler:")
        print(f"   - Running: {status['running']}")
        print(f"   - Jobs actifs: {status['job_count']}")
        print(f"\n🎋 Tâche génération de haïkus:")
        
        for job in status['jobs']:
            if job['id'] == 'generate_haiku_scheduled':
                print(f"   - Prochaine exécution: {job['next_run']}")
                print(f"   - Dernière exécution: {job['last_execution'] or 'Jamais'}")
                print(f"   - Statut: {job['last_status']}")
                break
        
        print("\n⚠️  IMPORTANT: Ne pas arrêter ce script si vous voulez que le scheduler continue.")
        print("   Pour que le scheduler reste actif en arrière-plan, laissez l'application")
        print("   backend (uvicorn) en cours d'exécution.")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du scheduler: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(ensure_scheduler_running())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
