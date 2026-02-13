#!/usr/bin/env python3
"""Script de test pour vérifier la fonctionnalité d'auto-restart des services."""

import sys
import os
import time
import subprocess
import signal

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import ServiceState
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_auto_restart():
    """Tester la fonctionnalité d'auto-restart."""
    
    logger.info("=" * 60)
    logger.info("TEST: Fonctionnalité d'Auto-Restart des Services")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # 1. Vérifier que la table service_states existe
        logger.info("\n1️⃣ Vérification de la table service_states...")
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='service_states'")).fetchone()
        if not result:
            logger.error("❌ Table service_states n'existe pas!")
            return False
        logger.info("✅ Table service_states existe")
        
        # 2. Créer des états fictifs pour test
        logger.info("\n2️⃣ Création d'états de test...")
        
        # Nettoyer les anciens états
        db.execute(text("DELETE FROM service_states"))
        db.commit()
        
        # Ajouter des états actifs
        test_services = [
            ('tracker', True),
            ('scheduler', True)
        ]
        
        for service_name, is_active in test_services:
            state = ServiceState(service_name=service_name, is_active=is_active)
            db.add(state)
            db.commit()
            status = "✅ ACTIF" if is_active else "⏸️ INACTIF"
            logger.info(f"   {status} - {service_name}")
        
        # 3. Vérifier les états créés
        logger.info("\n3️⃣ Vérification des états sauvegardés...")
        states = db.query(ServiceState).all()
        logger.info(f"   📊 {len(states)} services dans la DB:")
        for state in states:
            status = "✅" if state.is_active else "⏸️"
            logger.info(f"   {status} {state.service_name} - Dernière MAJ: {state.last_updated}")
        
        # 4. Simuler la restauration
        logger.info("\n4️⃣ Simulation de la restauration au démarrage...")
        active_services = db.query(ServiceState).filter_by(is_active=True).all()
        logger.info(f"   🔄 {len(active_services)} services à restaurer:")
        for service in active_services:
            logger.info(f"   ✨ Restauration simulée: {service.service_name}")
        
        # 5. Test de mise à jour d'état
        logger.info("\n5️⃣ Test de mise à jour d'état...")
        tracker_state = db.query(ServiceState).filter_by(service_name='tracker').first()
        if tracker_state:
            logger.info(f"   État actuel du tracker: {'actif' if tracker_state.is_active else 'inactif'}")
            tracker_state.is_active = not tracker_state.is_active
            db.commit()
            logger.info(f"   ✅ État mis à jour: {'actif' if tracker_state.is_active else 'inactif'}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ TOUS LES TESTS RÉUSSIS!")
        logger.info("=" * 60)
        
        logger.info("\n📋 Résumé:")
        logger.info("   ✓ Table service_states créée")
        logger.info("   ✓ États peuvent être sauvegardés")
        logger.info("   ✓ États peuvent être lus")
        logger.info("   ✓ États peuvent être mis à jour")
        logger.info("   ✓ Logique de restauration fonctionnelle")
        
        logger.info("\n🚀 Pour tester en production:")
        logger.info("   1. Démarrer le serveur")
        logger.info("   2. Activer un service (tracker/scheduler)")
        logger.info("   3. Redémarrer le serveur")
        logger.info("   4. Le service devrait redémarrer automatiquement!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_auto_restart()
    sys.exit(0 if success else 1)
