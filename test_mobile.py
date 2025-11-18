import flet as ft
import sqlite3
import os

def main(page: ft.Page):
    # إعدادات بسيطة للموبايل
    page.title = "City Mover Test"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    # اختبار بسيط للوظائف
    def test_database(e):
        try:
            # اختبار إنشاء قاعدة بيانات بسيطة
            db_path = "test_city_app.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # إنشاء جدول بسيط
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_users (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            ''')
            
            # إضافة بيانات اختبار
            cursor.execute("INSERT INTO test_users (name) VALUES (?)", ("Test User",))
            conn.commit()
            
            # قراءة البيانات
            cursor.execute("SELECT * FROM test_users")
            users = cursor.fetchall()
            
            conn.close()
            
            result_text.value = f"✅ Database test passed! Users: {users}"
            
        except Exception as error:
            result_text.value = f"❌ Database error: {str(error)}"
        
        page.update()

    def test_ui(e):
        try:
            # اختبار عناصر واجهة المستخدم
            result_text.value = "✅ UI test passed! Buttons are working."
            page.update()
        except Exception as error:
            result_text.value = f"❌ UI error: {str(error)}"
            page.update()

    # واجهة اختبار بسيطة
    result_text = ft.Text("Click buttons to test...", size=16)
    
    page.add(
        ft.Column([
            ft.Text("📱 Mobile Compatibility Test", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.ElevatedButton("Test Database", on_click=test_database),
            ft.ElevatedButton("Test UI", on_click=test_ui),
            ft.Divider(),
            result_text
        ])
    )

# تشغيل التطبيق بصيغة آمنة
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)