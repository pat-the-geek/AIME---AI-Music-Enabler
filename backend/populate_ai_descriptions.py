"""Peupler les descriptions AI des albums."""
from app.database import get_db
from app.models import Album
from sqlalchemy import func

def populate_sample_descriptions():
    """Ajouter des descriptions AI à quelques albums pour tester."""
    db = next(get_db())
    
    # Définir quelques descriptions d'exemple basées sur des genres/styles connus
    sample_data = [
        {
            "keywords": ["rock", "alternative"],
            "genre": "Rock Alternatif",
            "ai_style": "énergique, guitares puissantes, mélancolique",
            "ai_description": "Album de rock alternatif caractérisé par des guitares énergiques et une atmosphère mélancolique. Influence grunge et post-rock avec des mélodies accrocheuses."
        },
        {
            "keywords": ["jazz", "cool"],
            "genre": "Jazz",
            "ai_style": "sophistiqué, cool, improvisé",
            "ai_description": "Jazz cool sophistiqué avec des improvisations subtiles et une ambiance décontractée. Influences bebop et hard bop, parfait pour une soirée relaxante."
        },
        {
            "keywords": ["electronic", "ambient", "atmosphérique"],
            "genre": "Electronic",
            "ai_style": "atmosphérique, ambient, planant",
            "ai_description": "Musique électronique atmosphérique et planante, créant des paysages sonores immersifs. Idéal pour la méditation ou le travail créatif."
        },
        {
            "keywords": ["blues", "soul"],
            "genre": "Blues/Soul",
            "ai_style": "émouvant, profond, vintage",
            "ai_description": "Blues et soul authentique avec des voix puissantes et émouvantes. Instrumentation vintage avec guitare, orgue et section de cuivres."
        },
        {
            "keywords": ["classical", "symphonique"],
            "genre": "Classique",
            "ai_style": "orchestral, majestueux, émotionnel",
            "ai_description": "Œuvre orchestrale classique avec de riches arrangements symphoniques. Interprétation émotionnelle et technique irréprochable."
        },
        {
            "keywords": ["90", "années 90", "grunge"],
            "genre": "Rock Alternatif",
            "ai_style": "grunge, rock alternatif années 90, puissant",
            "ai_description": "Rock alternatif emblématique des années 90, avec une attitude grunge et des riffs de guitare puissants. Son brut et authentique caractéristique de l'époque."
        },
        {
            "keywords": ["funk", "groove"],
            "genre": "Funk",
            "ai_style": "groovy, dansant, rythmé",
            "ai_description": "Funk groovy avec des lignes de basse irrésistibles et des rythmes entraînants. Parfait pour danser avec une section de cuivres énergique."
        },
        {
            "keywords": ["indie", "folk"],
            "genre": "Indie Folk",
            "ai_style": "acoustique, intime, poétique",
            "ai_description": "Indie folk acoustique et intime avec des paroles poétiques. Arrangements simples mettant en valeur la voix et la guitare."
        },
        {
            "keywords": ["metal", "heavy"],
            "genre": "Metal",
            "ai_style": "heavy, agressif, technique",
            "ai_description": "Metal heavy avec des riffs agressifs et une technique instrumentale impressionnante. Double grosse caisse et guitares saturées."
        },
        {
            "keywords": ["reggae", "dub"],
            "genre": "Reggae/Dub",
            "ai_style": "relaxant, rythmé, basses profondes",
            "ai_description": "Reggae et dub avec des basses profondes et des effets spacieux. Rythme laid-back et ambiance jamaïcaine positive."
        }
    ]
    
    # Répartir ces descriptions sur différents albums
    total_albums = db.query(func.count(Album.id)).scalar()
    print(f"Total d'albums dans la base: {total_albums}")
    
    # Récupérer des albums aléatoires et leur assigner des descriptions
    albums_updated = 0
    
    for i, data in enumerate(sample_data):
        # Récupérer quelques albums (environ 10-20 par catégorie)
        albums_batch = db.query(Album).filter(
            Album.ai_description.is_(None)
        ).offset(i * 20).limit(20).all()
        
        for album in albums_batch:
            album.genre = data["genre"]
            album.ai_style = data["ai_style"]
            album.ai_description = data["ai_description"]
            
            # Récupérer l'URL de l'image si disponible
            if album.images:
                album.image_url = album.images[0].url
            
            albums_updated += 1
        
        db.commit()
        print(f"✅ {len(albums_batch)} albums mis à jour avec le genre '{data['genre']}'")
    
    print(f"\n✅ Total: {albums_updated} albums mis à jour avec des descriptions AI")
    
    # Afficher quelques exemples
    print("\n📚 Exemples d'albums avec descriptions AI:")
    examples = db.query(Album).filter(
        Album.ai_description.isnot(None)
    ).limit(5).all()
    
    for album in examples:
        artist = album.artists[0].name if album.artists else "Unknown"
        print(f"\n  {album.title} - {artist} ({album.year})")
        print(f"  Genre: {album.genre}")
        print(f"  Style: {album.ai_style}")
        print(f"  Description: {album.ai_description[:100]}...")

if __name__ == '__main__':
    populate_sample_descriptions()
