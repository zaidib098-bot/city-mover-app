import flet as ft
import sqlite3
import os
from pathlib import Path

# استيراد مكتبة flet_map إذا كانت متوفرة
try:
    import flet_map as map
except ImportError:
    # إذا لم تكن متوفرة، استخدم بديل
    class MockMap:
        def __init__(self, *args, **kwargs):
            pass
            
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
            
    class MockMapLatitudeLongitude:
        def __init__(self, lat, lon):
            self.latitude = lat
            self.longitude = lon
            
    class MockMapTapEvent:
        def __init__(self):
            self.name = "tap"
            self.coordinates = MockMapLatitudeLongitude(0, 0)
            
    class MockTileLayer:
        def __init__(self, *args, **kwargs):
            pass
            
    class MockMarkerLayer:
        def __init__(self, *args, **kwargs):
            self.markers = []
            
    class MockMarker:
        def __init__(self, *args, **kwargs):
            pass
            
    class MapInteractiveFlag:
        ALL = "all"
        
    class MapInteractionConfiguration:
        def __init__(self, flags=None):
            self.flags = flags
            
    map = MockMap()
    map.Map = MockMap
    map.MapLatitudeLongitude = MockMapLatitudeLongitude
    map.MapTapEvent = MockMapTapEvent
    map.TileLayer = MockTileLayer
    map.MarkerLayer = MockMarkerLayer
    map.Marker = MockMarker
    map.MapInteractiveFlag = MapInteractiveFlag
    map.MapInteractionConfiguration = MapInteractionConfiguration

import db

