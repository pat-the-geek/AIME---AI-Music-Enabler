"""
Service de gestion des éditions pré-générées de magazines.
Permet la génération, le stockage et la récupération d'éditions de magazines.
"""

import json
import os
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import random
from sqlalchemy.orm import Session

from app.services.magazine_generator_service import MagazineGeneratorService
from app.services.ai_service import AIService
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MagazineEditionService:
    """Service pour gérer les éditions pré-générées de magazines."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialiser l'AI Service pour le MagazineGeneratorService
        settings = get_settings()
        secrets = settings.secrets
        euria_config = secrets.get('euria', {})
        
        self.ai_service = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer')
        )
        
        self.magazine_service = MagazineGeneratorService(db, self.ai_service)
        self.base_path = Path(__file__).parent.parent.parent.parent / "data" / "magazine-editions"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def _get_edition_path(self, edition_id: str) -> Path:
        """Obtient le chemin complet d'une édition."""
        date_str = edition_id.split('-')[0:3]  # ['2026', '02', '03']
        date_folder = '-'.join(date_str)  # '2026-02-03'
        folder = self.base_path / date_folder
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{edition_id}.json"
    
    def _generate_edition_id(self, edition_number: int) -> str:
        """Génère un ID d'édition unique."""
        now = datetime.now(timezone.utc)
        return f"{now.strftime('%Y-%m-%d')}-{edition_number:03d}"
    
    async def generate_edition(self, edition_number: int = 1) -> Dict[str, Any]:
        """
        Génère une nouvelle édition de magazine.
        
        Args:
            edition_number: Numéro de l'édition du jour (1-10)
            
        Returns:
            Dict contenant l'édition complète
        """
        try:
            edition_id = self._generate_edition_id(edition_number)
            logger.info(f"📰 Génération de l'édition {edition_id}...")
            
            # Génération du magazine
            magazine_data = await self.magazine_service.generate_magazine()
            
            # Enrichissement complet (attendre que les descriptions soient enrichies)
            if magazine_data.get('enrichment_started'):
                logger.info(f"⏳ Attente de l'enrichissement pour l'édition {edition_id}...")
                # Attendre 3 minutes max pour les enrichissements (2-3 albums × 5-15s chacun)
                await asyncio.sleep(180)
                
                # IMPORTANT: Regénérer le magazine pour récupérer les descriptions enrichies depuis la DB
                logger.info(f"🔄 Rechargement du magazine avec descriptions enrichies...")
                magazine_data = await self.magazine_service.generate_magazine()
            
            # Construction de l'édition
            edition = {
                'id': edition_id,
                'edition_number': edition_number,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'albums': magazine_data.get('albums', []),
                'pages': magazine_data.get('pages', []),
                'ai_layouts': magazine_data.get('ai_layouts', {}),
                'enrichment_completed': True,
                'version': '1.0'
            }
            
            # Sauvegarde
            self._save_edition(edition)
            
            logger.info(f"✅ Édition {edition_id} générée et sauvegardée ({len(edition['albums'])} albums)")
            return edition
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération de l'édition: {e}")
            raise
    
    def _save_edition(self, edition: Dict[str, Any]) -> None:
        """Sauvegarde une édition en JSON."""
        try:
            path = self._get_edition_path(edition['id'])
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(edition, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Édition sauvegardée: {path}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde de l'édition: {e}")
            raise
    
    def load_edition(self, edition_id: str) -> Optional[Dict[str, Any]]:
        """
        Charge une édition depuis le stockage.
        
        Args:
            edition_id: ID de l'édition à charger
            
        Returns:
            Dict contenant l'édition ou None si non trouvée
        """
        try:
            path = self._get_edition_path(edition_id)
            if not path.exists():
                logger.warning(f"⚠️ Édition non trouvée: {edition_id}")
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                edition = json.load(f)
            
            logger.info(f"📖 Édition chargée: {edition_id}")
            return edition
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de l'édition {edition_id}: {e}")
            return None
    
    def list_editions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Liste toutes les éditions disponibles.
        
        Args:
            limit: Nombre maximum d'éditions à retourner
            
        Returns:
            Liste des métadonnées des éditions (triées par date décroissante)
        """
        try:
            editions = []
            
            # Parcourir tous les dossiers de dates
            for date_folder in sorted(self.base_path.iterdir(), reverse=True):
                if not date_folder.is_dir():
                    continue
                
                # Parcourir tous les fichiers JSON dans le dossier
                for edition_file in sorted(date_folder.glob("*.json"), reverse=True):
                    try:
                        with open(edition_file, 'r', encoding='utf-8') as f:
                            edition = json.load(f)
                        
                        # Extraire les métadonnées
                        editions.append({
                            'id': edition['id'],
                            'edition_number': edition.get('edition_number', 1),
                            'generated_at': edition['generated_at'],
                            'album_count': len(edition.get('albums', [])),
                            'page_count': len(edition.get('pages', [])),
                            'enrichment_completed': edition.get('enrichment_completed', False)
                        })
                        
                        if len(editions) >= limit:
                            break
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur lors de la lecture de {edition_file}: {e}")
                        continue
                
                if len(editions) >= limit:
                    break
            
            logger.info(f"📚 {len(editions)} éditions listées")
            return editions
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du listage des éditions: {e}")
            return []
    
    def get_random_edition(self) -> Optional[Dict[str, Any]]:
        """
        Récupère une édition aléatoire parmi les disponibles.
        
        Returns:
            Dict contenant l'édition ou None si aucune disponible
        """
        try:
            editions = self.list_editions()
            if not editions:
                logger.warning("⚠️ Aucune édition disponible")
                return None
            
            # Sélection aléatoire
            random_edition_meta = random.choice(editions)
            edition = self.load_edition(random_edition_meta['id'])
            
            logger.info(f"🎲 Édition aléatoire sélectionnée: {random_edition_meta['id']}")
            return edition
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sélection aléatoire: {e}")
            return None
    
    async def generate_daily_batch(self, count: int = 10, delay_minutes: int = 30) -> List[str]:
        """
        Génère un lot d'éditions quotidiennes.
        
        Args:
            count: Nombre d'éditions à générer
            delay_minutes: Délai entre chaque génération (en minutes)
            
        Returns:
            Liste des IDs des éditions générées
        """
        generated_ids = []
        
        try:
            logger.info(f"🚀 Début de la génération de {count} éditions (intervalle: {delay_minutes}min)")
            
            for i in range(1, count + 1):
                try:
                    edition = await self.generate_edition(edition_number=i)
                    generated_ids.append(edition['id'])
                    
                    # Délai entre les générations (sauf pour la dernière)
                    if i < count:
                        logger.info(f"⏸️ Pause de {delay_minutes} minutes avant la prochaine génération...")
                        await asyncio.sleep(delay_minutes * 60)
                    
                except Exception as e:
                    logger.error(f"❌ Erreur lors de la génération de l'édition #{i}: {e}")
                    continue
            
            logger.info(f"✅ Génération de lot terminée: {len(generated_ids)}/{count} éditions créées")
            return generated_ids
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération du lot: {e}")
            return generated_ids
    
    def cleanup_old_editions(self, keep_days: int = 30) -> int:
        """
        Supprime les éditions plus anciennes que keep_days jours.
        
        Args:
            keep_days: Nombre de jours d'éditions à conserver
            
        Returns:
            Nombre d'éditions supprimées
        """
        try:
            deleted_count = 0
            cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - keep_days)
            
            for date_folder in self.base_path.iterdir():
                if not date_folder.is_dir():
                    continue
                
                # Parser la date du dossier
                try:
                    folder_date = datetime.strptime(date_folder.name, '%Y-%m-%d')
                    folder_date = folder_date.replace(tzinfo=timezone.utc)
                    
                    if folder_date < cutoff_date:
                        # Supprimer tous les fichiers du dossier
                        for edition_file in date_folder.glob("*.json"):
                            edition_file.unlink()
                            deleted_count += 1
                        
                        # Supprimer le dossier vide
                        date_folder.rmdir()
                        logger.info(f"🗑️ Dossier supprimé: {date_folder.name}")
                        
                except ValueError:
                    logger.warning(f"⚠️ Format de dossier invalide: {date_folder.name}")
                    continue
            
            logger.info(f"🧹 Nettoyage terminé: {deleted_count} éditions supprimées")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du nettoyage: {e}")
            return 0
    
    def cleanup_excess_editions(self, max_editions: int = 100) -> int:
        """
        Supprime les éditions les plus anciennes si le nombre total dépasse max_editions.
        
        Args:
            max_editions: Nombre maximum d'éditions à conserver (défaut: 100)
            
        Returns:
            Nombre d'éditions supprimées
        """
        try:
            deleted_count = 0
            
            # Récupérer toutes les éditions avec leur date
            all_editions = []
            for date_folder in self.base_path.iterdir():
                if not date_folder.is_dir():
                    continue
                
                for edition_file in date_folder.glob("*.json"):
                    try:
                        with open(edition_file, 'r', encoding='utf-8') as f:
                            edition = json.load(f)
                        
                        all_editions.append({
                            'file_path': edition_file,
                            'generated_at': datetime.fromisoformat(edition['generated_at'].replace('Z', '+00:00'))
                        })
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur lecture {edition_file}: {e}")
                        continue
            
            # Si on dépasse la limite, supprimer les plus anciennes
            if len(all_editions) > max_editions:
                # Trier par date (plus anciennes en premier)
                all_editions.sort(key=lambda x: x['generated_at'])
                
                # Supprimer les éditions en excès
                editions_to_delete = all_editions[:len(all_editions) - max_editions]
                
                for edition in editions_to_delete:
                    try:
                        edition['file_path'].unlink()
                        deleted_count += 1
                        logger.info(f"🗑️ Édition supprimée: {edition['file_path'].name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur suppression {edition['file_path']}: {e}")
                
                # Nettoyer les dossiers vides
                for date_folder in self.base_path.iterdir():
                    if date_folder.is_dir() and not list(date_folder.glob("*.json")):
                        date_folder.rmdir()
                        logger.info(f"🗑️ Dossier vide supprimé: {date_folder.name}")
                
                logger.info(f"🧹 Nettoyage excédent terminé: {deleted_count} éditions supprimées (limite: {max_editions})")
            else:
                logger.info(f"✅ Nombre d'éditions OK: {len(all_editions)}/{max_editions}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du nettoyage excédent: {e}")
            return 0
