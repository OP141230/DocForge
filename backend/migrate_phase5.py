"""Database migration for Phase 5 - Research, Citations & Factual Verification.

The script applies ``app/core/db_schema.sql``, which only contains
``CREATE ... IF NOT EXISTS`` statements. That means it:

* creates the Phase 5 tables on an existing Phase 1-4 database,
* creates any table a previous phase somehow missed,
* is safe to run more than once,
* never drops or rewrites data.

Why not ALTER TABLE? Phase 5 only *adds* tables. Nothing in Phases 1-4 changes
shape, so additive DDL is enough - and it avoids the failure mode where a
migration half-rewrites a table and loses rows.

Known limitation: SQLite cannot change a column/foreign key in place. The
``brief_file_attachments`` foreign-key fix in ``db_schema.sql`` therefore only
applies to databases created from scratch; existing databases keep the old
constraint (which SQLite does not enforce anyway, because DocForge does not
enable ``PRAGMA foreign_keys``). Phase 5 deletes child rows explicitly instead of
relying on cascades.

Usage (PowerShell, from the backend directory):
    .\\.venv\\Scripts\\Activate.ps1
    python migrate_phase5.py
"""
import asyncio
import os
from pathlib import Path

import aiosqlite

PHASE5_TABLES = (
    "research_sessions",
    "research_questions",
    "research_sources",
    "research_evidence",
    "citations",
    "claim_verifications",
    "claim_verification_evidence",
)


def find_database_path() -> str:
    """Support running from the project root or the backend directory."""
    for candidate in ("./docforge.db", "./backend/docforge.db"):
        if os.path.exists(candidate):
            return candidate
    return "./docforge.db"


async def migrate_phase5() -> None:
    db_path = find_database_path()
    schema_path = Path(__file__).parent / "app" / "core" / "db_schema.sql"

    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}")
        return

    print(f"Migrating database to Phase 5 schema: {db_path}")

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing = {row[0] for row in await cursor.fetchall()}

        schema_sql = schema_path.read_text(encoding="utf-8")
        await db.executescript(schema_sql)
        await db.commit()

        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        after = {row[0] for row in await cursor.fetchall()}

    created = [name for name in PHASE5_TABLES if name not in existing and name in after]
    already = [name for name in PHASE5_TABLES if name in existing]

    if already:
        print(f"  = {len(already)} Phase 5 table(s) already existed")
    for name in created:
        print(f"  + created {name}")

    missing = [name for name in PHASE5_TABLES if name not in after]
    if missing:
        print(f"  ! MISSING: {', '.join(missing)}")
    else:
        print("\nPhase 5 database migration complete.")
        print("New tables:")
        print("- research_sessions: one research run, linked to a brief/document")
        print("- research_questions: editable questions that drive discovery")
        print("- research_sources: web / user-URL / knowledge-base sources")
        print("- research_evidence: traceable passages tied to a source")
        print("- citations: document <-> source links for in-text citations")
        print("- claim_verifications: per-claim verification findings")
        print("- claim_verification_evidence: supporting/contradicting links")


if __name__ == "__main__":
    asyncio.run(migrate_phase5())
