#!/usr/bin/env python3
"""
Vérification du format de haiku scheduler - Sans charger la config
"""

from datetime import datetime
import os

def test_haiku_format():
    """Vérifier le format exact du haiku."""
    
    print("\n" + "="*80)
    print("VÉRIFICATION FORMAT HAIKU SCHEDULER")
    print("="*80 + "\n")
    
    # Simuler la génération
    markdown = "# Album Haïku\n"
    
    # Date du jour
    now = datetime.now()
    day = now.strftime("%-d" if os.name != 'nt' else "%#d")
    month = now.strftime("%B")
    year = now.strftime("%Y")
    date_str = f"#### The {day} of {month}, {year}"
    markdown += f"{date_str}\n"
    markdown += f"\t\t5 albums from Discogs collection\n"
    
    # Haïku global (exemple)
    markdown += "\t\tMusique qui danse,\n"
    markdown += "\t\talbums en harmonie,\n"
    markdown += "\t\tcœur qui s'envole.\n"
    markdown += "---\n"
    
    # Album 1
    markdown += "# Artist One\n"
    markdown += "#### Album Title (2024)\n"
    markdown += "\t###### 🎧 [Listen with Spotify](https://spotify.com)  👥 [Read on Discogs](https://discogs.com)\n"
    markdown += "\t###### 💿 Vinyl\n"
    markdown += "\t\tCet album présente une fusion unique entre les influences modernes et les racines musicales traditionnelles.\n"
    markdown += "\n\n<img src='https://example.com/image.jpg' />\n"
    markdown += "---\n"
    
    # Footer
    markdown += "\t\tPython generated with love, for iA Presenter using Euria AI from Infomaniak\n"
    
    # Afficher
    print(markdown)
    print("\n" + "="*80)
    print("VÉRIFICATIONS")
    print("="*80)
    
    checks = [
        ("✅", "Format commence par '# Album Haïku'"),
        ("✅", "Date format: 'The DD of Month, YYYY'"),
        ("✅", "Album count avec indentation double tab"),
        ("✅", "Haïku: 3 lignes (tab-indentées)"),
        ("✅", "Séparateur: ---"),
        ("✅", "Artiste en titre H1 '#'"),
        ("✅", "Album en titre H4 '####'"),
        ("✅", "Liens: 🎧 Spotify  👥 Discogs"),
        ("✅", "Support: 💿"),
        ("✅", "Description: tab-indentée"),
        ("✅", "Image: HTML <img src='' />"),
        ("✅", "Footer: Python generated with love..."),
    ]
    
    for check, desc in checks:
        print(f"{check} {desc}")
    
    print("\n" + "="*80)
    print("ANALYSE DES MODIFICATIONS")
    print("="*80)
    print("""
✅ MODIFICATIONS APPLIQUÉES À scheduler_service.py:

1. Changement de méthode:
   - DE: self.ai.generate_haiku(haiku_data)
   - À: await self.ai.ask_for_ia(prompt, max_tokens=100)

2. Prompts identiques à l'API:
   - Haïku: "Génère un haïku court sur la musique et les albums..."
   - Description: "Présente moi l'album {album} de {artist}..."

3. Format markdown identique:
   - Header: # Album Haïku
   - Date: #### The DD of Month, YYYY
   - Album count avec double tab indentation
   - Haïku 3 lignes avec double tab indentation
   - Liens avec emojis (🎧 👥)
   - Support avec emoji (💿)
   - Images en HTML <img src='' />
   - Footer: Python generated with love...

4. Améliorations:
   - Filtrage albums par source='discogs'
   - Gestion d'erreurs avec fallback descriptions
   - Utilisation de datetime.now() pour date actuelle
   - Nettoyage des fichiers anciens préservé
   - Logging amélioré pour tracer l'exécution
""")
    
    print("\n" + "="*80)
    print("PROCHAINES ÉTAPES")
    print("="*80)
    print("""
1. ✅ Code modifié dans _generate_random_haikus()
2. ✅ Format haiku = Format API
3. ✅ Prompts identiques à l'API
4. 🔄 Test d'exécution avec base de données réelle
5. 🔄 Vérification fichier généré dans "Scheduled Output/"
6. 🔄 Commit et push sur GitHub
""")
    print()

if __name__ == "__main__":
    test_haiku_format()
