"""Migration pour ajouter les colonnes AI aux albums."""
from app.database import engine
from sqlalchemy import text

def migrate():
    """Ajouter les colonnes AI aux albums."""
    with engine.connect() as conn:
        # Ajouter les colonnes si elles n'existent pas
        try:
            conn.execute(text('ALTER TABLE albums ADD COLUMN genre VARCHAR(200)'))
            conn.execute(text('CREATE INDEX ix_albums_genre ON albums(genre)'))
            print('✅ Colonne genre ajoutée')
        except Exception as e:
            print(f'⚠️  Genre déjà existant ou erreur: {str(e)[:100]}')
        
        try:
            conn.execute(text('ALTER TABLE albums ADD COLUMN image_url VARCHAR(1000)'))
            print('✅ Colonne image_url ajoutée')
        except Exception as e:
            print(f'⚠️  Image_url déjà existant ou erreur: {str(e)[:100]}')
        
        try:
            conn.execute(text('ALTER TABLE albums ADD COLUMN ai_description VARCHAR(2000)'))
            print('✅ Colonne ai_description ajoutée')
        except Exception as e:
            print(f'⚠️  AI_description déjà existant ou erreur: {str(e)[:100]}')
        
        try:
            conn.execute(text('ALTER TABLE albums ADD COLUMN ai_style VARCHAR(500)'))
            print('✅ Colonne ai_style ajoutée')
        except Exception as e:
            print(f'⚠️  AI_style déjà existant ou erreur: {str(e)[:100]}')
        
        conn.commit()
        print('\n✅ Migration terminée')

if __name__ == '__main__':
    migrate()
