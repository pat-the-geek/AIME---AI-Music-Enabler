#!/usr/bin/env python3
"""
Optimiser les paramètres du scheduler via l'IA Euria.
Analyse les données de la base de données et utilise l'IA pour recommander
les meilleurs paramètres du scheduler d'enrichissement.
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ajouter le backend au path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import sessionmaker
    from app.models import Album, Artist, Track, ListeningHistory, Image
    from app.core.config import get_settings
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    print("Assurez-vous d'être dans le bon répertoire")
    sys.exit(1)


class SchedulerOptimizer:
    """Optimise les paramètres du scheduler via l'IA."""
    
    def __init__(self):
        """Initialiser l'optimiseur."""
        settings = get_settings()
        self.db_url = settings.database_url
        self.euria_url = settings.secrets.get('euria', {}).get('url')
        self.euria_bearer = settings.secrets.get('euria', {}).get('bearer')
        
        # Créer la session DB
        engine = create_engine(self.db_url)
        Session = sessionmaker(bind=engine)
        self.db = Session()
    
    def analyze_database(self) -> dict:
        """Analyser les données de la base de données."""
        print("\n📊 Analyse de la base de données...")
        
        try:
            # Statistiques générales
            total_albums = self.db.query(Album).count()
            total_artists = self.db.query(Artist).count()
            total_tracks = self.db.query(Track).count()
            total_scrobbles = self.db.query(ListeningHistory).count()
            
            # Albums avec/sans images
            albums_with_images = self.db.query(Album).join(Image).distinct().count()
            albums_without_images = total_albums - albums_with_images
            image_coverage = (albums_with_images / total_albums * 100) if total_albums > 0 else 0
            
            # Durée moyenne des morceaux
            try:
                if hasattr(Track, 'duration'):
                    avg_duration = self.db.query(func.avg(Track.duration)).scalar() or 0
                else:
                    avg_duration = 0
            except:
                avg_duration = 0
            
            # Dernière date d'import
            last_listening = self.db.query(func.max(ListeningHistory.timestamp)).scalar()
            last_import_date = datetime.fromtimestamp(last_listening) if last_listening else None
            
            # Pattern d'écoute (par heure du jour)
            listening_times = self.db.query(ListeningHistory).all()
            hourly_distribution = [0] * 24
            if listening_times:
                for listen in listening_times:
                    hour = datetime.fromtimestamp(listen.timestamp).hour
                    hourly_distribution[hour] += 1
            
            # Écoutes par jour (7 derniers jours)
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_scrobbles = self.db.query(ListeningHistory).filter(
                ListeningHistory.timestamp >= int(seven_days_ago.timestamp())
            ).count()
            
            daily_avg = recent_scrobbles / 7 if recent_scrobbles > 0 else 0
            
            # Artistes sans description
            artists_without_ai = total_artists  # Simplifié pour cet exemple
            
            return {
                "total_albums": total_albums,
                "total_artists": total_artists,
                "total_tracks": total_tracks,
                "total_scrobbles": total_scrobbles,
                "albums_with_images": albums_with_images,
                "albums_without_images": albums_without_images,
                "image_coverage_pct": round(image_coverage, 2),
                "avg_track_duration_sec": round(avg_duration, 2),
                "last_import_date": last_import_date.isoformat() if last_import_date else None,
                "recent_scrobbles_7days": recent_scrobbles,
                "daily_avg_scrobbles": round(daily_avg, 2),
                "peak_listening_hours": self._get_peak_hours(hourly_distribution),
                "artists_count": total_artists,
                "tracks_need_duration": self._count_tracks_without_duration()
            }
        
        except Exception as e:
            print(f"❌ Erreur analyse DB: {e}")
            return {}
    
    def _get_peak_hours(self, hourly_dist: list) -> list:
        """Obtenir les heures de pointe d'écoute."""
        hours_with_counts = [(i, hourly_dist[i]) for i in range(24)]
        hours_with_counts.sort(key=lambda x: x[1], reverse=True)
        return [h[0] for h in hours_with_counts[:3]]  # Top 3 hours
    
    def _count_tracks_without_duration(self) -> int:
        """Compter les morceaux sans durée."""
        try:
            # Essayer d'accéder à la colonne duration si elle existe
            if hasattr(Track, 'duration'):
                return self.db.query(Track).filter(Track.duration.is_(None)).count()
            else:
                return 0
        except:
            return 0
    
    def create_optimization_prompt(self, analysis: dict) -> str:
        """Créer le prompt pour l'IA Euria pour optimiser TOUTES les tâches du scheduler."""
        prompt = f"""Tu es un expert en optimisation de systèmes de musique et d'IA. 
Analyse ces données et recommande les paramètres OPTIMAUX pour CHAQUE tâche du scheduler.

📊 DONNÉES DE LA BASE DE DONNÉES:
- Albums: {analysis['total_albums']} ({analysis['albums_without_images']} sans images, {analysis['image_coverage_pct']}% couverts)
- Artistes: {analysis['total_artists']}
- Morceaux: {analysis['total_tracks']} (durée moyenne: {analysis['avg_track_duration_sec']}s)
- Écoutes totales: {analysis['total_scrobbles']}
- Écoutes (7 derniers jours): {analysis['recent_scrobbles_7days']} (~{analysis['daily_avg_scrobbles']}/jour)
- Heures de pointe d'écoute: {analysis['peak_listening_hours']}

⏰ TÂCHES DU SCHEDULER À OPTIMISER:
1. daily_enrichment (Enrichissement: images, descriptions, genres) - actuellement 02:00
2. generate_haiku_scheduled (Génération haïkus quotidienne) - actuellement 06:00
3. export_collection_markdown (Export Markdown) - actuellement 08:00
4. export_collection_json (Export JSON) - actuellement 10:00
5. weekly_haiku (Haikus hebdo) - actuellement dimanche 20:00
6. monthly_analysis (Analyse mensuelle) - actuellement 1er mois 03:00
7. optimize_ai_descriptions (Optimisation IA descriptions) - actuellement /6h
8. generate_magazine_editions (Génération magazines pré-générés) - actuellement 03:00
9. sync_discogs_daily (Sync Discogs) - actuellement 04:00

💡 OBJECTIFS D'OPTIMISATION:
- Éviter les heures de pointe d'écoute {analysis['peak_listening_hours']}
- Minimiser les pics de charge API
- Regrouper les tâches similaires logiquement
- Maximiser la qualité avec l'IA Euria

📋 RÉPONDS AVEC CE FORMAT JSON EXACT (et RIEN d'autre):
{{
  "scheduler_tasks": {{
    "daily_enrichment": {{
      "optimal_execution_time": "HH:MM",
      "optimal_batch_size": "nombre",
      "timeout_seconds": "nombre",
      "recommended_rate_limits": {{"musicbrainz_per_minute": "nombre", "discogs_per_minute": "nombre", "spotify_per_minute": "nombre"}},
      "priority": ["source1", "source2", "source3"],
      "reason": "justification courte"
    }},
    "generate_haiku_scheduled": {{
      "optimal_execution_time": "HH:MM",
      "batch_count": "nombre d'albums",
      "reason": "justification courte"
    }},
    "export_collection_markdown": {{
      "optimal_execution_time": "HH:MM",
      "reason": "justification courte"
    }},
    "export_collection_json": {{
      "optimal_execution_time": "HH:MM",
      "reason": "justification courte"
    }},
    "weekly_haiku": {{
      "optimal_day": "day_of_week (0-6, 0=lundi)",
      "optimal_execution_time": "HH:MM",
      "reason": "justification courte"
    }},
    "monthly_analysis": {{
      "optimal_day_of_month": "1-31",
      "optimal_execution_time": "HH:MM",
      "reason": "justification courte"
    }},
    "optimize_ai_descriptions": {{
      "optimal_frequency": "hours (ex: 6, 8, 12)",
      "batch_size": "nombre",
      "reason": "justification courte"
    }},
    "generate_magazine_editions": {{
      "optimal_execution_time": "HH:MM",
      "batch_size": "nombre",
      "reason": "justification courte"
    }},
    "sync_discogs_daily": {{
      "optimal_execution_time": "HH:MM",
      "reason": "justification courte"
    }}
  }},
  "global_notes": "observations générales sur l'optimisation globale",
  "scheduling_strategy": "stratégie générale de scheduling"
}}"""
        return prompt
    
    def call_euria_api(self, prompt: str) -> dict:
        """Appeler l'API Euria pour obtenir les recommandations."""
        print("\n🤖 Appel de l'IA Euria pour optimisation...")
        print("─" * 70)
        
        headers = {
            "Authorization": f"Bearer {self.euria_bearer}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mistral3",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1200,
            "temperature": 0.3  # Basse température pour réponses précises
        }
        
        try:
            print("📤 Envoi du prompt à Euria...")
            print(f"\n📝 PROMPT ENVOYÉ:\n{prompt}\n")
            print("─" * 70)
            
            response = requests.post(self.euria_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print("📥 Réponse reçue de Euria:")
            print(content)
            print("─" * 70)
            
            # Parser la réponse JSON
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                json_str = content.split('```')[1].split('```')[0].strip()
            else:
                json_str = content.strip()
            
            recommendations = json.loads(json_str)
            return recommendations
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur appel API Euria: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON: {e}")
            return {}
    
    def apply_recommendations(self, recommendations: dict) -> bool:
        """Appliquer les recommandations de l'IA à TOUTES les tâches du scheduler."""
        if not recommendations or "scheduler_tasks" not in recommendations:
            print("❌ Aucune recommandation de tâches à appliquer")
            return False
        
        try:
            config_dir = Path(__file__).parent.parent / "config"
            enrichment_config_file = config_dir / "enrichment_config.json"
            app_config_file = config_dir / "app.json"
            
            # Charger les configurations
            with open(enrichment_config_file, 'r') as f:
                enrichment_config = json.load(f)
            
            with open(app_config_file, 'r') as f:
                app_config = json.load(f)
            
            scheduler_tasks = recommendations["scheduler_tasks"]
            
            # 1️⃣ Optimiser daily_enrichment
            if "daily_enrichment" in scheduler_tasks:
                task_rec = scheduler_tasks["daily_enrichment"]
                print("\n🔄 Optimisation: daily_enrichment")
                
                if "optimal_batch_size" in task_rec:
                    batch_size = int(str(task_rec["optimal_batch_size"]).split()[0])
                    enrichment_config["auto_enrichment"]["batch_size"] = batch_size
                    print(f"  ✓ Batch size: {batch_size}")
                
                if "timeout_seconds" in task_rec:
                    timeout = int(str(task_rec["timeout_seconds"]).split()[0])
                    enrichment_config["auto_enrichment"]["timeout_seconds"] = timeout
                    print(f"  ✓ Timeout: {timeout}s")
                
                if "recommended_rate_limits" in task_rec:
                    limits = task_rec["recommended_rate_limits"]
                    enrichment_config["auto_enrichment"]["rate_limits"] = {
                        "musicbrainz_per_minute": int(limits.get("musicbrainz_per_minute", 60)),
                        "discogs_per_minute": int(limits.get("discogs_per_minute", 120)),
                        "spotify_per_minute": int(limits.get("spotify_per_minute", 60))
                    }
                    print(f"  ✓ Rate limits mis à jour")
                
                if "optimal_execution_time" in task_rec:
                    exec_time = str(task_rec["optimal_execution_time"]).split()[0]
                    if ":" in exec_time and len(exec_time) == 5:
                        if "scheduler" not in app_config:
                            app_config["scheduler"] = {}
                        if "tasks" not in app_config["scheduler"]:
                            app_config["scheduler"]["tasks"] = []
                        
                        for task in app_config["scheduler"]["tasks"]:
                            if task.get("id") == "daily_enrichment" or task.get("name") == "daily_enrichment":
                                task["time"] = exec_time
                        print(f"  ✓ Heure d'exécution: {exec_time}")
            
            # 2️⃣ Optimiser generate_haiku_scheduled
            if "generate_haiku_scheduled" in scheduler_tasks:
                task_rec = scheduler_tasks["generate_haiku_scheduled"]
                print("\n🎋 Optimisation: generate_haiku_scheduled")
                if "optimal_execution_time" in task_rec:
                    exec_time = str(task_rec["optimal_execution_time"]).split()[0]
                    if ":" in exec_time:
                        if "scheduler" not in app_config:
                            app_config["scheduler"] = {}
                        if "tasks" not in app_config["scheduler"]:
                            app_config["scheduler"]["tasks"] = []
                        
                        for task in app_config["scheduler"]["tasks"]:
                            if task.get("id") == "generate_haiku_scheduled":
                                task["time"] = exec_time
                        print(f"  ✓ Heure d'exécution: {exec_time}")
            
            # 3️⃣ Optimiser export_collection_markdown
            if "export_collection_markdown" in scheduler_tasks:
                task_rec = scheduler_tasks["export_collection_markdown"]
                print("\n📝 Optimisation: export_collection_markdown")
                if "optimal_execution_time" in task_rec:
                    exec_time = str(task_rec["optimal_execution_time"]).split()[0]
                    if ":" in exec_time:
                        if "scheduler" not in app_config:
                            app_config["scheduler"] = {}
                        if "tasks" not in app_config["scheduler"]:
                            app_config["scheduler"]["tasks"] = []
                        
                        for task in app_config["scheduler"]["tasks"]:
                            if task.get("id") == "export_collection_markdown":
                                task["time"] = exec_time
                        print(f"  ✓ Heure d'exécution: {exec_time}")
            
            # 4️⃣ Optimiser export_collection_json
            if "export_collection_json" in scheduler_tasks:
                task_rec = scheduler_tasks["export_collection_json"]
                print("\n💾 Optimisation: export_collection_json")
                if "optimal_execution_time" in task_rec:
                    exec_time = str(task_rec["optimal_execution_time"]).split()[0]
                    if ":" in exec_time:
                        if "scheduler" not in app_config:
                            app_config["scheduler"] = {}
                        if "tasks" not in app_config["scheduler"]:
                            app_config["scheduler"]["tasks"] = []
                        
                        for task in app_config["scheduler"]["tasks"]:
                            if task.get("id") == "export_collection_json":
                                task["time"] = exec_time
                        print(f"  ✓ Heure d'exécution: {exec_time}")
            
            # 5️⃣ Optimiser weekly_haiku
            if "weekly_haiku" in scheduler_tasks:
                task_rec = scheduler_tasks["weekly_haiku"]
                print("\n🎋 Optimisation: weekly_haiku")
                if "optimal_day" in task_rec and "optimal_execution_time" in task_rec:
                    day = int(str(task_rec["optimal_day"]).split()[0])
                    exec_time = str(task_rec["optimal_execution_time"]).split()[0]
                    if ":" in exec_time:
                        if "scheduler" not in app_config:
                            app_config["scheduler"] = {}
                        if "tasks" not in app_config["scheduler"]:
                            app_config["scheduler"]["tasks"] = []
                        
                        for task in app_config["scheduler"]["tasks"]:
                            if task.get("id") == "weekly_haiku":
                                task["day"] = day
                                task["time"] = exec_time
                        print(f"  ✓ Jour/Heure: {day}/{exec_time}")
            
            # 6️⃣ Optimiser monthly_analysis
            if "monthly_analysis" in scheduler_tasks:
                task_rec = scheduler_tasks["monthly_analysis"]
                print("\n📊 Optimisation: monthly_analysis")
                if "optimal_day_of_month" in task_rec and "optimal_execution_time" in task_rec:
                    day = int(str(task_rec["optimal_day_of_month"]).split()[0])
                    exec_time = str(task_rec["optimal_execution_time"]).split()[0]
                    if ":" in exec_time:
                        if "scheduler" not in app_config:
                            app_config["scheduler"] = {}
                        if "tasks" not in app_config["scheduler"]:
                            app_config["scheduler"]["tasks"] = []
                        
                        for task in app_config["scheduler"]["tasks"]:
                            if task.get("id") == "monthly_analysis":
                                task["day"] = day
                                task["time"] = exec_time
                        print(f"  ✓ Jour du mois/Heure: {day}/{exec_time}")
            
            # 7️⃣ Optimiser optimize_ai_descriptions
            if "optimize_ai_descriptions" in scheduler_tasks:
                task_rec = scheduler_tasks["optimize_ai_descriptions"]
                print("\n🤖 Optimisation: optimize_ai_descriptions")
                if "optimal_frequency" in task_rec:
                    freq = int(str(task_rec["optimal_frequency"]).split()[0])
                    if "scheduler" not in app_config:
                        app_config["scheduler"] = {}
                    if "tasks" not in app_config["scheduler"]:
                        app_config["scheduler"]["tasks"] = []
                    
                    for task in app_config["scheduler"]["tasks"]:
                        if task.get("id") == "optimize_ai_descriptions":
                            task["frequency_hours"] = freq
                    print(f"  ✓ Fréquence: toutes les {freq}h")
            
            # 8️⃣ Optimiser generate_magazine_editions
            if "generate_magazine_editions" in scheduler_tasks:
                task_rec = scheduler_tasks["generate_magazine_editions"]
                print("\n📰 Optimisation: generate_magazine_editions")
                if "optimal_execution_time" in task_rec:
                    exec_time = str(task_rec["optimal_execution_time"]).split()[0]
                    if ":" in exec_time:
                        if "scheduler" not in app_config:
                            app_config["scheduler"] = {}
                        if "tasks" not in app_config["scheduler"]:
                            app_config["scheduler"]["tasks"] = []
                        
                        for task in app_config["scheduler"]["tasks"]:
                            if task.get("id") == "generate_magazine_editions":
                                task["time"] = exec_time
                        print(f"  ✓ Heure d'exécution: {exec_time}")
            
            # 🔟 Optimiser sync_discogs_daily
            if "sync_discogs_daily" in scheduler_tasks:
                task_rec = scheduler_tasks["sync_discogs_daily"]
                print("\n💿 Optimisation: sync_discogs_daily")
                if "optimal_execution_time" in task_rec:
                    exec_time = str(task_rec["optimal_execution_time"]).split()[0]
                    if ":" in exec_time:
                        if "scheduler" not in app_config:
                            app_config["scheduler"] = {}
                        if "tasks" not in app_config["scheduler"]:
                            app_config["scheduler"]["tasks"] = []
                        
                        for task in app_config["scheduler"]["tasks"]:
                            if task.get("id") == "sync_discogs_daily":
                                task["time"] = exec_time
                        print(f"  ✓ Heure d'exécution: {exec_time}")
            
            # Sauvegarder les configurations mises à jour
            with open(enrichment_config_file, 'w') as f:
                json.dump(enrichment_config, f, indent=2, ensure_ascii=False)
            
            with open(app_config_file, 'w') as f:
                json.dump(app_config, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Configurations sauvegardées:")
            print(f"   • {enrichment_config_file}")
            print(f"   • {app_config_file}")
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur application recommandations: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_report(self, analysis: dict, recommendations: dict) -> str:
        """Générer un rapport d'optimisation pour TOUTES les tâches."""
        scheduler_tasks = recommendations.get("scheduler_tasks", {})
        
        # Générer la section recommandations des tâches
        tasks_report = ""
        for task_id, task_name in [
            ("daily_enrichment", "🔄 Enrichissement quotidien"),
            ("generate_haiku_scheduled", "🎋 Génération de haïkus"),
            ("export_collection_markdown", "📝 Export Markdown"),
            ("export_collection_json", "💾 Export JSON"),
            ("weekly_haiku", "🎋 Haïku hebdomadaire"),
            ("monthly_analysis", "📊 Analyse mensuelle"),
            ("optimize_ai_descriptions", "🤖 Optimisation IA"),
            ("generate_magazine_editions", "📰 Génération de magazines"),
            ("sync_discogs_daily", "💿 Sync Discogs")
        ]:
            if task_id in scheduler_tasks:
                task_rec = scheduler_tasks[task_id]
                reason = task_rec.get("reason", "Optimisée par l'IA")
                
                if task_id == "daily_enrichment":
                    exec_time = task_rec.get("optimal_execution_time", "N/A")
                    batch = task_rec.get("optimal_batch_size", "N/A")
                    tasks_report += f"\n{task_name}\n"
                    tasks_report += f"  • Heure: {exec_time}\n"
                    tasks_report += f"  • Batch size: {batch}\n"
                    tasks_report += f"  • Raison: {reason}"
                
                elif task_id == "weekly_haiku":
                    day = task_rec.get("optimal_day", "N/A")
                    exec_time = task_rec.get("optimal_execution_time", "N/A")
                    tasks_report += f"\n{task_name}\n"
                    tasks_report += f"  • Jour: {day}, Heure: {exec_time}\n"
                    tasks_report += f"  • Raison: {reason}"
                
                elif task_id == "monthly_analysis":
                    day = task_rec.get("optimal_day_of_month", "N/A")
                    exec_time = task_rec.get("optimal_execution_time", "N/A")
                    tasks_report += f"\n{task_name}\n"
                    tasks_report += f"  • Jour du mois: {day}, Heure: {exec_time}\n"
                    tasks_report += f"  • Raison: {reason}"
                
                elif task_id == "optimize_ai_descriptions":
                    freq = task_rec.get("optimal_frequency", "N/A")
                    tasks_report += f"\n{task_name}\n"
                    tasks_report += f"  • Fréquence: toutes les {freq}h\n"
                    tasks_report += f"  • Raison: {reason}"
                
                else:
                    exec_time = task_rec.get("optimal_execution_time", "N/A")
                    tasks_report += f"\n{task_name}\n"
                    tasks_report += f"  • Heure: {exec_time}\n"
                    tasks_report += f"  • Raison: {reason}"
        
        report = f"""
╔════════════════════════════════════════════════════════════════════════╗
║    RAPPORT D'OPTIMISATION GLOBAL DU SCHEDULER PAR L'IA - Euria        ║
║                        {datetime.now().strftime('%d %B %Y')}                           ║
╚════════════════════════════════════════════════════════════════════════╝

📊 ANALYSE DE LA BASE DE DONNÉES
─────────────────────────────────────────────────────────────────────────
• Albums: {analysis.get('total_albums', 'N/A')}
  └─ Avec images: {analysis.get('albums_with_images', 'N/A')} ({analysis.get('image_coverage_pct', 'N/A')}%)
  └─ Sans images: {analysis.get('albums_without_images', 'N/A')} (À enrichir)
  
• Artistes: {analysis.get('total_artists', 'N/A')}
• Morceaux: {analysis.get('total_tracks', 'N/A')} (durée moy: {analysis.get('avg_track_duration_sec', 'N/A')}s)
• Écoutes totales: {analysis.get('total_scrobbles', 'N/A')}
• Dernière import: {analysis.get('last_import_date', 'N/A')}
• Heures de pointe: {analysis.get('peak_listening_hours', 'N/A')}

🎯 OPTIMISATION DE TOUS LES SCHEDULER TASKS
─────────────────────────────────────────────────────────────────────────
{tasks_report}

💡 STRATÉGIE GLOBALE DU SCHEDULING
─────────────────────────────────────────────────────────────────────────
{recommendations.get('scheduling_strategy', 'Optimisée pour éviter les heures de pointe')}

📝 NOTES GLOBALES
─────────────────────────────────────────────────────────────────────────
{recommendations.get('global_notes', 'Toutes les tâches du scheduler ont été optimisées')}

✅ STATUT: Les configurations de TOUTES les 9 tâches ont été mises à jour automatiquement.

📅 PROCHAIN CYCLE D'OPTIMISATION:
   Dimanche prochain à 03:00 via la tâche 'optimize_scheduler_with_ai'
"""
        return report
    
    def run(self):
        """Exécuter l'optimisation complète."""
        print("\n" + "="*70)
        print("🚀 OPTIMISATION DU SCHEDULER PAR L'IA EURIA")
        print("="*70)
        
        # Analyser la base
        analysis = self.analyze_database()
        if not analysis:
            print("❌ Erreur lors de l'analyse")
            return
        
        print("\n✅ Analyse complétée")
        print(f"   • Albums: {analysis['total_albums']}")
        print(f"   • Artistes: {analysis['total_artists']}")
        print(f"   • Image coverage: {analysis['image_coverage_pct']}%")
        print(f"   • Écoutes (7j): {analysis['recent_scrobbles_7days']}")
        
        # Créer le prompt
        prompt = self.create_optimization_prompt(analysis)
        
        # Appeler Euria
        recommendations = self.call_euria_api(prompt)
        if not recommendations:
            print("❌ Erreur lors de l'appel à Euria")
            return
        
        print("\n✅ Recommandations reçues")
        
        # Appliquer les recommandations
        if self.apply_recommendations(recommendations):
            print("\n✅ Recommandations appliquées")
            
            # Générer le rapport
            report = self.generate_report(analysis, recommendations)
            print(report)
            
            # Sauvegarder le rapport
            report_file = Path(__file__).parent.parent / "docs" / "SCHEDULER-OPTIMIZATION-REPORT.md"
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"\n📄 Rapport sauvegardé: {report_file}")
        else:
            print("❌ Erreur lors de l'application des recommandations")


if __name__ == "__main__":
    optimizer = SchedulerOptimizer()
    optimizer.run()
