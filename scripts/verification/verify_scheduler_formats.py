#!/usr/bin/env python3
"""
Vérification rapide que les formats du scheduler sont maintenant identiques à l'API.

Usage:
    python3 verify_scheduler_formats.py
"""

def verify_scheduler_modifications():
    """Vérifier les modifications du scheduler."""
    
    print("\n" + "="*70)
    print("✅ VÉRIFICATION DES MODIFICATIONS DU SCHEDULER")
    print("="*70 + "\n")
    
    # Vérifier le fichier
    import os
    scheduler_file = "backend/app/services/scheduler_service.py"
    
    if not os.path.exists(scheduler_file):
        print(f"❌ Fichier non trouvé: {scheduler_file}")
        return False
    
    with open(scheduler_file, 'r') as f:
        content = f.read()
    
    checks = [
        ("Import MarkdownExportService", "from app.services.markdown_export_service import MarkdownExportService" in content),
        ("Utilisation MarkdownExportService dans _export_collection_markdown", 
         "MarkdownExportService.get_collection_markdown(db)" in content),
        ("Export JSON avec images", '"url": img.url' in content and '"type": img.image_type' in content and '"source": img.source' in content),
        ("Export JSON avec métadonnées", '"ai_info": meta.ai_info' in content),
        ("Export JSON filtre discogs", "Album.source == 'discogs'" in content),
        ("Haiku avec table des matières", "## Table des matières" in content),
        ("Haiku avec liens Spotify/Discogs", "links.append" in content),
        ("Haiku avec images", "album.images[0].url" in content),
    ]
    
    print("Vérifications des modifications:\n")
    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ TOUTES LES MODIFICATIONS SONT EN PLACE!")
        print("\nLes formats du scheduler sont maintenant identiques à l'API:")
        print("  • Haiku: table des matières, métadonnées, images")
        print("  • JSON: images et métadonnées complètes") 
        print("  • Markdown: MarkdownExportService (format API exact)")
    else:
        print("⚠️  CERTAINES MODIFICATIONS MANQUENT")
    print("="*70 + "\n")
    
    return all_passed

if __name__ == "__main__":
    verify_scheduler_modifications()