def main(page: ft.Page):
    # إعدادات خاصة بالأندرويد
    page.title = "City Mover App - تطبيق الانتقال للمدن"
    page.window.width = 400  # عرض مناسب للجوال
    page.window.height = 800
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 5
    page.spacing = 5

    # تحسينات للأندرويد
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # ألوان التطبيق
    PRIMARY_COLOR = "#1E40AF"
    SECONDARY_COLOR = "#0EA5E9"
    ACCENT_COLOR = "#F59E0B"
    SUCCESS_COLOR = "#10B981"
    WARNING_COLOR = "#F59E0B"
    ERROR_COLOR = "#EF4444"
    BACKGROUND_COLOR = "#F8FAFC"
    SURFACE_COLOR = "#FFFFFF"
    TEXT_COLOR = "#1E293B"

    # تهيئة قاعدة البيانات
    db.init_db()

    # تخزين بيانات الجلسة
    if not page.session.contains_key("user"):
        page.session.set("user", None)

    # ---------- مناطق دمشق المفعلة ----------
    DAMASCUS_ACTIVE_AREAS = ["المزة", "كفرسوسة", "الميدان"]
    
    # ---------- جميع مناطق دمشق ----------
    DAMASCUS_ALL_AREAS = [
        "المزة", "كفرسوسة", "الميدان", "القدم", "القصاع", "المالكي", "أبو رمانة",
        "البرامكة", "ركن الدين", "الصالحية", "الشعلان", "المهاجرين", "العدوي",
        "القنوات", "باب توما", "باب شرقي", "ساروجة", "العفيف", "الجسر الأبيض",
        "الزاهرة", "الرحمانية", "دمر", "السبينة", "جوبر", "حرستا", "دوما",
        "داريا", "معضمية الشام", "صحنايا", "الكسوة", "التضامن", "الهامة",
        "قدسيا", "يملك", "القدم", "القابون", "برزة", "القطيفة", "الخضيري",
        "الزبداني", "بلد", "جرمانا", "سقبا", "معربا", "عربين", "حزة", "ببيلا"
    ]

    # ---------- عناصر مشتركة ----------

    def create_logo():
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LOCATION_CITY, color=PRIMARY_COLOR, size=28),
                ft.Column([
                    ft.Text("City Mover", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("تطبيق الانتقال للمدن", size=12, color="white"),
                ], spacing=0)
            ], spacing=8),
            padding=10,
        )

    def app_bar(title: str):
        user = page.session.get("user")
        right_controls = []
        if user:
            user_icon = ft.Icons.PERSON if user['role'] == 'user' else ft.Icons.BUSINESS_CENTER
            user_color = SECONDARY_COLOR if user['role'] == 'user' else ACCENT_COLOR
            
            right_controls = [
                ft.Container(
                    content=ft.Row([
                        ft.Icon(user_icon, color="white", size=20),
                        ft.Text(f"{user['username']}", color="white", size=14),
                        ft.Container(
                            content=ft.Text(
                                "مستخدم" if user['role'] == 'user' else "مالك",
                                size=12,
                                color="white"
                            ),
                            bgcolor=user_color,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=20,
                        )
                    ], spacing=8),
                    padding=8,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        icon_color="white",
                        on_click=logout,
                        tooltip="تسجيل الخروج",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                        )
                    ),
                    padding=8,
                ),
            ]

        return ft.AppBar(
            leading=create_logo(),
            title=ft.Text(title, weight=ft.FontWeight.BOLD, color="white", size=18),
            center_title=False,
            toolbar_height=70,
            bgcolor=PRIMARY_COLOR,
            actions=right_controls,
        )

    def logout(e=None):
        page.session.set("user", None)
        page.go("/login")

    def create_card(content, color=SURFACE_COLOR, elevation=2):
        return ft.Container(
            content=content,
            padding=15,
            margin=8,
            border_radius=12,
            bgcolor=color,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2),
            ),
        )

    def create_section_header(title: str, icon: str = None):
        content = [ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR)]
        if icon:
            content.insert(0, ft.Icon(icon, color=PRIMARY_COLOR, size=22))
        return ft.Container(
            content=ft.Row(content, spacing=8),
            padding=ft.padding.only(bottom=8),
        )

    def create_touch_button(text, icon=None, on_click=None, bgcolor=PRIMARY_COLOR, expand=False):
        return ft.Container(
            content=ft.ElevatedButton(
                text=text,
                icon=icon,
                on_click=on_click,
                style=ft.ButtonStyle(
                    color="white",
                    bgcolor=bgcolor,
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
            ),
            margin=4,
            width=160 if not expand else None,
        )

    # ---------- شاشة تسجيل الدخول / إنشاء حساب ----------

    def login_view():
        username = ft.TextField(
            label="اسم المستخدم",
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            text_size=16,
        )
        password = ft.TextField(
            label="كلمة المرور",
            expand=True,
            password=True,
            can_reveal_password=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            text_size=16,
        )

        mode_tabs = ft.Tabs(
            tabs=[
                ft.Tab(
                    text="تسجيل الدخول",
                    icon=ft.Icons.LOGIN,
                ),
                ft.Tab(
                    text="إنشاء حساب جديد",
                    icon=ft.Icons.PERSON_ADD,
                ),
            ],
            selected_index=0,
            expand=1,
            indicator_color=SECONDARY_COLOR,
            label_color=PRIMARY_COLOR,
            unselected_label_color=ft.Colors.GREY_600,
        )

        role_dropdown = ft.Dropdown(
            label="نوع الحساب",
            options=[
                ft.dropdown.Option("user", "مستخدم يبحث عن مدينة / سكن"),
                ft.dropdown.Option("owner", "مالك عقار / مضيف"),
            ],
            value="user",
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            text_size=16,
        )

        msg = ft.Text(color=ERROR_COLOR, size=14)

        def submit(e):
            nonlocal username, password
            if mode_tabs.selected_index == 0:
                # تسجيل الدخول
                user = db.get_user_by_credentials(username.value.strip(), password.value.strip())
                if not user:
                    msg.value = "بيانات الدخول غير صحيحة، حاول مرة أخرى."
                    msg.color = ERROR_COLOR
                    page.update()
                    return
                page.session.set("user", user)
                if user["role"] == "owner":
                    page.go("/owner")
                else:
                    page.go("/user")
            else:
                # إنشاء حساب جديد
                uname = username.value.strip()
                pwd = password.value.strip()
                role = role_dropdown.value
                if not uname or not pwd:
                    msg.value = "الرجاء إدخال اسم مستخدم وكلمة مرور."
                    msg.color = ERROR_COLOR
                    page.update()
                    return
                try:
                    user_id = db.create_user(uname, pwd, role)
                    new_user = {"id": user_id, "username": uname, "role": role}
                    page.session.set("user", new_user)
                    msg.value = "تم إنشاء الحساب بنجاح! تم تسجيل الدخول تلقائياً."
                    msg.color = SUCCESS_COLOR
                    page.update()
                    if role == "owner":
                        page.go("/owner")
                    else:
                        page.go("/user")
                except Exception as ex:
                    msg.value = f"خطأ في إنشاء الحساب: {ex}"
                    msg.color = ERROR_COLOR
                    page.update()

        submit_btn = create_touch_button(
            "متابعة", 
            ft.Icons.ARROW_FORWARD, 
            submit,
            bgcolor=PRIMARY_COLOR
        )

        content_col = ft.Column(
            [
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.LOCATION_CITY, size=40, color=PRIMARY_COLOR),
                            ft.Column([
                                ft.Text("مرحباً بك في", size=16, color=TEXT_COLOR),
                                ft.Text("City Mover", size=28, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                            ], spacing=0)
                        ], spacing=15),
                        ft.Text(
                            "هذا التطبيق يساعدك على الانتقال لمدينة جديدة والعثور على سكن وخدمات قريبة",
                            size=14,
                            color=ft.Colors.GREY_700,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                    margin=ft.margin.only(bottom=10),
                ),
                
                create_card(
                    ft.Column([
                        mode_tabs,
                        ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                        username,
                        password,
                        role_dropdown,
                        ft.Container(
                            content=submit_btn,
                            alignment=ft.alignment.center,
                            padding=15,
                        ),
                        msg,
                    ])
                ),
                
                ft.Container(
                    content=ft.Column([
                        ft.Text("حسابات تجريبية:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.PERSON, size=16, color=SECONDARY_COLOR),
                                    ft.Text("مستخدم: user1 / 123456", size=12),
                                ]),
                                ft.Row([
                                    ft.Icon(ft.Icons.BUSINESS_CENTER, size=16, color=ACCENT_COLOR),
                                    ft.Text("مالك: owner1 / 123456", size=12),
                                ]),
                            ], spacing=5),
                            bgcolor=BACKGROUND_COLOR,
                            padding=12,
                            border_radius=8,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=15,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.ADAPTIVE,
        )

        return ft.View(
            route="/login",
            controls=[
                app_bar("تسجيل الدخول / إنشاء حساب"),
                ft.Container(
                    content=content_col,
                    padding=15,
                    alignment=ft.alignment.top_center,
                    expand=True,
                    bgcolor=BACKGROUND_COLOR,
                ),
            ],
        )

    # ---------- شاشة المستخدم (User) ----------

    def user_view():
        user = page.session.get("user")
        if not user or user["role"] != "user":
            page.go("/login")
            return login_view()

        cities = db.get_cities()
        city_dropdown = ft.Dropdown(
            label="اختر المدينة التي ترغب بالانتقال إليها",
            expand=True,
            options=[ft.dropdown.Option(str(c["id"]), c["name"]) for c in cities],
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            text_size=16,
        )

        area_dropdown = ft.Dropdown(
            label="اختر المنطقة",
            expand=True,
            options=[],
            disabled=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            text_size=16,
        )

        selected_city_name = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR)
        selected_area_name = ft.Text("", size=14, color=TEXT_COLOR)
        
        properties_container = ft.Column(spacing=15)
        tips_container = ft.Column(spacing=10)

        # طبقة الماركر لخريطة الباحث عن منزل
        user_marker_layer_ref = ft.Ref[map.MarkerLayer]()

        user_map = map.Map(
            expand=True,
            height=300,
            initial_center=map.MapLatitudeLongitude(33.5138, 36.2765),  # دمشق
            initial_zoom=11,
            interaction_configuration=map.MapInteractionConfiguration(
                flags=map.MapInteractiveFlag.ALL
            ),
            layers=[
                map.TileLayer(
                    url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                ),
                map.MarkerLayer(ref=user_marker_layer_ref, markers=[]),
            ],
        )

        def get_all_areas_by_city(city_id: int):
            """جلب جميع المناطق المتاحة لمدينة معينة من قاعدة البيانات"""
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT area FROM properties 
                WHERE city_id = ? AND area IS NOT NULL AND area != ''
            """, (city_id,))
            areas = [row[0] for row in cur.fetchall()]
            conn.close()
            return areas

        def get_properties_by_city_and_area(city_id: int, area: str):
            """جلب العقارات بناءً على المدينة والمنطقة"""
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT p.id, p.title, p.area, p.description, p.rent, p.lat, p.lon, p.services,
                       u.username as owner_username
                FROM properties p
                JOIN users u ON p.owner_id = u.id
                WHERE p.city_id = ? AND p.area = ?
            """, (city_id, area))
            properties = []
            for row in cur.fetchall():
                properties.append({
                    "id": row[0],
                    "title": row[1],
                    "area": row[2],
                    "description": row[3],
                    "rent": row[4],
                    "lat": row[5],
                    "lon": row[6],
                    "services": row[7],
                    "owner_username": row[8]
                })
            conn.close()
            return properties

        def load_areas_for_city(city_id: int):
            """تحميل جميع المناطق المتاحة للمدينة المختارة"""
            area_dropdown.options.clear()
            area_dropdown.disabled = True
            
            city = db.get_city_by_id(city_id)
            if not city:
                return
                
            city_name = city["name"]
            
            if city_name == "دمشق":
                # لدمشق: نعرض جميع المناطق مع تمييز المناطق المفعلة
                for area in DAMASCUS_ALL_AREAS:
                    is_active = area in DAMASCUS_ACTIVE_AREAS
                    area_text = f"{area} {'✓' if is_active else ''}"
                    area_dropdown.options.append(ft.dropdown.Option(area, area_text))
                
                area_dropdown.disabled = False
                selected_area_name.value = f"المناطق المفعلة: {', '.join(DAMASCUS_ACTIVE_AREAS)}"
                selected_area_name.color = SUCCESS_COLOR
            else:
                # للمدن الأخرى: نعرض المناطق من قاعدة البيانات
                all_areas = get_all_areas_by_city(city_id)
                for area in all_areas:
                    area_dropdown.options.append(ft.dropdown.Option(area, area))
                area_dropdown.disabled = False
                selected_area_name.value = f"المناطق المتاحة: {len(all_areas)} منطقة"
                selected_area_name.color = TEXT_COLOR
            
            area_dropdown.value = None
            # تفريغ قائمة العقارات
            properties_container.controls.clear()
            page.update()

        def load_tips_for_city(city_name: str):
            tips_container.controls.clear()
            tips_container.controls.append(
                create_section_header("نصائح سريعة للانتقال", ft.Icons.LIGHTBULB)
            )
            base_tips = [
                "• احسب ميزانيتك الشهرية (السكن + المواصلات + الطعام).",
                "• تعرّف على المواصلات العامة في المدينة وخطوطها.",
                "• ابحث عن الخدمات الأساسية القريبة (سوبرماركت، مستشفى، مدرسة...).",
                "• حاول زيارة الحي في أوقات مختلفة من اليوم لمعرفة مدى الازدحام والهدوء.",
                "• تحقق من جودة الخدمات الأساسية (ماء، كهرباء، إنترنت).",
            ]
            for t in base_tips:
                tips_container.controls.append(
                    ft.Container(
                        content=ft.Text(t, size=14, color=ft.Colors.GREY_700),
                        padding=ft.padding.symmetric(vertical=5),
                    )
                )

        def contact_owner(owner_username: str, property_title: str):
            """فتح نافذة للتواصل مع المالك"""
            def send_message(e):
                if message_field.value.strip():
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"تم إرسال رسالتك إلى {owner_username}"),
                        bgcolor=SUCCESS_COLOR,
                        action="موافق",
                    )
                    page.snack_bar.open = True
                    page.update()
                    page.close(dlg)
                else:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("الرجاء كتابة رسالة"),
                        bgcolor=WARNING_COLOR,
                        action="موافق",
                    )
                    page.snack_bar.open = True
                    page.update()

            message_field = ft.TextField(
                label="رسالتك إلى المالك",
                multiline=True,
                min_lines=3,
                max_lines=6,
                expand=True,
                border_color=PRIMARY_COLOR,
                filled=True,
                text_size=16,
            )
            
            dlg = ft.AlertDialog(
                title=ft.Text(f"التواصل مع {owner_username}", color=PRIMARY_COLOR),
                content=ft.Column([
                    ft.Text(f"بخصوص: {property_title}", color=TEXT_COLOR),
                    message_field
                ], tight=True, height=200),
                actions=[
                    ft.TextButton(
                        "إرسال", 
                        on_click=send_message,
                        style=ft.ButtonStyle(color=SUCCESS_COLOR)
                    ),
                    ft.TextButton(
                        "إلغاء", 
                        on_click=lambda e: page.close(dlg),
                        style=ft.ButtonStyle(color=ERROR_COLOR)
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            
            page.open(dlg)

        def show_properties(e=None):
            properties_container.controls.clear()
            if user_marker_layer_ref.current:
                user_marker_layer_ref.current.markers.clear()

            if not city_dropdown.value:
                properties_container.controls.append(
                    ft.Container(
                        content=ft.Text("الرجاء اختيار مدينة أولاً.", color=ERROR_COLOR),
                        padding=10,
                        alignment=ft.alignment.center,
                    )
                )
                page.update()
                return

            city_id = int(city_dropdown.value)
            city = db.get_city_by_id(city_id)
            city_name = city["name"] if city else ""
            selected_city_name.value = f"المدينة: {city_name}"

            # إذا لم يتم اختيار منطقة، لا نعرض شيئاً
            if not area_dropdown.value:
                properties_container.controls.append(
                    ft.Container(
                        content=ft.Text("الرجاء اختيار منطقة لعرض المنازل المتاحة.", color=WARNING_COLOR),
                        padding=10,
                        alignment=ft.alignment.center,
                    )
                )
                page.update()
                return

            # التحقق إذا كانت المنطقة مفعلة لدمشق
            if city_name == "دمشق" and area_dropdown.value not in DAMASCUS_ACTIVE_AREAS:
                properties_container.controls.append(
                    ft.Container(
                        content=ft.Text("لا توجد منازل متاحة في هذه المنطقة حالياً.", color=ERROR_COLOR),
                        padding=10,
                        alignment=ft.alignment.center,
                    )
                )
                page.update()
                return

            # جلب العقارات للمنطقة المختارة
            props = get_properties_by_city_and_area(city_id, area_dropdown.value)

            if not props:
                properties_container.controls.append(
                    ft.Container(
                        content=ft.Text("لا يوجد منازل متاحة حالياً في المنطقة المختارة."),
                        padding=10,
                        alignment=ft.alignment.center,
                    )
                )
            else:
                for p in props:
                    def make_show_on_map(lat=p["lat"], lon=p["lon"], title=p["title"]):
                        def _inner(ev):
                            if lat is None or lon is None:
                                page.snack_bar = ft.SnackBar(
                                    ft.Text("لا توجد إحداثيات لهذا المنزل."),
                                    bgcolor=WARNING_COLOR,
                                    open=True,
                                )
                                page.update()
                                return

                            if user_marker_layer_ref.current:
                                user_marker_layer_ref.current.markers.clear()
                                user_marker_layer_ref.current.markers.append(
                                    map.Marker(
                                        content=ft.Icon(
                                            ft.Icons.HOME,
                                            color=ft.Colors.RED,
                                        ),
                                        coordinates=map.MapLatitudeLongitude(lat, lon),
                                    )
                                )
                            page.update()
                        return _inner

                    def make_contact_owner(username=p["owner_username"], title=p["title"]):
                        return lambda e: contact_owner(username, title)

                    card = create_card(
                        ft.Column(
                            [
                                ft.Row([
                                    ft.Icon(ft.Icons.HOME, color=PRIMARY_COLOR, size=24),
                                    ft.Text(p["title"], size=16, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR, expand=True),
                                ]),
                                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=16, color=SECONDARY_COLOR), 
                                                   ft.Text(f"المنطقة: {p['area'] or 'غير محدد'}", size=14)]),
                                            ft.Row([ft.Icon(ft.Icons.ATTACH_MONEY, size=16, color=SUCCESS_COLOR), 
                                                   ft.Text(f"الإيجار الشهري: {p['rent']} ل.س" if p["rent"] else "الإيجار غير محدد", size=14)]),
                                            ft.Row([ft.Icon(ft.Icons.PERSON, size=16, color=ACCENT_COLOR), 
                                                   ft.Text(f"المالك: {p['owner_username']}", size=14)]),
                                        ], spacing=8),
                                        expand=True,
                                    ),
                                ]),
                                ft.Divider(height=10, color=ft.Colors.GREY_300),
                                ft.Text(p["description"] or "", size=13, color=ft.Colors.GREY_700),
                                ft.Text(f"الخدمات القريبة: {p['services'] or 'غير مذكورة'}", size=12, color=ft.Colors.GREY_600),
                                ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                                ft.Row(
                                    [
                                        create_touch_button(
                                            "عرض على الخريطة",
                                            ft.Icons.MAP,
                                            on_click=make_show_on_map(),
                                            bgcolor=SECONDARY_COLOR
                                        ),
                                        create_touch_button(
                                            "خرائط جوجل",
                                            ft.Icons.OPEN_IN_NEW,
                                            on_click=lambda ev, lat=p["lat"], lon=p["lon"]: (
                                                page.launch_url(f"https://www.google.com/maps?q={lat},{lon}")
                                                if lat is not None and lon is not None
                                                else None
                                            ),
                                            bgcolor=PRIMARY_COLOR
                                        ),
                                        create_touch_button(
                                            "تواصل",
                                            ft.Icons.CONTACT_PHONE,
                                            on_click=make_contact_owner(),
                                            bgcolor=SUCCESS_COLOR
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    wrap=True,
                                ),
                            ]
                        )
                    )
                    properties_container.controls.append(card)

            load_tips_for_city(city_name)
            page.update()

        def on_city_change(e):
            if city_dropdown.value:
                load_areas_for_city(int(city_dropdown.value))
                show_properties()

        def on_area_change(e):
            show_properties()

        city_dropdown.on_change = on_city_change
        area_dropdown.on_change = on_area_change

        # تحميل نصائح أولية
        tips_container.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INFO, color=PRIMARY_COLOR, size=40),
                    ft.Text("اختر مدينة لعرض نصائح الانتقال المرتبطة بها.", size=14, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                alignment=ft.alignment.center,
            )
        )

        left_panel = ft.Container(
            content=ft.Column(
                [
                    create_section_header("البحث عن سكن", ft.Icons.SEARCH),
                    create_card(
                        ft.Column([
                            ft.Text("خطوة 1: اختر مدينة الانتقال", size=16, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                            city_dropdown,
                            ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                            ft.Text("خطوة 2: اختر المنطقة", size=16, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                            area_dropdown,
                            ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                            selected_city_name,
                            selected_area_name,
                        ])
                    ),
                    create_section_header("المنازل المتاحة", ft.Icons.HOME),
                    ft.Container(
                        content=ft.Column([properties_container], scroll=ft.ScrollMode.ADAPTIVE),
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            expand=1,
            padding=10,
        )

        right_panel = ft.Container(
            content=ft.Column(
                [
                    create_section_header("خريطة موقع المنزل", ft.Icons.MAP),
                    create_card(ft.Container(content=user_map, height=300)),
                    create_section_header("نصائح الانتقال", ft.Icons.LIGHTBULB),
                    create_card(
                        ft.Container(
                            content=ft.Column([tips_container], scroll=ft.ScrollMode.ADAPTIVE),
                            height=300,
                        )
                    ),
                ],
                expand=True,
            ),
            expand=1,
            padding=10,
        )

        # استخدام عمود واحد للجوال مع إمكانية التمرير
        layout = ft.Column(
            [
                create_section_header("البحث عن سكن", ft.Icons.SEARCH),
                create_card(
                    ft.Column([
                        ft.Text("اختر مدينة الانتقال", size=16, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                        city_dropdown,
                        ft.Divider(height=10),
                        ft.Text("اختر المنطقة", size=16, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                        area_dropdown,
                        selected_city_name,
                        selected_area_name,
                    ])
                ),
                
                create_section_header("خريطة موقع المنزل", ft.Icons.MAP),
                create_card(ft.Container(content=user_map, height=300)),
                
                create_section_header("المنازل المتاحة", ft.Icons.HOME),
                ft.Container(
                    content=ft.Column([properties_container], scroll=ft.ScrollMode.ADAPTIVE),
                    expand=True,
                ),
                
                create_section_header("نصائح الانتقال", ft.Icons.LIGHTBULB),
                create_card(
                    ft.Container(
                        content=ft.Column([tips_container], scroll=ft.ScrollMode.ADAPTIVE),
                        height=300,
                    )
                ),
            ],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True,
        )

        return ft.View(
            route="/user",
            appbar=app_bar("لوحة المستخدم - التخطيط للانتقال"),
            controls=[
                ft.Container(
                    content=layout,
                    expand=True,
                    bgcolor=BACKGROUND_COLOR,
                )
            ],
        )

    # ---------- شاشة المالك (Owner) ----------

    def owner_view():
        user = page.session.get("user")
        if not user or user["role"] != "owner":
            page.go("/login")
            return login_view()

        cities = db.get_cities()
        city_dropdown = ft.Dropdown(
            label="المدينة",
            expand=True,
            options=[ft.dropdown.Option(str(c["id"]), c["name"]) for c in cities],
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            text_size=16,
        )

        # Dropdown للمناطق - سيتم تعبئته بناءً على المدينة المختارة
        area_dropdown = ft.Dropdown(
            label="المنطقة",
            expand=True,
            options=[],
            disabled=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            text_size=16,
        )

        area_field = ft.TextField(
            label="أو اكتب اسم منطقة جديدة", 
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            text_size=16,
        )
        title_field = ft.TextField(
            label="عنوان الإعلان (مثال: شقة مفروشة بالقرب من المركز)",
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            text_size=16,
        )
        rent_field = ft.TextField(
            label="الإيجار الشهري (ل.س)", 
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            text_size=16,
        )
        desc_field = ft.TextField(
            label="وصف المنزل",
            multiline=True,
            min_lines=3,
            max_lines=5,
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            text_size=16,
        )
        services_field = ft.TextField(
            label="الخدمات القريبة (سوبرماركت، مواصلات، مدارس...)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            text_size=16,
        )
        lat_field = ft.TextField(
            label="خط العرض (Latitude)", 
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            text_size=16,
        )
        lon_field = ft.TextField(
            label="خط الطول (Longitude)", 
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            text_size=16,
        )

        msg = ft.Text(color=ERROR_COLOR, size=14)

        # خريطة تفاعلية لتحديد موقع المنزل بالضغط
        owner_marker_layer_ref = ft.Ref[map.MarkerLayer]()

        def handle_owner_map_tap(e: map.MapTapEvent):
            if e.name != "tap":
                return
            coords = e.coordinates
            lat = coords.latitude
            lon = coords.longitude
            lat_field.value = f"{lat:.6f}"
            lon_field.value = f"{lon:.6f}"

            if owner_marker_layer_ref.current:
                owner_marker_layer_ref.current.markers.clear()
                owner_marker_layer_ref.current.markers.append(
                    map.Marker(
                        content=ft.Icon(ft.Icons.LOCATION_ON, color=ERROR_COLOR),
                        coordinates=coords,
                    )
                )
            msg.value = "تم اختيار موقع العقار على الخريطة."
            msg.color = SUCCESS_COLOR
            page.update()

        owner_map = map.Map(
            expand=True,
            height=300,
            initial_center=map.MapLatitudeLongitude(33.5138, 36.2765),
            initial_zoom=11,
            interaction_configuration=map.MapInteractionConfiguration(
                flags=map.MapInteractiveFlag.ALL
            ),
            on_tap=handle_owner_map_tap,
            layers=[
                map.TileLayer(
                    url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                ),
                map.MarkerLayer(ref=owner_marker_layer_ref, markers=[]),
            ],
        )

        def get_all_areas_by_city_owner(city_id: int):
            """جلب جميع المناطق المتاحة لمدينة معينة للمالك"""
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT area FROM properties 
                WHERE city_id = ? AND area IS NOT NULL AND area != ''
            """, (city_id,))
            areas = [row[0] for row in cur.fetchall()]
            conn.close()
            return areas

        def load_areas_for_owner_city(city_id: int):
            """تحميل جميع المناطق المتاحة للمدينة المختارة في واجهة المالك"""
            area_dropdown.options.clear()
            area_dropdown.disabled = True
            
            city = db.get_city_by_id(city_id)
            if not city:
                return
                
            city_name = city["name"]
            
            if city_name == "دمشق":
                # لدمشق: نعرض جميع المناطق مع تمييز المناطق المفعلة
                for area in DAMASCUS_ALL_AREAS:
                    is_active = area in DAMASCUS_ACTIVE_AREAS
                    area_text = f"{area} {'✓' if is_active else ''}"
                    area_dropdown.options.append(ft.dropdown.Option(area, area_text))
                
                area_dropdown.disabled = False
                msg.value = f"المناطق المفعلة لدمشق: {', '.join(DAMASCUS_ACTIVE_AREAS)}"
                msg.color = SUCCESS_COLOR
            else:
                # للمدن الأخرى: نعرض المناطق من قاعدة البيانات
                all_areas = get_all_areas_by_city_owner(city_id)
                for area in all_areas:
                    area_dropdown.options.append(ft.dropdown.Option(area, area))
                area_dropdown.disabled = False
                msg.value = f"تم تحميل {len(all_areas)} منطقة للمدينة"
                msg.color = TEXT_COLOR
            
            area_dropdown.value = None
            page.update()

        def on_city_change_owner(e):
            if city_dropdown.value:
                load_areas_for_owner_city(int(city_dropdown.value))

        city_dropdown.on_change = on_city_change_owner

        def open_google_maps(e=None):
            try:
                lat = float(lat_field.value)
                lon = float(lon_field.value)
                page.launch_url(f"https://www.google.com/maps?q={lat},{lon}")
                return
            except Exception:
                pass

            if city_dropdown.value:
                city = db.get_city_by_id(int(city_dropdown.value))
                if city:
                    q = city["name"]
                    page.launch_url(f"https://www.google.com/maps/search/?api=1&query={q}")
                    return

            page.launch_url("https://www.google.com/maps")

        def save_property(e):
            if not city_dropdown.value:
                msg.value = "الرجاء اختيار مدينة."
                msg.color = ERROR_COLOR
                page.update()
                return

            # تحديد المنطقة المختارة
            selected_area = None
            if area_dropdown.value:
                selected_area = area_dropdown.value
            elif area_field.value.strip():
                selected_area = area_field.value.strip()
            
            if not selected_area:
                msg.value = "الرجاء اختيار منطقة أو كتابة اسم منطقة جديدة."
                msg.color = ERROR_COLOR
                page.update()
                return

            city_id = int(city_dropdown.value)
            city = db.get_city_by_id(city_id)
            city_name = city["name"] if city else ""

            # التحقق من صحة المنطقة لمدينة دمشق
            if city_name == "دمشق" and selected_area not in DAMASCUS_ACTIVE_AREAS:
                msg.value = f"لدمشق: يمكنك فقط إضافة عقارات في المناطق التالية: {', '.join(DAMASCUS_ACTIVE_AREAS)}"
                msg.color = ERROR_COLOR
                page.update()
                return

            try:
                rent = int(rent_field.value) if rent_field.value else None
            except ValueError:
                msg.value = "الإيجار يجب أن يكون رقماً."
                msg.color = ERROR_COLOR
                page.update()
                return
            try:
                lat = float(lat_field.value) if lat_field.value else None
                lon = float(lon_field.value) if lon_field.value else None
            except ValueError:
                msg.value = "إحداثيات غير صحيحة."
                msg.color = ERROR_COLOR
                page.update()
                return

            try:
                db.add_property(
                    owner_id=user["id"],
                    city_id=city_id,
                    area=selected_area,
                    title=title_field.value.strip(),
                    description=desc_field.value.strip(),
                    rent=rent,
                    lat=lat,
                    lon=lon,
                    services=services_field.value.strip(),
                )
                msg.value = "تم حفظ العقار بنجاح ✅"
                msg.color = SUCCESS_COLOR

                # تفريغ الحقول
                area_field.value = ""
                title_field.value = ""
                rent_field.value = ""
                desc_field.value = ""
                services_field.value = ""
                lat_field.value = ""
                lon_field.value = ""
                if owner_marker_layer_ref.current:
                    owner_marker_layer_ref.current.markers.clear()
                page.update()
                load_owner_properties()
            except Exception as ex:
                msg.value = f"حدث خطأ أثناء الحفظ: {ex}"
                msg.color = ERROR_COLOR
                page.update()

        def edit_property(property_id: int):
            """فتح نافذة لتعديل بيانات العقار"""
            # جلب بيانات العقار الحالية
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT title, area, description, rent, lat, lon, services, city_id 
                FROM properties WHERE id = ?
            """, (property_id,))
            prop = cur.fetchone()
            conn.close()
            
            if not prop:
                return
            
            # إنشاء حقول التعديل
            edit_title = ft.TextField(label="العنوان", value=prop[0], expand=True, border_color=PRIMARY_COLOR, filled=True)
            edit_area = ft.TextField(label="المنطقة", value=prop[1], expand=True, border_color=PRIMARY_COLOR, filled=True)
            edit_desc = ft.TextField(label="الوصف", value=prop[2], multiline=True, min_lines=3, expand=True, border_color=PRIMARY_COLOR, filled=True)
            edit_rent = ft.TextField(label="الإيجار", value=str(prop[3]) if prop[3] else "", expand=True, border_color=PRIMARY_COLOR, filled=True)
            edit_lat = ft.TextField(label="خط العرض", value=str(prop[4]) if prop[4] else "", expand=True, border_color=PRIMARY_COLOR, filled=True)
            edit_lon = ft.TextField(label="خط الطول", value=str(prop[5]) if prop[5] else "", expand=True, border_color=PRIMARY_COLOR, filled=True)
            edit_services = ft.TextField(label="الخدمات", value=prop[6] or "", multiline=True, min_lines=2, expand=True, border_color=PRIMARY_COLOR, filled=True)
            
            def update_property(e):
                try:
                    rent_val = int(edit_rent.value) if edit_rent.value.strip() else None
                    lat_val = float(edit_lat.value) if edit_lat.value.strip() else None
                    lon_val = float(edit_lon.value) if edit_lon.value.strip() else None
                    
                    conn = db.get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE properties 
                        SET title=?, area=?, description=?, rent=?, lat=?, lon=?, services=?
                        WHERE id=?
                    """, (
                        edit_title.value.strip(),
                        edit_area.value.strip(),
                        edit_desc.value.strip(),
                        rent_val,
                        lat_val,
                        lon_val,
                        edit_services.value.strip(),
                        property_id
                    ))
                    conn.commit()
                    conn.close()
                    
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("تم تحديث بيانات العقار بنجاح"),
                        bgcolor=SUCCESS_COLOR,
                        action="موافق",
                    )
                    page.snack_bar.open = True
                    page.update()
                    page.close(dlg)
                    load_owner_properties()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"خطأ في التحديث: {ex}"),
                        bgcolor=ERROR_COLOR,
                        action="موافق",
                    )
                    page.snack_bar.open = True
                    page.update()
            
            dlg = ft.AlertDialog(
                title=ft.Text("تعديل بيانات العقار", color=PRIMARY_COLOR),
                content=ft.Column([
                    edit_title,
                    edit_area,
                    edit_desc,
                    ft.Row([edit_rent, edit_lat, edit_lon]),
                    edit_services
                ], scroll=ft.ScrollMode.ADAPTIVE, height=400),
                actions=[
                    ft.TextButton("حفظ التعديلات", on_click=update_property, style=ft.ButtonStyle(color=SUCCESS_COLOR)),
                    ft.TextButton("إلغاء", on_click=lambda e: page.close(dlg), style=ft.ButtonStyle(color=ERROR_COLOR)),
                ],
            )
            
            page.open(dlg)

        add_btn = create_touch_button(
            "حفظ العقار", 
            ft.Icons.SAVE, 
            on_click=save_property,
            bgcolor=SUCCESS_COLOR
        )
        
        open_maps_btn = create_touch_button(
            "فتح خرائط جوجل",
            ft.Icons.OPEN_IN_NEW,
            on_click=open_google_maps,
            bgcolor=PRIMARY_COLOR
        )

        properties_list_column = ft.Column(spacing=15)

        def load_owner_properties():
            properties_list_column.controls.clear()
            props = db.get_properties_by_owner(user["id"])
            if not props:
                properties_list_column.controls.append(
                    create_card(
                        ft.Column([
                            ft.Icon(ft.Icons.HOME, size=40, color=ft.Colors.GREY_400),
                            ft.Text("لم تقم بإضافة أي عقار بعد.", size=16, color=ft.Colors.GREY_600),
                            ft.Text("استخدم النموذج أدناه لإضافة عقارك الأول", size=14, color=ft.Colors.GREY_500),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        color=BACKGROUND_COLOR,
                    )
                )
            else:
                for p in props:
                    # الحصول على اسم المدينة للتحقق من المنطقة المفعلة
                    city = db.get_city_by_id(p.get("city_id", 0))
                    city_name = city["name"] if city else ""
                    is_active_area = city_name == "دمشق" and p["area"] in DAMASCUS_ACTIVE_AREAS
                    
                    def make_edit_function(prop_id=p["id"]):
                        return lambda e: edit_property(prop_id)
                    
                    properties_list_column.controls.append(
                        create_card(
                            ft.Column(
                                [
                                    ft.Row([
                                        ft.Icon(ft.Icons.APARTMENT, color=PRIMARY_COLOR, size=24),
                                        ft.Text(p["title"], size=16, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR, expand=True),
                                        ft.Container(
                                            content=ft.Row([
                                                ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color="white"),
                                                ft.Text("مفعل", size=12, color="white"),
                                            ]),
                                            bgcolor=SUCCESS_COLOR,
                                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                            border_radius=20,
                                            visible=is_active_area
                                        ) if is_active_area else ft.Container()
                                    ]),
                                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                                    ft.Row([
                                        ft.Container(
                                            content=ft.Column([
                                                ft.Row([ft.Icon(ft.Icons.LOCATION_CITY, size=16, color=SECONDARY_COLOR), 
                                                       ft.Text(f"المدينة: {city_name}", size=14)]),
                                                ft.Row([ft.Icon(ft.Icons.MAP, size=16, color=ACCENT_COLOR), 
                                                       ft.Text(f"المنطقة: {p['area'] or 'غير محدد'}", size=14)]),
                                                ft.Row([ft.Icon(ft.Icons.ATTACH_MONEY, size=16, color=SUCCESS_COLOR), 
                                                       ft.Text(f"الإيجار: {p['rent']} ل.س" if p["rent"] else "الإيجار غير محدد", size=14)]),
                                            ], spacing=8),
                                            expand=True,
                                        ),
                                    ]),
                                    ft.Divider(height=10, color=ft.Colors.GREY_300),
                                    ft.Text(p["description"] or "", size=13, color=ft.Colors.GREY_700),
                                    ft.Text(f"الخدمات القريبة: {p['services'] or 'غير مذكورة'}", size=12, color=ft.Colors.GREY_600),
                                    ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                                    ft.Row([
                                        create_touch_button(
                                            "تعديل البيانات",
                                            ft.Icons.EDIT,
                                            on_click=make_edit_function(),
                                            bgcolor=PRIMARY_COLOR
                                        )
                                    ], alignment=ft.MainAxisAlignment.CENTER),
                                ]
                            )
                        )
                    )

        load_owner_properties()

        # واجهة المالك كعمود واحد للجوال
        layout = ft.Column(
            [
                create_section_header("إضافة عقار جديد", ft.Icons.ADD_BUSINESS),
                create_card(
                    ft.Column([
                        city_dropdown,
                        area_dropdown,
                        area_field,
                        ft.Container(
                            content=ft.Text(
                                "ملاحظة: لمدينة دمشق، يمكنك فقط إضافة عقارات في المناطق المفعلة (المزة، كفرسوسة، الميدان)", 
                                size=12, 
                                color=WARNING_COLOR
                            ),
                            bgcolor=ft.Colors.ORANGE_50,
                            padding=10,
                            border_radius=8,
                        ),
                    ])
                ),
                create_card(
                    ft.Column([
                        title_field,
                        rent_field,
                        desc_field,
                        services_field,
                    ])
                ),
                create_card(
                    ft.Column([
                        ft.Row([lat_field, lon_field]),
                        ft.Text(
                            "اضغط على الخريطة لتحديد موقع المنزل، أو استخدم خرائط جوجل للمساعدة.",
                            size=12,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Container(content=owner_map, height=300),
                        ft.Row([open_maps_btn], alignment=ft.MainAxisAlignment.CENTER),
                    ])
                ),
                ft.Container(
                    content=ft.Row([add_btn], alignment=ft.MainAxisAlignment.CENTER),
                    padding=20,
                ),
                ft.Container(
                    content=msg,
                    alignment=ft.alignment.center,
                ),
                
                create_section_header("عقاراتي", ft.Icons.REAL_ESTATE_AGENT),
                ft.Container(
                    content=ft.Column([properties_list_column], scroll=ft.ScrollMode.ADAPTIVE),
                    expand=True,
                ),
            ],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True,
        )

        return ft.View(
            route="/owner",
            appbar=app_bar("لوحة المالك - إدارة العقارات"),
            controls=[
                ft.Container(
                    content=layout,
                    expand=True,
                    bgcolor=BACKGROUND_COLOR,
                )
            ],
        )

    # ---------- إدارة الـ Routes ----------

    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()
        if page.route == "/login":
            page.views.append(login_view())
        elif page.route == "/user":
            page.views.append(user_view())
        elif page.route == "/owner":
            page.views.append(owner_view())
        else:
            page.go("/login")
            page.views.append(login_view())
        page.update()

    def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # بدء التطبيق من شاشة الدخول
    page.go("/login")


if __name__ == "__main__":
    # تشغيل التطبيق على الأندرويد مع الحفاظ على جميع الميزات
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
        assets_dir="assets"
)
