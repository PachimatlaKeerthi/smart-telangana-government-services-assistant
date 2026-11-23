
# ============================================================
# FAVOURITE SERVICES DATABASE FUNCTIONS
# ============================================================

def create_favorites_table():

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, service_key),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (service_key)
                    REFERENCES services(service_key)
                    ON DELETE CASCADE
            )
        """)

        connection.commit()

    finally:
        connection.close()


def add_favorite(user_id, service_key):

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO favorites
            (user_id, service_key)
            VALUES (?, ?)
        """, (user_id, service_key))

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def get_user_favorites(user_id):

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                s.service_key,
                s.name,
                s.description,
                f.created_at
            FROM favorites f
            JOIN services s
                ON f.service_key = s.service_key
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
        """, (user_id,))

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def remove_favorite(user_id, service_key):

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM favorites
            WHERE user_id = ?
            AND service_key = ?
        """, (user_id, service_key))

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()

import sqlite3
import json
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "government_services.db"


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database(categories, services):

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                service_key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                notice TEXT,
                details TEXT,
                portal_name TEXT,
                portal_instructions TEXT,
                official_url TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_services (
                category_key TEXT,
                service_key TEXT,
                PRIMARY KEY (category_key, service_key),
                FOREIGN KEY (category_key)
                    REFERENCES categories(category_key),
                FOREIGN KEY (service_key)
                    REFERENCES services(service_key)
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]

        if category_count == 0:

            for category_key, category in categories.items():

                cursor.execute("""
                    INSERT INTO categories
                    (category_key, name, description)
                    VALUES (?, ?, ?)
                """, (
                    category_key,
                    category["name"],
                    category["description"]
                ))

            for service_key, service in services.items():

                cursor.execute("""
                    INSERT INTO services (
                        service_key, name, description, notice,
                        details, portal_name, portal_instructions,
                        official_url
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    service_key,
                    service["name"],
                    service["description"],
                    service.get("notice", ""),
                    json.dumps(service.get("details", [])),
                    service.get("portal_name", ""),
                    json.dumps(service.get("portal_instructions", [])),
                    service.get("official_url", "")
                ))

            for category_key, category in categories.items():

                for service_key in category["services"]:

                    if service_key in services:

                        cursor.execute("""
                            INSERT INTO category_services
                            (category_key, service_key)
                            VALUES (?, ?)
                        """, (category_key, service_key))

        connection.commit()

    finally:
        connection.close()


# ============================================================
# USER REGISTRATION AND LOGIN DATABASE FUNCTIONS
# ============================================================

def create_users_table():

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()

    finally:
        connection.close()


def add_user(username, email, password_hash):

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        """, (username, email, password_hash))

        connection.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connection.close()


def get_user_by_email(email):

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,))

        user = cursor.fetchone()

        return dict(user) if user else None

    finally:
        connection.close()


# ============================================================
# PASSWORD RESET DATABASE FUNCTIONS
# ============================================================

def update_user_password(email, password_hash):

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE users
            SET password_hash = ?
            WHERE email = ?
        """, (password_hash, email))

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def create_password_resets_table():

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                token_hash TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)

        connection.commit()

    finally:
        connection.close()


def save_password_reset(email, token_hash, expires_at):

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM password_resets
            WHERE email = ?
        """, (email,))

        cursor.execute("""
            INSERT INTO password_resets
            (token_hash, email, expires_at)
            VALUES (?, ?, ?)
        """, (token_hash, email, expires_at))

        connection.commit()

    finally:
        connection.close()


def get_password_reset(token_hash):

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT email, expires_at
            FROM password_resets
            WHERE token_hash = ?
        """, (token_hash,))

        row = cursor.fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def delete_password_reset(token_hash):

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM password_resets
            WHERE token_hash = ?
        """, (token_hash,))

        connection.commit()

    finally:
        connection.close()


# ============================================================
# CATEGORY DATABASE FUNCTIONS
# ============================================================

