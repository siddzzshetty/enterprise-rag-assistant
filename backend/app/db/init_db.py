from pathlib import Path
import sqlite3

from backend.app.core.config import get_settings
from backend.app.core.security import hash_password
from backend.app.db.connection import Database


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


class SeedData:
    clients = [
        ("Acme Research", "acme-research"),
        ("Northstar Analytics", "northstar-analytics"),
    ]

    projects = [
        ("Acme Research", [
            ("Retail Pricing Study", "retail-pricing-study", "Consumer pricing perceptions across metro markets."),
            ("Brand Health Tracker", "brand-health-tracker", "Quarterly brand tracking and awareness study."),
        ]),
        ("Northstar Analytics", [
            ("B2B Buying Journey", "b2b-buying-journey", "Decision-making research for enterprise buyers."),
            ("Customer Satisfaction Audit", "customer-satisfaction-audit", "VoC analysis and satisfaction diagnostics."),
        ]),
    ]

    users = [
        ("Acme Research", "admin@acme.com", "acme_admin", "Acme Admin", "Password123!"),
        ("Northstar Analytics", "admin@northstar.com", "northstar_admin", "Northstar Admin", "Password123!"),
    ]


class DatabaseInitializer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.database = Database()

    def initialize(self) -> None:
        with self.database.connect() as connection:
            self._apply_schema(connection)
            self._seed_reference_data(connection)
            connection.commit()

    def _apply_schema(self, connection: sqlite3.Connection) -> None:
        with SCHEMA_PATH.open("r", encoding="utf-8") as schema_file:
            connection.executescript(schema_file.read())

    def _seed_reference_data(self, connection: sqlite3.Connection) -> None:
        client_ids: dict[str, int] = {}

        for client_name, client_slug in SeedData.clients:
            connection.execute(
                "INSERT OR IGNORE INTO clients (name, slug) VALUES (?, ?)",
                (client_name, client_slug),
            )
            client_ids[client_name] = connection.execute(
                "SELECT id FROM clients WHERE slug = ?",
                (client_slug,),
            ).fetchone()[0]

        for client_name, project_items in SeedData.projects:
            client_id = client_ids[client_name]
            for project_name, project_slug, project_description in project_items:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO projects (client_id, name, slug, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (client_id, project_name, project_slug, project_description),
                )

        for client_name, email, username, full_name, password in SeedData.users:
            client_id = client_ids[client_name]
            connection.execute(
                """
                INSERT OR IGNORE INTO users (client_id, email, username, full_name, password_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (client_id, email, username, full_name, hash_password(password)),
            )


def initialize_database() -> None:
    DatabaseInitializer().initialize()


if __name__ == "__main__":
    initialize_database()
