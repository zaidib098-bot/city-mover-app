import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).with_name("city_app.db")


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    """إنشاء الجداول الأساسية إذا لم تكن موجودة."""
    with get_connection() as conn:
        cur = conn.cursor()

        # جدول المستخدمين
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'owner', 'admin'))
            )
            """
        )

        # جدول المدن
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            """
        )

        # جدول العقارات / المنازل
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                city_id INTEGER NOT NULL,
                area TEXT,
                title TEXT NOT NULL,
                description TEXT,
                rent INTEGER,
                lat REAL,
                lon REAL,
                services TEXT,
                FOREIGN KEY(owner_id) REFERENCES users(id),
                FOREIGN KEY(city_id) REFERENCES cities(id)
            )
            """
        )

        conn.commit()

        # تعبئة المدن الافتراضية إذا كانت فارغة
        cur.execute("SELECT COUNT(*) FROM cities")
        count = cur.fetchone()[0]
        if count == 0:
            default_cities = [
                "دمشق", "حلب", "حمص", "حماة", "اللاذقية", "طرطوس",
                "دير الزور", "الرقة", "الحسكة", "ريف دمشق",
                "درعا", "القنيطرة", "سويدا", "إدلب"
            ]
            cur.executemany(
                "INSERT INTO cities (name) VALUES (?)",
                [(c,) for c in default_cities]
            )
            conn.commit()

        # إنشاء مستخدمين تجريبيين إذا لم يوجدوا
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        if user_count == 0:
            demo_users = [
                ("user1", "123456", "user"),
                ("owner1", "123456", "owner"),
            ]
            cur.executemany(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                demo_users,
            )
            conn.commit()


def create_user(username: str, password: str, role: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role),
        )
        conn.commit()
        return cur.lastrowid


def get_user_by_credentials(username: str, password: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, role FROM users WHERE username=? AND password=?",
            (username, password),
        )
        row = cur.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "role": row[2]}
        return None


def get_cities():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM cities ORDER BY name")
        return [{"id": r[0], "name": r[1]} for r in cur.fetchall()]


def get_city_by_id(city_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM cities WHERE id=?", (city_id,))
        r = cur.fetchone()
        if r:
            return {"id": r[0], "name": r[1]}
        return None


def add_property(owner_id: int, city_id: int, area: str, title: str, description: str,
                 rent: int, lat: float, lon: float, services: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO properties (owner_id, city_id, area, title, description, rent, lat, lon, services)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (owner_id, city_id, area, title, description, rent, lat, lon, services),
        )
        conn.commit()
        return cur.lastrowid


def get_properties_by_city(city_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.title, p.area, p.description, p.rent, p.lat, p.lon, p.services,
                   u.username
            FROM properties p
            JOIN users u ON p.owner_id = u.id
            WHERE p.city_id=?
            ORDER BY p.id DESC
            """,
            (city_id,),
        )
        res = []
        for r in cur.fetchall():
            res.append(
                {
                    "id": r[0],
                    "title": r[1],
                    "area": r[2],
                    "description": r[3],
                    "rent": r[4],
                    "lat": r[5],
                    "lon": r[6],
                    "services": r[7],
                    "owner_username": r[8],
                }
            )
        return res


def get_properties_by_owner(owner_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, title, area, description, rent, lat, lon, services
            FROM properties
            WHERE owner_id=?
            ORDER BY id DESC
            """,
            (owner_id,),
        )
        res = []
        for r in cur.fetchall():
            res.append(
                {
                    "id": r[0],
                    "title": r[1],
                    "area": r[2],
                    "description": r[3],
                    "rent": r[4],
                    "lat": r[5],
                    "lon": r[6],
                    "services": r[7],
                }
            )
        return res
