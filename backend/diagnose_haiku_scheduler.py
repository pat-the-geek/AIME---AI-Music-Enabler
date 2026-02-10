#!/usr/bin/env python3
"""
Diagnostic pour comprendre pourquoi la génération de haïkus n'est jamais exécutée.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Ajouter le répertoire backend au PYTHONPATH
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models import ScheduledTaskExecution, ServiceState
from app.core.config import get_settings
from app.services.scheduler_service import SchedulerService

def print_section(title):
    """Afficher un titre de section."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def check_database_state():
    """Vérifier l'état du scheduler dans la base de données."""
    print_section("1️⃣  ÉTAT DE LA BASE DE DONNÉES")
    
    db = SessionLocal()
    try:
        # Vérifier l'état du service scheduler
        scheduler_state = db.query(ServiceState).filter_by(service_name='scheduler').first()
        if scheduler_state:
            print(f"✅ Scheduler trouvé en base:")
            print(f"   - Actif: {scheduler_state.is_active}")
            print(f"   - Dernière mise à jour: {scheduler_state.last_updated}")
        else:
            print("⚠️  Scheduler NON trouvé en base de données")
            print("   Cela signifie qu'il devrait être démarré automatiquement")
        
        print()
        
        # Vérifier les exécutions de tâches
        haiku_task = db.query(ScheduledTaskExecution).filter_by(
            task_id='generate_haiku_scheduled'
        ).first()
        
        print(f"📋 Tâche 'generate_haiku_scheduled' en base:")
        if haiku_task:
            print(f"   - Nom: {haiku_task.task_name}")
            print(f"   - Dernière exécution: {haiku_task.last_executed or 'Jamais'}")
            print(f"   - Statut: {haiku_task.last_status or 'N/A'}")
            print(f"   - Prochaine exécution: {haiku_task.next_run_time or 'N/A'}")
            print(f"   - Nombre d'exécutions: {haiku_task.execution_count or 0}")
        else:
            print("   ❌ Aucune entrée trouvée pour cette tâche")
            print("   Cela signifie qu'elle n'a jamais été exécutée")
        
        print()
        
        # Lister toutes les tâches enregistrées
        all_tasks = db.query(ScheduledTaskExecution).all()
        print(f"📊 Toutes les tâches en base ({len(all_tasks)}):")
        for task in all_tasks:
            status_icon = "✅" if task.last_status == "success" else "❌"
            print(f"   {status_icon} {task.task_id}: "
                  f"dernière exécution={task.last_executed or 'jamais'}, "
                  f"statut={task.last_status or 'N/A'}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


async def check_scheduler_instance():
    """Vérifier l'instance du scheduler."""
    print_section("2️⃣  INSTANCE DU SCHEDULER")
    
    try:
        settings = get_settings()
        config = {**settings.secrets, **settings.app_config}
        scheduler = SchedulerService(config)
        
        print(f"📅 Scheduler créé:")
        print(f"   - Instance: {scheduler}")
        print(f"   - En cours d'exécution: {scheduler.is_running}")
        print(f"   - Type: {type(scheduler.scheduler)}")
        
        if not scheduler.is_running:
            print("\n⚠️  LE SCHEDULER N'EST PAS EN COURS D'EXÉCUTION")
            print("   Tentative de démarrage...")
            try:
                await scheduler.start()
                print(f"   ✅ Scheduler démarré: {scheduler.is_running}")
            except Exception as e:
                print(f"   ❌ Erreur lors du démarrage: {e}")
                return None
        
        print()
        
        # Lister les jobs
        jobs = scheduler.scheduler.get_jobs()
        print(f"🔢 Nombre de jobs planifiés: {len(jobs)}")
        
        for job in jobs:
            print(f"\n   📋 Job: {job.id}")
            print(f"      - Nom: {job.name}")
            print(f"      - Trigger: {job.trigger}")
            print(f"      - Next run: {job.next_run_time}")
            print(f"      - Fonction: {job.func}")
            
            if job.id == 'generate_haiku_scheduled':
                print(f"\n   🎋 TÂCHE HAIKU TROUVÉE!")
                print(f"      - Trigger details: {job.trigger}")
                if hasattr(job.trigger, 'fields'):
                    for field in job.trigger.fields:
                        print(f"         {field.name}: {field}")
        
        print()
        
        # Obtenir le statut complet
        status = scheduler.get_status()
        print(f"📊 Statut du scheduler:")
        print(f"   - Running: {status.get('running')}")
        print(f"   - Job count: {status.get('job_count')}")
        print(f"   - Jobs: {len(status.get('jobs', []))}")
        
        for job_info in status.get('jobs', []):
            if job_info['id'] == 'generate_haiku_scheduled':
                print(f"\n   🎋 Tâche Haiku depuis get_status():")
                print(f"      - ID: {job_info['id']}")
                print(f"      - Nom: {job_info['name']}")
                print(f"      - Next run: {job_info.get('next_run')}")
                print(f"      - Last execution: {job_info.get('last_execution')}")
                print(f"      - Last status: {job_info.get('last_status')}")
        
        return scheduler
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_haiku_execution(scheduler):
    """Tester l'exécution manuelle de la tâche."""
    print_section("3️⃣  TEST D'EXÉCUTION MANUELLE")
    
    if not scheduler:
        print("⚠️  Scheduler non disponible, impossible de tester")
        return
    
    print("🧪 Tentative d'exécution manuelle de _generate_random_haikus()...")
    print("   (Cela peut prendre quelques secondes)\n")
    
    try:
        await scheduler._generate_random_haikus()
        print("\n✅ Exécution terminée avec succès!")
        
        # Vérifier que l'exécution a été enregistrée
        db = SessionLocal()
        try:
            haiku_task = db.query(ScheduledTaskExecution).filter_by(
                task_id='generate_haiku_scheduled'
            ).first()
            
            if haiku_task:
                print(f"\n📝 Mise à jour en base:")
                print(f"   - Dernière exécution: {haiku_task.last_executed}")
                print(f"   - Statut: {haiku_task.last_status}")
                print(f"   - Nombre d'exécutions: {haiku_task.execution_count}")
            else:
                print("\n⚠️  Pas d'enregistrement en base après l'exécution")
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()


async def check_trigger_configuration():
    """Vérifier la configuration du trigger."""
    print_section("4️⃣  ANALYSE DU TRIGGER CRON")
    
    from apscheduler.triggers.cron import CronTrigger
    
    # Créer le même trigger que le code
    trigger = CronTrigger(hour=6, minute=0)
    
    print(f"📅 Configuration du CronTrigger:")
    print(f"   - Trigger: {trigger}")
    print(f"   - Timezone: {trigger.timezone}")
    
    # Calculer les 5 prochaines exécutions
    now = datetime.now(trigger.timezone)
    print(f"\n🕐 Heure actuelle: {now}")
    print(f"\n📆 Prochaines exécutions prévues:")
    
    next_fire = trigger.get_next_fire_time(None, now)
    for i in range(5):
        if next_fire:
            print(f"   {i+1}. {next_fire}")
            next_fire = trigger.get_next_fire_time(next_fire, next_fire)
        else:
            break


async def main():
    """Point d'entrée principal."""
    print("\n" + "🔍" * 40)
    print("   DIAGNOSTIC - Génération de Haïkus Scheduler")
    print("🔍" * 40)
    
    # 1. Vérifier l'état de la base de données
    check_database_state()
    
    # 2. Vérifier l'instance du scheduler
    scheduler = await check_scheduler_instance()
    
    # 3. Analyser le trigger
    await check_trigger_configuration()
    
    # 4. Tester l'exécution (optionnel)
    print_section("5️⃣  OPTIONS DE TEST")
    print("Voulez-vous tester l'exécution manuelle de la tâche?")
    print("⚠️  Cela va générer un fichier de haïkus dans le dossier de sortie.")
    response = input("\nTaper 'oui' pour continuer, ou Entrée pour passer: ").strip().lower()
    
    if response in ['oui', 'o', 'yes', 'y']:
        await test_haiku_execution(scheduler)
    else:
        print("Test manuel ignoré.")
    
    # Arrêter le scheduler si on l'a démarré
    if scheduler and scheduler.is_running:
        await scheduler.stop()
        print("\n✅ Scheduler arrêté")
    
    print("\n" + "=" * 80)
    print("  FIN DU DIAGNOSTIC")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
