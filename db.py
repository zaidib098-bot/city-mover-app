import sqlite3
import os
from pathlib import Path  

def get_db_path():
    """الحصول على مسار قاعدة البيانات المناسب لكل منصة"""
    try:
        # محاولة اكتشاف نظام الأندرويد باستخدام متغيرات البيئة
        android_runtime = os.environ.get('ANDROID_RUNTIME')
        android_data = os.environ.get('ANDROID_DATA')
        
        # إذا كنا على أندرويد (عند استخدام Pydroid أو Termux أو BeeWare)
        if android_runtime or android_data:
            # على Android - استخدام مسار التخزين الداخلي
            # هذا المسار يعمل مع معظم تطبيقات الأندرويد
            if 'PYKINATOR' in os.environ or 'PYTHONPATH' in os.environ:
                # لـ Pydroid
                db_path = "/storage/emulated/0/city_app.db"
            else:
                # مسار افتراضي للأندرويد
                db_path = "/data/data/com.example.citymover/databases/city_app.db"
            
            print(f"📱 Android DB path: {db_path}")
            return db_path
        else:
            # على أجهزة أخرى (Windows, Linux, macOS)
            db_path = str(Path(__file__).parent / "city_app.db")
            print(f"💻 Desktop DB path: {db_path}")
            return db_path
            
    except Exception as e:
        print(f"⚠️  Using fallback DB path: {e}")
        # إذا فشل كل شيء، استخدم المسار الحالي
        return str(Path(__file__).parent / "city_app.db")

def get_connection():
    """إنشاء اتصال بقاعدة البيانات"""
    db_path = get_db_path()
    print(f"🔗 Connecting to database: {db_path}")
    
    # التأكد من وجود المجلد
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    except Exception:
        # إذا فشل إنشاء المجلد، استخدم المسار الحالي
        db_path = str(Path(__file__).parent / "city_app.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """إنشاء الجداول الأساسية إذا لم تكن موجودة."""
    try:
        conn = get_connection()
        cur = conn.cursor()

        # جدول المستخدمين
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'owner', 'admin')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # جدول المدن
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(city_id) REFERENCES cities(id) ON DELETE CASCADE
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
                "INSERT OR IGNORE INTO cities (name) VALUES (?)",
                [(c,) for c in default_cities]
            )
            print(f"🏙️  Added {len(default_cities)} default cities")
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
                "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                demo_users,
            )
            print("👤 Added demo users: user1/123456 (user), owner1/123456 (owner)")
            conn.commit()
        
        conn.close()
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        # محاولة إنشاء ملف DB بسيط في حالة الخطأ
        try:
            db_path = str(Path(__file__).parent / "city_app.db")
            conn = sqlite3.connect(db_path)
            conn.close()
            print(f"📄 Created empty DB file: {db_path}")
        except Exception as create_error:
            print(f"❌ Failed to create DB file: {create_error}")

def create_user(username: str, password: str, role: str):
    """إنشاء مستخدم جديد"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role),
        )
        user_id = cur.lastrowid
        conn.commit()
        conn.close()
        print(f"👤 User created: {username} (ID: {user_id})")
        return user_id
    except sqlite3.IntegrityError:
        raise Exception("اسم المستخدم موجود مسبقاً")
    except Exception as e:
        print(f"❌ Create user error: {e}")
        raise Exception(f"خطأ في إنشاء المستخدم: {e}")

def get_user_by_credentials(username: str, password: str):
    """الحصول على بيانات المستخدم باستخدام اسم المستخدم وكلمة المرور"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, role FROM users WHERE username=? AND password=?",
            (username, password),
        )
        row = cur.fetchone()
        conn.close()
        
        if row:
            user_data = {"id": row[0], "username": row[1], "role": row[2]}
            print(f"🔐 User logged in: {username}")
            return user_data
        else:
            print(f"❌ Login failed for user: {username}")
            return None
    except Exception as e:
        print(f"❌ Get user credentials error: {e}")
        return None

def get_cities():
    """الحصول على قائمة جميع المدن"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM cities ORDER BY name")
        cities = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
        conn.close()
        print(f"🏙️  Retrieved {len(cities)} cities")
        return cities
    except Exception as e:
        print(f"❌ Get cities error: {e}")
        return []

