#!/usr/bin/env python3
"""Regenerate album descriptions using EurIA (AIService.generate_album_info).

Defaults to updating ALL albums. Use --only-missing to target albums without
ai_info, and --limit to cap the number processed in one run.
"""
import argparse
import asyncio
import sys
from typing import Optional

# Ensure app imports work when running from repo root or elsewhere.
sys.path.insert(0, '/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend')

from app.core.config import get_settings
from app.database import SessionLocal
from app.models import Album, Metadata
from app.services.external.ai_service import AIService
from sqlalchemy.orm import joinedload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenerate album descriptions with EurIA"
    )
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Update only albums missing metadata.ai_info",
    )
    parser.add_argument(
        "--only-discogs",
        action="store_true",
        help="Update only albums imported from Discogs",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max number of albums to process (0 = no limit)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between AI calls in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing changes to the database",
    )
    return parser


def get_album_query(db, only_missing: bool, only_discogs: bool):
    query = db.query(Album).options(
        joinedload(Album.album_metadata),
        joinedload(Album.artists),
    )

    if only_discogs:
        query = query.filter(Album.source == "discogs")

    if only_missing:
        query = query.outerjoin(Metadata, Album.id == Metadata.album_id).filter(
            (Metadata.id == None) | (Metadata.ai_info == None)
        )

    return query


async def update_all_album_descriptions(
    only_missing: bool,
    only_discogs: bool,
    limit: int,
    delay: float,
    dry_run: bool,
) -> None:
    settings = get_settings()
    secrets = settings.secrets
    euria_config = secrets.get("euria", {})

    ai_service = AIService(
        url=euria_config.get("url"),
        bearer=euria_config.get("bearer"),
        max_attempts=euria_config.get("max_attempts", 5),
    )

    db = SessionLocal()

    try:
        query = get_album_query(db, only_missing, only_discogs)
        if limit and limit > 0:
            query = query.limit(limit)

        albums = query.all()
        total = len(albums)

        print(f"Albums to process: {total}")

        updated = 0
        skipped = 0
        failed = 0

        for idx, album in enumerate(albums, 1):
            artist_names = [a.name for a in album.artists] if album.artists else []
            artist_name = ", ".join(artist_names) if artist_names else "Unknown"

            print(f"[{idx}/{total}] {artist_name} - {album.title}")

            try:
                if delay > 0:
                    await asyncio.sleep(delay)

                ai_info: Optional[str] = await ai_service.generate_album_info(
                    artist_name,
                    album.title,
                )

                if not ai_info:
                    print("  Skipped: AI returned no content")
                    skipped += 1
                    continue

                if not album.album_metadata:
                    album.album_metadata = Metadata(album_id=album.id, ai_info=ai_info)
                else:
                    album.album_metadata.ai_info = ai_info

                if dry_run:
                    db.rollback()
                    print("  Dry-run: change not saved")
                else:
                    db.commit()
                    print(f"  Updated: {len(ai_info)} chars")

                updated += 1
            except Exception as exc:
                db.rollback()
                failed += 1
                print(f"  Failed: {exc}")

        print("\nDone.")
        print(f"Updated: {updated}")
        print(f"Skipped: {skipped}")
        print(f"Failed: {failed}")
    finally:
        db.close()


def main() -> None:
    args = build_arg_parser().parse_args()
    asyncio.run(
        update_all_album_descriptions(
            only_missing=args.only_missing,
            only_discogs=args.only_discogs,
            limit=args.limit,
            delay=args.delay,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
