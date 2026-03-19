"""SQLite database for Dubai Prod Agent."""

import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "agent.db"


async def get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db


async def init_db():
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            platform TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            notes TEXT DEFAULT '',
            monthly_fee REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER REFERENCES clients(id),
            platform TEXT NOT NULL,
            content_type TEXT DEFAULT 'post',
            caption TEXT DEFAULT '',
            media_url TEXT DEFAULT '',
            status TEXT DEFAULT 'draft',
            scheduled_at TIMESTAMP,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            client_id INTEGER REFERENCES clients(id),
            assigned_agent TEXT DEFAULT 'manager',
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER REFERENCES clients(id),
            platform TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL DEFAULT 0,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS research_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            client_id INTEGER REFERENCES clients(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES research_projects(id),
            company_name TEXT NOT NULL,
            contact_name TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            website TEXT DEFAULT '',
            industry TEXT DEFAULT '',
            location TEXT DEFAULT '',
            company_size TEXT DEFAULT '',
            source TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            status TEXT DEFAULT 'new',
            tags TEXT DEFAULT '',
            found_by TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            task_type TEXT DEFAULT 'reels',
            status TEXT DEFAULT 'new',
            client_id INTEGER REFERENCES clients(id),
            original_command TEXT DEFAULT '',
            delivery TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS workflow_stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL REFERENCES workflows(id),
            stage_number INTEGER NOT NULL,
            stage_name TEXT NOT NULL,
            agent_role TEXT NOT NULL,
            status TEXT DEFAULT 'waiting',
            depends_on INTEGER,
            input_data TEXT DEFAULT '',
            output_data TEXT DEFAULT '',
            deliverables TEXT DEFAULT '',
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS designs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER REFERENCES content(id),
            prompt TEXT DEFAULT '',
            image_url TEXT DEFAULT '',
            video_url TEXT DEFAULT '',
            music_url TEXT DEFAULT '',
            voiceover_text TEXT DEFAULT '',
            pipeline_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sections_json TEXT DEFAULT '[]',
            rendered_html TEXT DEFAULT '',
            language TEXT DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            subject TEXT DEFAULT '',
            preview_text TEXT DEFAULT '',
            sender_name TEXT DEFAULT 'Dubai Prod',
            sender_email TEXT DEFAULT 'info@dubaiprod.com',
            template_json TEXT DEFAULT '[]',
            rendered_html TEXT DEFAULT '',
            target_segment TEXT DEFAULT '',
            selected_leads TEXT DEFAULT '[]',
            status TEXT DEFAULT 'draft',
            scheduled_at TIMESTAMP,
            sent_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Migrations — add columns if missing
    try:
        await db.execute("ALTER TABLE tasks ADD COLUMN source TEXT DEFAULT 'platform'")
    except Exception:
        pass  # Column already exists

    await db.commit()
    await db.close()
