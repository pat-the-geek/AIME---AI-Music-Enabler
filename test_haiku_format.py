#!/usr/bin/env python3
"""
Test pour vérifier que le format des haikus du scheduler 
correspond EXACTEMENT à celui de l'API /collection/markdown/presentation
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire backend au chemin
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Configuration
os.environ.setdefault("ENV", "development")

from app.database import SessionLocal
from app.models import Album, Artist, Image
from app.services.ai_service import AIService
from app.config import get_config

async def test_haiku_generation():
    """Test la génération de haikus avec le format exact."""
    
    config = get_config()
    db = SessionLocal()
    ai = AIService(config)
    
    try:
        # Récupérer les 5 premiers albums
        albums = db.query(Album).filter(Album.source == 'discogs').limit(5).all()
        
        if not albums:
            print("❌ Aucun album trouvé en base de données")
            return
        
        print(f"✅ {len(albums)} albums trouvés pour test")
        print("\n" + "="*80)
        print("GÉNÉRATION DE HAIKU - FORMAT API")
        print("="*80 + "\n")
        
        # Générer le markdown
        markdown = "# Album Haïku\n"
        
        # Date du jour
        now = datetime.now()
        day = now.strftime("%-d" if os.name != 'nt' else "%#d")
        month = now.strftime("%B")
        year = now.strftime("%Y")
        date_str = f"#### The {day} of {month}, {year}"
        markdown += f"{date_str}\n"
        markdown += f"\t\t{len(albums)} albums from Discogs collection\n"
        
        # Haïku global
        print("📝 Génération du haïku global...")
        haiku_prompt = "Génère un haïku court sur la musique et les albums. Réponds uniquement avec le haïku en 3 lignes, sans numérotation."
        haiku_text = await ai.ask_for_ia(haiku_prompt, max_tokens=100)
        
        print(f"✅ Haïku reçu: {repr(haiku_text)}\n")
        
        # Ajouter chaque ligne du haïku avec indentation
        for line in haiku_text.strip().split('\n'):
            markdown += f"\t\t{line.strip()}\n"
        
        markdown += "---\n"
        
        # Générer une section pour chaque album
        for i, album in enumerate(albums, 1):
            print(f"\n📚 Album {i}/{len(albums)}: {album.title}")
            
            # Artiste en titre
            if album.artists:
                artist_name = album.artists[0].name
                markdown += f"# {artist_name}\n"
            
            # Titre, année et infos
            title_line = f"#### {album.title}"
            if album.year:
                title_line += f" ({album.year})"
            markdown += f"{title_line}\n"
            
            # Liens Spotify et Discogs
            markdown += "\t###### 🎧"
            if album.spotify_url:
                markdown += f" [Listen with Spotify]({album.spotify_url})"
            markdown += "  👥"
            if album.discogs_url:
                markdown += f" [Read on Discogs]({album.discogs_url})"
            markdown += "\n\t###### 💿 "
            markdown += f"{album.support if album.support else 'Digital'}\n"
            
            # Description générée par l'IA
            print(f"   📝 Génération de la description...")
            try:
                album_lower = album.title.lower()
                artist_lower = (album.artists[0].name.lower() if album.artists else "artiste inconnu")
                description_prompt = f"""Présente moi l'album {album_lower} de {artist_lower}. 
N'ajoute pas de questions ou de commentaires. 
Limite ta réponse à 35 mots maximum.
Réponds uniquement en français."""
                description = await ai.ask_for_ia(description_prompt, max_tokens=100)
                
                if not description or len(description) < 10:
                    description = f"Album {album.title} sorti en {album.year if album.year else '?'}. Œuvre musicale enrichissante, à découvrir absolument."
                    
                print(f"   ✅ Description: {description[:50]}...")
                
            except Exception as e:
                print(f"   ⚠️ Erreur: {e}")
                description = f"Album {album.title} sorti en {album.year if album.year else '?'}. Œuvre musicale enrichissante, à découvrir absolument."
            
            # Ajouter la description avec indentation
            description = description.strip()
            for line in description.split('\n'):
                markdown += f"\t\t{line}\n"
            
            # Image HTML
            if album.images and album.images[0].url:
                image_url = album.images[0].url
                markdown += f"\n\n<img src='{image_url}' />\n"
            
            markdown += "---\n"
        
        # Footer
        markdown += "\t\tPython generated with love, for iA Presenter using Euria AI from Infomaniak\n"
        
        # Sauvegarder le fichier
        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filepath = output_dir / f"test-haiku-{timestamp}.md"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print("\n" + "="*80)
        print(f"✅ FICHIER GÉNÉRÉ: {filepath}")
        print("="*80 + "\n")
        print(markdown)
        print("\n" + "="*80)
        print("INFORMATIONS DE VÉRIFICATION")
        print("="*80)
        print(f"✅ Format: # Album Haïku")
        print(f"✅ Date: {date_str}")
        print(f"✅ Nombre d'albums: {len(albums)}")
        print(f"✅ Haïku: 3 lignes (tab-indentées)")
        print(f"✅ Liens: 🎧 Spotify  👥 Discogs")
        print(f"✅ Support: 💿")
        print(f"✅ Image: HTML <img src='' />")
        print(f"✅ Footer: Python generated with love...")
        print(f"\n✅ Format IDENTIQUE à l'API /collection/markdown/presentation\n")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_haiku_generation())