def get_city_by_id(city_id: int):
    """الحصول على بيانات مدينة معينة"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM cities WHERE id=?", (city_id,))
        r = cur.fetchone()
        conn.close()
        
        if r:
            return {"id": r[0], "name": r[1]}
        return None
    except Exception as e:
        print(f"❌ Get city by id error: {e}")
        return None

def add_property(owner_id: int, city_id: int, area: str, title: str, description: str,
                 rent: int, lat: float, lon: float, services: str):
    """إضافة عقار جديد"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO properties (owner_id, city_id, area, title, description, rent, lat, lon, services)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (owner_id, city_id, area, title, description, rent, lat, lon, services),
        )
        property_id = cur.lastrowid
        conn.commit()
        conn.close()
        print(f"🏠 Property added: {title} (ID: {property_id})")
        return property_id
    except Exception as e:
        print(f"❌ Add property error: {e}")
        raise Exception(f"خطأ في إضافة العقار: {e}")

def get_properties_by_city(city_id: int):
    """الحصول على العقارات في مدينة معينة"""
    try:
        conn = get_connection()
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
        properties = []
        for r in cur.fetchall():
            properties.append(
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
        conn.close()
        print(f"🏠 Retrieved {len(properties)} properties for city ID: {city_id}")
        return properties
    except Exception as e:
        print(f"❌ Get properties by city error: {e}")
        return []

def get_properties_by_owner(owner_id: int):
    """الحصول على عقارات مالك معين"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.title, p.area, p.description, p.rent, p.lat, p.lon, p.services, p.city_id
            FROM properties p
            WHERE p.owner_id=?
            ORDER BY p.id DESC
            """,
            (owner_id,),
        )
        properties = []
        for r in cur.fetchall():
            properties.append(
                {
                    "id": r[0],
                    "title": r[1],
                    "area": r[2],
                    "description": r[3],
                    "rent": r[4],
                    "lat": r[5],
                    "lon": r[6],
                    "services": r[7],
                    "city_id": r[8],
                }
            )
        conn.close()
        print(f"🏠 Retrieved {len(properties)} properties for owner ID: {owner_id}")
        return properties
    except Exception as e:
        print(f"❌ Get properties by owner error: {e}")
        return []

def get_properties_by_city_and_area(city_id: int, area: str):
    """الحصول على العقارات في مدينة ومنطقة معينة"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.title, p.area, p.description, p.rent, p.lat, p.lon, p.services,
                   u.username as owner_username
            FROM properties p
            JOIN users u ON p.owner_id = u.id
            WHERE p.city_id=? AND p.area=?
            ORDER BY p.id DESC
            """,
            (city_id, area),
        )
        properties = []
        for r in cur.fetchall():
            properties.append(
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
        conn.close()
        print(f"🏠 Retrieved {len(properties)} properties for city {city_id}, area: {area}")
        return properties
    except Exception as e:
        print(f"❌ Get properties by city and area error: {e}")
        return []

def delete_property(property_id: int, owner_id: int):
    """حذف عقار (للمالك فقط)"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM properties WHERE id=? AND owner_id=?",
            (property_id, owner_id),
        )
        deleted = cur.rowcount > 0
        conn.commit()
        conn.close()
        
        if deleted:
            print(f"🗑️  Property deleted: ID {property_id}")
        else:
            print(f"❌ Property not found or access denied: ID {property_id}")
            
        return deleted
    except Exception as e:
        print(f"❌ Delete property error: {e}")
        return False

def update_property(property_id: int, owner_id: int, **updates):
    """تحديث بيانات عقار"""
    try:
        if not updates:
            return False
            
        conn = get_connection()
        cur = conn.cursor()
        
        # بناء استعلام التحديث ديناميكياً
        set_clause = ", ".join([f"{key}=?" for key in updates.keys()])
        values = list(updates.values())
        values.extend([property_id, owner_id])
        
        query = f"UPDATE properties SET {set_clause} WHERE id=? AND owner_id=?"
        
        cur.execute(query, values)
        updated = cur.rowcount > 0
        conn.commit()
        conn.close()
        
        if updated:
            print(f"✏️  Property updated: ID {property_id}")
        else:
            print(f"❌ Property update failed: ID {property_id}")
            
        return updated
    except Exception as e:
        print(f"❌ Update property error: {e}")
        return False

# اختبار الوظائف عند التشغيل المباشر
if __name__ == "__main__":
    print("🧪 Testing database module...")
    init_db()
    
    # اختبار الوظائف الأساسية
    cities = get_cities()
    print(f"🏙️  Cities: {[c['name'] for c in cities]}")
    
    # اختبار المستخدمين
    user = get_user_by_credentials("user1", "123456")
    if user:
        print(f"👤 Test user: {user['username']} - {user['role']}")
    
    print("✅ Database module test completed!")