def get_all_categories():

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM categories
            ORDER BY category_key
        """)

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# ============================================================
# SERVICE DATABASE FUNCTIONS
# ============================================================

def get_all_services():

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM services
            ORDER BY service_key
        """)

        result = []

        for row in cursor.fetchall():

            service = dict(row)

            service["details"] = json.loads(
                service["details"] or "[]"
            )

            service["portal_instructions"] = json.loads(
                service["portal_instructions"] or "[]"
            )

            result.append(service)

        return result

    finally:
        connection.close()


def get_category_data(category_key):

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT category_key, name, description
            FROM categories
            WHERE category_key = ?
        """, (category_key,))

        category_row = cursor.fetchone()

        if category_row is None:
            return None, []

        selected_category = dict(category_row)

        cursor.execute("""
            SELECT
                s.service_key AS key,
                s.name,
                s.description
            FROM services s
            JOIN category_services cs
                ON s.service_key = cs.service_key
            WHERE cs.category_key = ?
            ORDER BY s.name
        """, (category_key,))

        category_services = [
            dict(row) for row in cursor.fetchall()
        ]

        return selected_category, category_services

    finally:
        connection.close()


def get_service_data(service_key):

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM services
            WHERE service_key = ?
        """, (service_key,))

        row = cursor.fetchone()

        if row is None:
            return None

        service = dict(row)

        service["details"] = json.loads(
            service["details"] or "[]"
        )

        service["portal_instructions"] = json.loads(
            service["portal_instructions"] or "[]"
        )

        return service

    finally:
        connection.close()


# ============================================================
# SEARCH DATABASE FUNCTION
# ============================================================

def search_database(search_text):

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        search_text = " ".join(str(search_text or "").lower().split())

        if not search_text:
            return []

        cursor.execute("""
            SELECT
                category_key AS key,
                name,
                description,
                'category' AS type
            FROM categories
        """)

        category_results = []
        service_results = []

        for row in cursor.fetchall():

            category = dict(row)

            searchable_category = (
                category["name"] + " " +
                (category["description"] or "")
            ).lower()

            if search_text in searchable_category:

                category["priority"] = (
                    0 if category["name"].lower() == search_text
                    else 1
                )

                category_results.append(category)

        cursor.execute("""
            SELECT
                service_key AS key,
                name,
                description,
                details
            FROM services
        """)

        for row in cursor.fetchall():

            service = dict(row)

            details = json.loads(
                service["details"] or "[]"
            )

            searchable_text = (
                service["name"] + " " +
                (service["description"] or "") + " " +
                " ".join(details)
            ).lower()

            if search_text in searchable_text:

                service_results.append({
                    "key": service["key"],
                    "name": service["name"],
                    "description": service["description"],
                    "type": "service",
                    "priority": (
                        0 if service["name"].lower() == search_text
                        else 1 if search_text in service["name"].lower()
                        else 2
                    )
                })

        combined_results = service_results + category_results

        combined_results.sort(
            key=lambda item: item["priority"]
        )

        for item in combined_results:
            item.pop("priority", None)

        return combined_results

    finally:
        connection.close()

# ============================================================
# FAVOURITE SERVICES DATABASE FUNCTIONS
# ============================================================

def create_favorites_table():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, service_key),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (service_key)
                    REFERENCES services(service_key)
                    ON DELETE CASCADE
            )
        """)

        connection.commit()

    finally:
        connection.close()


def add_favorite(user_id, service_key):
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO favorites
            (user_id, service_key)
            VALUES (?, ?)
        """, (user_id, service_key))

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()


def get_user_favorites(user_id):
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                s.service_key,
                s.name,
                s.description,
                f.created_at
            FROM favorites f
            JOIN services s
                ON f.service_key = s.service_key
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
        """, (user_id,))

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def remove_favorite(user_id, service_key):
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM favorites
            WHERE user_id = ?
            AND service_key = ?
        """, (user_id, service_key))

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()

