"""Replace playlists with album collections

Revision ID: 003
Revises: 002
Create Date: 2026-02-01 20:55:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Supprimer les anciennes tables de playlists
    op.drop_table('playlist_tracks')
    op.drop_table('playlists')
    
    # Créer les nouvelles tables de collections d'albums
    op.create_table('album_collections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('search_type', sa.String(), nullable=True),
        sa.Column('search_criteria', sa.JSON(), nullable=True),
        sa.Column('ai_query', sa.Text(), nullable=True),
        sa.Column('album_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_album_collections_name'), 'album_collections', ['name'], unique=False)
    op.create_index(op.f('ix_album_collections_search_type'), 'album_collections', ['search_type'], unique=False)
    
    op.create_table('collection_albums',
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('album_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['album_id'], ['albums.id'], ),
        sa.ForeignKeyConstraint(['collection_id'], ['album_collections.id'], ),
        sa.PrimaryKeyConstraint('collection_id', 'album_id')
    )
    op.create_index(op.f('ix_collection_albums_position'), 'collection_albums', ['position'], unique=False)


def downgrade():
    # Supprimer les tables de collections d'albums
    op.drop_index(op.f('ix_collection_albums_position'), table_name='collection_albums')
    op.drop_table('collection_albums')
    op.drop_index(op.f('ix_album_collections_search_type'), table_name='album_collections')
    op.drop_index(op.f('ix_album_collections_name'), table_name='album_collections')
    op.drop_table('album_collections')
    
    # Recréer les anciennes tables de playlists
    op.create_table('playlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('algorithm', sa.String(), nullable=True),
        sa.Column('ai_prompt', sa.Text(), nullable=True),
        sa.Column('track_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('playlist_tracks',
        sa.Column('playlist_id', sa.Integer(), nullable=False),
        sa.Column('track_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['playlist_id'], ['playlists.id'], ),
        sa.ForeignKeyConstraint(['track_id'], ['tracks.id'], ),
        sa.PrimaryKeyConstraint('playlist_id', 'track_id')
    )
