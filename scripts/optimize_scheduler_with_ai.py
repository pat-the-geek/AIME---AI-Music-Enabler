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
        """Créer le prompt pour l'IA."""
        prompt = f"""Tu es un expert en optimisation de systèmes de musique et d'IA. 
Analyse ces données de base de données musicale et recommande les paramètres OPTIMAUX du scheduler d'enrichissement.

📊 DONNÉES ACTUELLES DE LA BASE DE DONNÉES:
- Albums: {analysis['total_albums']} ({analysis['albums_without_images']} sans images, {analysis['image_coverage_pct']}% couverts)
- Artistes: {analysis['total_artists']}
- Morceaux: {analysis['total_tracks']} (durée moyenne: {analysis['avg_track_duration_sec']}s)
- Écoutes totales: {analysis['total_scrobbles']}
- Écoutes (7 derniers jours): {analysis['recent_scrobbles_7days']} (~{analysis['daily_avg_scrobbles']}/jour)
- Dernière import: {analysis['last_import_date']}
- Heures de pointe d'écoute: {analysis['peak_listening_hours']}
- Artistes nécessitant descriptions: ~{analysis['artists_count']}

🎯 OBJECTIFS DU SCHEDULER D'ENRICHISSEMENT:
1. Enrichir les images des albums (priority=MusicBrainz→Discogs→Spotify)
2. Générer les descriptions automatiques pour les albums
3. Détecter les genres musicaux
4. Corriger le formatage des artistes collaboratifs

⏰ TÂCHES À OPTIMISER:
- Heure d'exécution quotidienne (actuellement 02:00)
- Fréquence d'enrichissement (batch size, interval)
- Rate limits par API (MusicBrainz: 60/min, Discogs: 120/min, Spotify: 60/min)
- Batch size pour les enrichissements par lot
- Timeout et retry strategy

💡 CONSIDÉRATIONS:
- L'IA doit recommander l'HEURE OPTIMALE basée sur les patterns d'écoute
- Proposer un batch_size optimal basé sur le volume de données
- Recommander les rate limits adaptés à la charge
- Suggérer les timeouts appropriés

📋 RÉPONDS AVEC CE FORMAT JSON EXACT (et RIEN d'autre):
{{
  "optimal_execution_time": "HH:MM (explication courte)",
  "optimal_batch_size": "nombre (pourquoi)",
  "recommended_rate_limits": {{
    "musicbrainz_per_minute": "nombre",
    "discogs_per_minute": "nombre", 
    "spotify_per_minute": "nombre"
  }},
  "timeout_seconds": "nombre",
  "enrichment_priority": ["source1", "source2", "source3"],
  "weekly_schedule": "recommandation pour exécutions additionnelles",
  "optimization_notes": "observations et justifications (2-3 phrases)"
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
        """Appliquer les recommandations à la configuration."""
        if not recommendations:
            print("❌ Aucune recommandation à appliquer")
            return False
        
        try:
            config_dir = Path(__file__).parent.parent / "config"
            enrichment_config_file = config_dir / "enrichment_config.json"
            app_config_file = config_dir / "app.json"
            
            # Charger l'enrichment_config.json
            with open(enrichment_config_file, 'r') as f:
                enrichment_config = json.load(f)
            
            # Charger l'app.json
            with open(app_config_file, 'r') as f:
                app_config = json.load(f)
            
            # Mettre à jour les paramètres d'enrichissement
            if "optimal_batch_size" in recommendations:
                batch_size = int(recommendations["optimal_batch_size"].split()[0])
                enrichment_config["auto_enrichment"]["batch_size"] = batch_size
                print(f"✓ Batch size: {batch_size}")
            
            if "timeout_seconds" in recommendations:
                timeout = int(recommendations["timeout_seconds"].split()[0])
                enrichment_config["auto_enrichment"]["timeout_seconds"] = timeout
                print(f"✓ Timeout: {timeout}s")
            
            if "recommended_rate_limits" in recommendations:
                limits = recommendations["recommended_rate_limits"]
                enrichment_config["auto_enrichment"]["rate_limits"] = {
                    "musicbrainz_per_minute": int(limits.get("musicbrainz_per_minute", 60)),
                    "discogs_per_minute": int(limits.get("discogs_per_minute", 120)),
                    "spotify_per_minute": int(limits.get("spotify_per_minute", 60))
                }
                print(f"✓ Rate limits mis à jour")
            
            # Mettre à jour l'heure d'exécution dans app.json
            if "optimal_execution_time" in recommendations:
                exec_time = recommendations["optimal_execution_time"].split()[0]  # Extraire "HH:MM"
                if ":" in exec_time and len(exec_time) == 5:
                    # Mettre à jour le scheduler
                    app_config["scheduler"]["enrichment_scheduler"]["schedule"] = f"daily_{exec_time}"
                    
                    # Mettre à jour aussi dans la task
                    for task in app_config["scheduler"]["tasks"]:
                        if task["name"] == "daily_enrichment":
                            task["time"] = exec_time
                    
                    print(f"✓ Heure d'exécution: {exec_time}")
            
            # Sauvegarder les configurations
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
            return False
    
    def generate_report(self, analysis: dict, recommendations: dict) -> str:
        """Générer un rapport d'optimisation."""
        report = f"""
╔════════════════════════════════════════════════════════════════════════╗
║          RAPPORT D'OPTIMISATION SCHEDULER PAR L'IA - Euria            ║
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

🎯 RECOMMANDATIONS DE L'IA
─────────────────────────────────────────────────────────────────────────
• Heure d'exécution: {recommendations.get('optimal_execution_time', 'N/A')}
• Batch size: {recommendations.get('optimal_batch_size', 'N/A')}
• Timeout: {recommendations.get('timeout_seconds', 'N/A')}
• Rate limits:
  └─ MusicBrainz: {recommendations.get('recommended_rate_limits', {}).get('musicbrainz_per_minute', 'N/A')}/min
  └─ Discogs: {recommendations.get('recommended_rate_limits', {}).get('discogs_per_minute', 'N/A')}/min
  └─ Spotify: {recommendations.get('recommended_rate_limits', {}).get('spotify_per_minute', 'N/A')}/min
• Priority: {recommendations.get('enrichment_priority', 'N/A')}
• Exécutions additionnelles: {recommendations.get('weekly_schedule', 'N/A')}

💡 NOTES D'OPTIMISATION
─────────────────────────────────────────────────────────────────────────
{recommendations.get('optimization_notes', 'N/A')}

✅ STATUT: Les configurations ont été mises à jour automatiquement.
   Prochain enrichissement: {recommendations.get('optimal_execution_time', '02:00')}
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
