#!/usr/bin/env python3
"""Script de test des améliorations Roon."""

def test_artist_variants():
    """Tester la génération de variantes d'artiste."""
    from app.services.roon_service import RoonService
    
    # Créer une instance fictive pour tester les méthodes helper
    service = RoonService.__new__(RoonService)
    
    # Test 1: Artiste avec "The"
    variants = service._generate_artist_variants("The Beatles")
    print("🎸 Variantes pour 'The Beatles':")
    for v in variants:
        print(f"  - {v}")
    assert "Beatles" in variants
    assert "The Beatles" in variants
    
    # Test 2: Artiste sans "The"
    variants = service._generate_artist_variants("Pink Floyd")
    print("\n🎸 Variantes pour 'Pink Floyd':")
    for v in variants:
        print(f"  - {v}")
    assert "Pink Floyd" in variants
    assert "The Pink Floyd" in variants
    
    # Test 3: Artiste avec "and"
    variants = service._generate_artist_variants("Simon and Garfunkel")
    print("\n🎸 Variantes pour 'Simon and Garfunkel':")
    for v in variants:
        print(f"  - {v}")
    assert "Simon & Garfunkel" in variants
    
    print("\n✅ Test des variantes d'artiste: RÉUSSI\n")


def test_album_variants():
    """Tester la génération de variantes d'album."""
    from app.services.roon_service import RoonService
    
    service = RoonService.__new__(RoonService)
    
    # Test 1: Album normal
    variants = service._generate_album_variants("Abbey Road")
    print("💿 Variantes pour 'Abbey Road':")
    for v in variants:
        print(f"  - {v}")
    assert "Abbey Road" in variants
    assert len(variants) > 1
    
    # Test 2: Soundtrack
    variants = service._generate_album_variants("Inception")
    print("\n💿 Variantes pour 'Inception':")
    for v in variants:
        print(f"  - {v}")
    assert "Inception [Original Motion Picture Soundtrack]" in variants
    assert "Inception (Soundtrack)" in variants
    assert "Inception OST" in variants
    
    # Test 3: Album avec "The"
    variants = service._generate_album_variants("The Wall")
    print("\n💿 Variantes pour 'The Wall':")
    for v in variants:
        print(f"  - {v}")
    assert "Wall" in variants
    
    print("\n✅ Test des variantes d'album: RÉUSSI\n")


def test_imports():
    """Tester que tous les imports fonctionnent."""
    try:
        from app.services.roon_service import RoonService
        print("✅ Import RoonService: OK")
        
        # Vérifier que les méthodes existent
        assert hasattr(RoonService, 'play_album')
        assert hasattr(RoonService, 'play_track')
        assert hasattr(RoonService, 'playback_control')
        assert hasattr(RoonService, '_generate_artist_variants')
        assert hasattr(RoonService, '_generate_album_variants')
        print("✅ Toutes les méthodes sont présentes")
        
    except Exception as e:
        print(f"❌ Erreur d'import: {e}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST DES AMÉLIORATIONS ROON")
    print("=" * 60)
    print()
    
    try:
        test_imports()
        print()
        test_artist_variants()
        test_album_variants()
        
        print("=" * 60)
        print("✅ TOUS LES TESTS RÉUSSIS!")
        print("=" * 60)
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ ÉCHEC DES TESTS: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        exit(1)
