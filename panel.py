import flet as ft
import subprocess
import json
import os
import sys
import requests
import database.database as db

BOT_PROCESS = None
BOT_PATH = "bot.py"
SETTINGS_PATH = "settings.json"
LOG_PATH = os.path.join("logs", "bot.log")
PANEL_BOT_CONTROL_ENABLED = os.getenv("PANEL_BOT_CONTROL_ENABLED", "1") == "1"

def start_bot(page):
    global BOT_PROCESS
    if not PANEL_BOT_CONTROL_ENABLED:
        page.snack_bar = ft.SnackBar(ft.Text("Управление процессом бота отключено в этой среде"))
        page.snack_bar.open = True
        page.update()
        return
    if BOT_PROCESS is None or BOT_PROCESS.poll() is not None:
        BOT_PROCESS = subprocess.Popen([sys.executable, BOT_PATH])
        page.snack_bar = ft.SnackBar(ft.Text("Бот запущен!"))
        page.snack_bar.open = True
        page.update()

def stop_bot(page):
    global BOT_PROCESS
    if not PANEL_BOT_CONTROL_ENABLED:
        page.snack_bar = ft.SnackBar(ft.Text("Управление процессом бота отключено в этой среде"))
        page.snack_bar.open = True
        page.update()
        return
    if BOT_PROCESS and BOT_PROCESS.poll() is None:
        BOT_PROCESS.terminate()
        BOT_PROCESS = None
        page.snack_bar = ft.SnackBar(ft.Text("Бот остановлен!"))
        page.snack_bar.open = True
        page.update()

def load_settings():
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(data):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def read_logs():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            return f.read()[-5000:]
    return "Лог-файл не найден."

def get_guild_password(guild_id):
    settings = load_settings()
    return settings.get("guilds", {}).get(guild_id, {}).get("PANEL_PASSWORD")

def get_admin_password():
    settings = load_settings()
    return settings.get("main", {}).get("ADMIN_PANEL_PASSWORD")

def main(page: ft.Page):
    page.title = "Панель управления Discord-ботом"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.DEEP_PURPLE_400,
            secondary=ft.Colors.PURPLE_700,
            background=ft.Colors.BLACK,
            surface=ft.Colors.BLUE_GREY_900,
            on_primary=ft.Colors.WHITE,
            on_secondary=ft.Colors.WHITE,
            on_background=ft.Colors.WHITE,
            on_surface=ft.Colors.WHITE,
        ),
        font_family="Montserrat"
    )
    page.scroll = ft.ScrollMode.AUTO

    settings = load_settings()
    main_settings = settings.get("main", {})
    guilds = settings.get("guilds", {})
    guild_ids = list(guilds.keys())
    selected_guild = guild_ids[0] if guild_ids else None

    # --- AUTH STATE ---
    auth_state = {"is_admin": False, "guild_id": None, "is_authed": False, "guilds_info": {}}

    def show_login():
        page.controls.clear()
        # Используем только settings.json
        guilds_map = {gid: guilds[gid] for gid in guild_ids}
        auth_state["guilds_info"] = guilds_map
        dropdown_options = []
        for gid in guild_ids:
            g = guilds_map.get(gid)
            if g:
                text = f"{g.get('name', gid)} ({gid})"
            else:
                text = gid
            dropdown_options.append(ft.dropdown.Option(gid, text=text))
        selected = selected_guild
        login_guild_dropdown = ft.Dropdown(
            label="Сервер (guild)",
            options=dropdown_options,
            value=selected,
            width=350
        )
        password_field = ft.TextField(label="Пароль", password=True, can_reveal_password=True, width=350)
        login_error = ft.Text("", color=ft.Colors.RED_300)
        def try_login(e):
            entered_pass = password_field.value
            selected = login_guild_dropdown.value
            if entered_pass == get_admin_password():
                auth_state["is_admin"] = True
                auth_state["is_authed"] = True
                auth_state["guild_id"] = None
                show_panel()
            elif selected and entered_pass == get_guild_password(selected):
                auth_state["is_admin"] = False
                auth_state["is_authed"] = True
                auth_state["guild_id"] = selected
                show_panel()
            else:
                login_error.value = "Неверный пароль или сервер!"
                page.update()
        login_btn = ft.ElevatedButton("Войти", icon=ft.Icons.LOGIN, on_click=try_login, style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_PURPLE_400, color=ft.Colors.WHITE))
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("Lapochka Bot Panel", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_100),
                    ft.Text("Авторизация", size=20, weight=ft.FontWeight.BOLD),
                    login_guild_dropdown,
                    password_field,
                    login_btn,
                    login_error
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                alignment=ft.alignment.center,
                padding=50,
                expand=True
            )
        )
        page.update()

    def show_panel():
        page.controls.clear()
        # --- Guild/server header ---
        header_controls = []
        def refresh_panel(e=None):
            show_panel()
        if auth_state["is_admin"]:
            header_controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=ft.Colors.DEEP_PURPLE_200, size=36),
                    ft.Text("Вы вошли как администратор", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_100),
                ], alignment=ft.MainAxisAlignment.CENTER)
            )
        else:
            gid = auth_state["guild_id"]
            ginfo = auth_state["guilds_info"].get(gid)
            if ginfo:
                row = [
                    ft.Icon(ft.Icons.GROUP, color=ft.Colors.DEEP_PURPLE_200, size=36),
                    ft.Text(ginfo.get("name", gid), size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_100),
                    ft.Text(f"ID: {gid}", size=14, color=ft.Colors.GREY_500)
                ]
                header_controls.append(ft.Row(row, alignment=ft.MainAxisAlignment.CENTER))
        if header_controls:
            # Добавляем кнопки 'Обновить' и 'Выйти' справа
            refresh_btn = ft.ElevatedButton(
                "Обновить",
                icon=ft.Icons.REFRESH,
                style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_PURPLE_400, color=ft.Colors.WHITE),
                on_click=refresh_panel
            )
            exit_btn = ft.ElevatedButton(
                "Выйти",
                icon=ft.Icons.LOGOUT,
                style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE),
                on_click=lambda e: show_login()
            )
            page.add(
                ft.Container(
                    ft.Row([
                        ft.Column(header_controls, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([refresh_btn, exit_btn], alignment=ft.MainAxisAlignment.END)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=20
                )
            )

        # --- Основные настройки (main) ---
        main_fields = []
        for key, value in main_settings.items():
            main_fields.append(
                ft.TextField(label=key, value=str(value), multiline=True if isinstance(value, str) and "\n" in value else False)
            )
        def save_main_settings(e):
            for i, key in enumerate(main_settings.keys()):
                main_settings[key] = main_fields[i].value
            settings["main"] = main_settings
            save_settings(settings)
            page.snack_bar = ft.SnackBar(ft.Text("Основные настройки сохранены!"), bgcolor=ft.Colors.DEEP_PURPLE_400)
            page.snack_bar.open = True
            page.update()
        main_tab = ft.Container(
            content=ft.Column([
                ft.Text("Основные настройки", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200),
                *main_fields,
                ft.ElevatedButton(
                    "Сохранить основные настройки",
                    icon=ft.Icons.SAVE,
                    on_click=save_main_settings,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_PURPLE_400, color=ft.Colors.WHITE)
                )
            ], spacing=20),
            padding=30,
        )

        # --- Guild selection ---
        guild_dropdown = ft.Dropdown(
            label="Выберите сервер (guild)",
            options=[ft.dropdown.Option(gid) for gid in guild_ids],
            value=selected_guild,
            width=350
        )
        def get_guild_settings(gid):
            return guilds.get(gid, {})

        # --- Управление ботом ---
        bot_status = ft.Text("Статус: Остановлен", color=ft.Colors.GREY_400, size=36, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        def update_bot_status():
            global BOT_PROCESS
            if BOT_PROCESS and BOT_PROCESS.poll() is None:
                bot_status.value = "\u25CF Запущен"
                bot_status.color = ft.Colors.GREEN_400
            else:
                bot_status.value = "\u25CF Остановлен"
                bot_status.color = ft.Colors.RED_400
        update_bot_status()

        if auth_state["is_admin"]:
            start_btn = ft.ElevatedButton(
                "Запустить бота",
                icon=ft.Icons.PLAY_ARROW,
                on_click=lambda e: [start_bot(page), update_bot_status(), page.update()],
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.DEEP_PURPLE_400,
                    color=ft.Colors.WHITE
                )
            )
            stop_btn = ft.ElevatedButton(
                "Остановить бота",
                icon=ft.Icons.STOP,
                on_click=lambda e: [stop_bot(page), update_bot_status(), page.update()],
                style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE)
            )
            bot_tab = ft.Container(
                content=ft.Column([
                    ft.Text("Управление ботом", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200),
                    bot_status,
                    ft.Row([start_btn, stop_btn], alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=30, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
            )
        else:
            bot_tab = ft.Container(
                content=ft.Column([
                    ft.Text("Статус бота", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200, text_align=ft.TextAlign.CENTER),
                    bot_status,
                ], spacing=30, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
            )

        # --- Настройки ---
        settings_fields = []
        def build_settings_fields(guild_settings, prefix=""):
            fields = []
            for key, value in guild_settings.items():
                field_key = f"{prefix}{key}" if prefix else key
                if isinstance(value, bool):
                    field = ft.Switch(label=key, value=value)
                    fields.append((field_key, field))
                elif isinstance(value, int) or value is None:
                    field = ft.TextField(label=key, value="" if value is None else str(value))
                    fields.append((field_key, field))
                elif isinstance(value, dict):
                    fields.append((key, ft.Text(f"{key}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_100)))
                    fields.extend(build_settings_fields(value, prefix=f"{field_key}."))
                else:
                    field = ft.TextField(label=key, value=str(value))
                    fields.append((field_key, field))
            return fields

        def update_settings_fields(e=None):
            nonlocal settings_fields
            guild_settings = get_guild_settings(guild_dropdown.value)
            settings_fields = build_settings_fields(guild_settings)
            settings_column.controls = [field for _, field in settings_fields]
            page.update()

        guild_dropdown.on_change = update_settings_fields
        settings_column = ft.Column([], spacing=10)
        update_settings_fields()

        def save_settings_click(e):
            # Собираем новые значения
            def set_nested(d, keys, value):
                for k in keys[:-1]:
                    d = d.setdefault(k, {})
                d[keys[-1]] = value
            new_guild_settings = get_guild_settings(guild_dropdown.value).copy()
            for field_key, field in settings_fields:
                if isinstance(field, ft.Switch):
                    v = field.value
                elif isinstance(field, ft.TextField):
                    try:
                        v = int(field.value)
                    except Exception:
                        v = field.value if field.value != "" else None
                else:
                    continue
                keys = field_key.split(".")
                set_nested(new_guild_settings, keys, v)
            # Обновляем настройки
            settings["guilds"][guild_dropdown.value] = new_guild_settings
            save_settings(settings)
            page.snack_bar = ft.SnackBar(ft.Text("Настройки сохранены!"))
            page.snack_bar.open = True
            settings_status_text.value = "Настройки сохранены!"
            page.update()

        settings_status_text = ft.Text("", color=ft.Colors.GREEN_400)
        save_btn = ft.FilledButton("Сохранить настройки", icon=ft.Icons.SAVE, on_click=save_settings_click, style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_PURPLE_400, color=ft.Colors.WHITE))
        guild_tab = ft.Container(
            content=ft.Column([
                ft.Text("Настройки серверов", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200),
                guild_dropdown,
                settings_column,
                save_btn,
                settings_status_text
            ], spacing=20),
            padding=30,
        )

        # --- Логи ---
        log_text = ft.Text(read_logs(), selectable=True, size=12, color=ft.Colors.GREY_200)
        def refresh_logs(e):
            log_text.value = read_logs()
            page.update()
        refresh_btn = ft.ElevatedButton("Обновить логи", icon=ft.Icons.REFRESH, on_click=refresh_logs, style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_PURPLE_400, color=ft.Colors.WHITE))
        logs_tab = ft.Container(
            content=ft.Column([
                ft.Text("Логи бота", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200),
                log_text,
                refresh_btn
            ], spacing=20),
            padding=30,
        )

        # --- Поздравления (Birthday Greetings) ---
        def get_users_for_guild_with_birthday(guild_id):
            with db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT u.user_id, u.username
                    FROM users u
                    INNER JOIN birthdays b ON u.guild_id = b.guild_id AND u.user_id = b.user_id
                    WHERE u.guild_id = ?
                """, (guild_id,))
                return c.fetchall()

        def add_birthday(guild_id, user_id, username, birthday):
            db.register_user(guild_id, user_id, username)
            db.set_birthday(guild_id, user_id, birthday)

        def remove_birthday(guild_id, user_id):
            with db.get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM birthdays WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
                c.execute("DELETE FROM birthday_greetings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
                conn.commit()

        def get_birthdays_for_guild(guild_id):
            with db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT u.user_id, u.username, b.birthday
                    FROM users u
                    INNER JOIN birthdays b ON u.guild_id = b.guild_id AND u.user_id = b.user_id
                    WHERE u.guild_id = ?
                """, (guild_id,))
                return c.fetchall()

        def build_greeting_tab():
            guild_id = auth_state["guild_id"]
            users = get_users_for_guild_with_birthday(guild_id)
            user_options = [ft.dropdown.Option(user_id, text=f"{username} ({user_id})") for user_id, username in users]
            selected_user = user_options[0].key if user_options else None

            user_dropdown = ft.Dropdown(
                label="Пользователь",
                options=user_options,
                value=selected_user,
                width=350
            )

            # Поля для поздравления
            title_field = ft.TextField(label="Заголовок", width=400)
            url_field = ft.TextField(label="URL", width=400)
            desc_field = ft.TextField(label="Описание", multiline=True, width=400)
            image_url_field = ft.TextField(label="URL изображения", width=400)
            footer_field = ft.TextField(label="Footer", width=400)
            status_text = ft.Text("")

            def load_greeting_fields(user_id):
                if not user_id:
                    title_field.value = ""
                    url_field.value = ""
                    desc_field.value = ""
                    image_url_field.value = ""
                    footer_field.value = ""
                    status_text.value = ""
                    page.update()
                    return
                greeting = db.get_greeting(guild_id, user_id)
                if greeting:
                    title_field.value = greeting.get("title", "")
                    url_field.value = greeting.get("url", "") or ""
                    desc_field.value = greeting.get("description", "")
                    image_url_field.value = greeting.get("image_url", "") or ""
                    footer_field.value = greeting.get("footer", "") or ""
                else:
                    title_field.value = ""
                    url_field.value = ""
                    desc_field.value = ""
                    image_url_field.value = ""
                    footer_field.value = ""
                status_text.value = ""
                page.update()

            def on_user_change(e):
                load_greeting_fields(user_dropdown.value)

            user_dropdown.on_change = on_user_change

            def save_greeting(e):
                user_id = user_dropdown.value
                if not user_id:
                    status_text.value = "Выберите пользователя!"
                    page.update()
                    return
                greeting = {
                    "title": title_field.value,
                    "url": url_field.value or None,
                    "description": desc_field.value,
                    "image_url": image_url_field.value or None,
                    "footer": footer_field.value or None,
                }
                db.set_greeting(guild_id, user_id, greeting)
                status_text.value = "Поздравление сохранено!"
                page.update()

            save_btn = ft.FilledButton("Сохранить поздравление", icon=ft.Icons.SAVE, on_click=save_greeting, style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_PURPLE_400, color=ft.Colors.WHITE))

            # При инициализации загружаем первое поздравление
            load_greeting_fields(user_dropdown.value)

            return ft.Container(
                content=ft.Column([
                    ft.Text("Редактирование поздравления пользователя", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200),
                    user_dropdown,
                    title_field,
                    url_field,
                    desc_field,
                    image_url_field,
                    footer_field,
                    save_btn,
                    status_text
                ], spacing=15, width=420),
                padding=30,
            )

        # --- Дни рождения (Birthdays) ---
        def build_birthdays_tab():
            guild_id = auth_state["guild_id"]
            birthday_list_column = ft.Column([])
            status_text = ft.Text("")

            def refresh_birthdays():
                birthday_list_column.controls.clear()
                bdays = get_birthdays_for_guild(guild_id)
                for user_id, username, birthday in bdays:
                    def make_remove_btn(uid, uname):
                        def on_remove_click(e):
                            remove_birthday(guild_id, uid)
                            status_text.value = f"День рождения {uname} ({uid}) удалён."
                            refresh_birthdays()
                            page.update()
                        return ft.IconButton(icon=ft.Icons.DELETE, tooltip="Удалить", on_click=on_remove_click)
                    remove_btn = make_remove_btn(user_id, username)
                    birthday_list_column.controls.append(
                        ft.Row([
                            ft.Text(f"{username} ({user_id}): {birthday}", size=14),
                            remove_btn
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                page.update()

            add_birthday_name_field = ft.TextField(label="Имя", width=140)
            add_birthday_id_field = ft.TextField(label="user_id", width=120)
            add_birthday_date_field = ft.TextField(label="Дата (DD.MM.YYYY)", width=180)
            def add_birthday_click(e):
                uname = add_birthday_name_field.value.strip()
                uid = add_birthday_id_field.value.strip()
                bday = add_birthday_date_field.value.strip()
                if not uid or not uname or not bday:
                    status_text.value = "Заполните все поля!"
                    page.update()
                    return
                add_birthday(guild_id, uid, uname, bday)
                add_birthday_id_field.value = ""
                add_birthday_name_field.value = ""
                add_birthday_date_field.value = ""
                status_text.value = f"День рождения {uname} ({uid}) добавлен."
                refresh_birthdays()
                page.update()
            add_btn = ft.FilledButton("Добавить", icon=ft.Icons.ADD, on_click=add_birthday_click, style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_PURPLE_400, color=ft.Colors.WHITE))
            refresh_birthdays()
            return ft.Container(
                content=ft.Column([
                    ft.Text("Дни рождения на сервере", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200),
                    birthday_list_column,
                    ft.Row([
                        add_birthday_name_field,
                        add_birthday_id_field,
                        add_birthday_date_field,
                        add_btn
                    ], alignment=ft.MainAxisAlignment.START),
                    status_text
                ], spacing=15),
                padding=30,
            )

        # --- Админы (Admins) ---
        def build_admins_tab():
            guild_id = auth_state["guild_id"]
            with db.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT user_id FROM admins WHERE guild_id = ?", (guild_id,))
                admin_rows = c.fetchall()
                c.execute("SELECT user_id, username FROM users WHERE guild_id = ?", (guild_id,))
                user_map = {str(uid): uname for uid, uname in c.fetchall()}

            admin_list_column = ft.Column([])
            status_text = ft.Text("")

            def refresh_admins():
                admin_list_column.controls.clear()
                def make_remove_btn(uid, uname):
                    def on_remove_click(e):
                        db.remove_admin(guild_id, str(uid))
                        status_text.value = f"Админ {uname} ({uid}) удалён."
                        update_admins_and_users()
                        page.update()
                    return ft.IconButton(
                        icon=ft.Icons.DELETE,
                        tooltip="Удалить",
                        on_click=on_remove_click
                    )
                def update_admins_and_users():
                    with db.get_connection() as conn:
                        c = conn.cursor()
                        c.execute("SELECT user_id FROM admins WHERE guild_id = ?", (guild_id,))
                        nonlocal admin_rows
                        admin_rows = c.fetchall()
                        c.execute("SELECT user_id, username FROM users WHERE guild_id = ?", (guild_id,))
                        nonlocal user_map
                        user_map = {str(uid2): uname2 for uid2, uname2 in c.fetchall()}
                    refresh_admins()
                for (user_id,) in admin_rows:
                    uname = user_map.get(str(user_id), str(user_id))
                    remove_btn = make_remove_btn(user_id, uname)
                    admin_list_column.controls.append(
                        ft.Row([
                            ft.Text(f"{uname} ({user_id})", size=16),
                            remove_btn
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                page.update()

            def add_admin_click(e):
                new_id = add_admin_id_field.value.strip()
                new_name = add_admin_name_field.value.strip()
                if not new_id or not new_name:
                    status_text.value = "Введите user_id и имя!"
                elif db.is_admin(guild_id, new_id):
                    status_text.value = "Пользователь уже админ."
                else:
                    db.add_admin(guild_id, new_id)
                    db.register_user(guild_id, new_id, new_name)
                    status_text.value = f"Админ {new_name} ({new_id}) добавлен."
                    add_admin_id_field.value = ""
                    add_admin_name_field.value = ""
                    # Обновить список
                    with db.get_connection() as conn:
                        c = conn.cursor()
                        c.execute("SELECT user_id FROM admins WHERE guild_id = ?", (guild_id,))
                        nonlocal admin_rows
                        admin_rows = c.fetchall()
                        c.execute("SELECT user_id, username FROM users WHERE guild_id = ?", (guild_id,))
                        nonlocal user_map
                        user_map = {str(uid): uname for uid, uname in c.fetchall()}
                    refresh_admins()
                page.update()

            add_admin_id_field = ft.TextField(label="user_id для добавления", width=180)
            add_admin_name_field = ft.TextField(label="Имя пользователя", width=180)
            add_btn = ft.FilledButton("Добавить админа", icon=ft.Icons.PERSON_ADD, on_click=add_admin_click, style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_PURPLE_400, color=ft.Colors.WHITE))

            refresh_admins()

            return ft.Container(
                content=ft.Column([
                    ft.Text("Администраторы сервера", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200),
                    admin_list_column,
                    ft.Row([add_admin_id_field, add_admin_name_field, add_btn]),
                    status_text
                ], spacing=15),
                padding=30,
            )
        # --- Сообщения (Scheduled Messages) ---
        def build_scheduled_messages_tab():
            guild_id = auth_state["guild_id"]
            msg_list_column = ft.Column([])
            status_text = ft.Text("")

            repeat_options = [
                ft.dropdown.Option("never", text="Один раз"),
                ft.dropdown.Option("day", text="Каждый день"),
                ft.dropdown.Option("week", text="Каждую неделю"),
                ft.dropdown.Option("month", text="Каждый месяц"),
                ft.dropdown.Option("year", text="Каждый год"),
            ]
            repeat_texts = {
                "never": "Один раз",
                "day": "Каждый день",
                "week": "Каждую неделю",
                "month": "Каждый месяц",
                "year": "Каждый год",
            }

            def refresh_msgs():
                msg_list_column.controls.clear()
                msgs = db.get_scheduled_messages_with_meta(guild_id)
                for msg_id, repeat, dt, channel_id, message, enabled, last_error, attempt_count, last_attempt_at in msgs:
                    def make_remove_btn(mid):
                        def on_remove_click(e):
                            db.remove_scheduled_message(guild_id, mid)
                            status_text.value = f"Сообщение {mid} удалено."
                            refresh_msgs()
                            page.update()
                        return ft.IconButton(icon=ft.Icons.DELETE, tooltip="Удалить", on_click=on_remove_click)
                    def make_enable_btn(mid, enabled):
                        def on_enable_click(e):
                            # Получаем текущее сообщение
                            for m in msgs:
                                if m[0] == mid:
                                    db.update_scheduled_message(guild_id, mid, m[1], m[2], m[3], m[4], enabled=0 if enabled else 1)
                                    break
                            refresh_msgs()
                            page.update()
                        return ft.IconButton(icon=ft.Icons.PAUSE if enabled else ft.Icons.PLAY_ARROW, tooltip="Вкл/Выкл", on_click=on_enable_click)

                    error_preview = last_error[:40] + "..." if last_error and len(last_error) > 40 else (last_error or "-")
                    msg_row = ft.Row([
                        ft.Text(f"ID: {msg_id}", size=12, color=ft.Colors.GREY_500),
                        ft.Text(f"Повтор: {repeat_texts.get(repeat, repeat)}", size=12),
                        ft.Text(f"Время: {dt}", size=12),
                        ft.Text(f"Канал: {channel_id}", size=12),
                        ft.Text(f"Текст: {message[:30]}{'...' if len(message)>30 else ''}", size=12),
                        ft.Text(f"Попыток: {attempt_count or 0}", size=12),
                        ft.Text(f"Последняя: {last_attempt_at or '-'}", size=12),
                        ft.Text(f"Ошибка: {error_preview}", size=12, color=ft.Colors.RED_300 if last_error else ft.Colors.GREY_500),
                        ft.Text("Вкл" if enabled else "Выкл", size=12, color=ft.Colors.GREEN_400 if enabled else ft.Colors.RED_400),
                        make_enable_btn(msg_id, enabled),
                        make_remove_btn(msg_id)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    msg_list_column.controls.append(msg_row)
                page.update()

            add_repeat_field = ft.Dropdown(label="Повторение", options=repeat_options, value="never", width=140)
            add_datetime_field = ft.TextField(label="Дата и время (DD.MM.YYYY HH:MM)", width=200)
            add_channel_field = ft.TextField(label="ID канала", width=120)
            add_message_field = ft.TextField(label="Сообщение", multiline=True, width=300)
            def add_msg_click(e):
                repeat = add_repeat_field.value
                dt = add_datetime_field.value.strip()
                channel_id = add_channel_field.value.strip()
                msg = add_message_field.value.strip()
                if not repeat or not dt or not channel_id or not msg:
                    status_text.value = "Заполните все поля!"
                    page.update()
                    return
                try:
                    # Проверка формата времени DD.MM.YYYY HH:MM
                    from datetime import datetime
                    dt_obj = datetime.strptime(dt, "%d.%m.%Y %H:%M")
                    dt_iso = dt_obj.strftime("%Y-%m-%d %H:%M:00")
                except Exception:
                    status_text.value = "Неверный формат даты/времени! Пример: 07.06.2025 18:00"
                    page.update()
                    return
                db.add_scheduled_message(guild_id, repeat, dt_iso, channel_id, msg, enabled=1)
                add_repeat_field.value = "never"
                add_datetime_field.value = ""
                add_channel_field.value = ""
                add_message_field.value = ""
                status_text.value = "Сообщение запланировано."
                refresh_msgs()
                page.update()
            add_btn = ft.FilledButton("Добавить", icon=ft.Icons.ADD, on_click=add_msg_click, style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_PURPLE_400, color=ft.Colors.WHITE))
            refresh_msgs()
            return ft.Container(
                content=ft.Column([
                    ft.Text("Запланированные сообщения", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200),
                    msg_list_column,
                    ft.Row([
                        add_repeat_field,
                        add_datetime_field,
                        add_channel_field,
                        add_message_field,
                        add_btn
                    ], alignment=ft.MainAxisAlignment.START),
                    status_text
                ], spacing=15),
                padding=30,
            )

        # --- Tabs ---
        tabs = []
        tabs.append(ft.Tab(text="Управление", icon=ft.Icons.ROCKET_LAUNCH, content=bot_tab))
        if auth_state["is_admin"]:
            tabs.append(ft.Tab(text="Основные настройки", icon=ft.Icons.SETTINGS, content=main_tab))
            tabs.append(ft.Tab(text="Настройки серверов", icon=ft.Icons.STORAGE, content=guild_tab))
            tabs.append(ft.Tab(text="Логи", icon=ft.Icons.LIST, content=logs_tab))
        else:
            tabs.append(ft.Tab(text="Настройки сервера", icon=ft.Icons.STORAGE, content=guild_tab))
            tabs.append(ft.Tab(text="Поздравления", icon=ft.Icons.CAKE, content=build_greeting_tab()))
            tabs.append(ft.Tab(text="Дни рождения", icon=ft.Icons.CALENDAR_MONTH, content=build_birthdays_tab()))
            tabs.append(ft.Tab(text="Сообщения", icon=ft.Icons.SCHEDULE, content=build_scheduled_messages_tab()))
            tabs.append(ft.Tab(text="Админы", icon=ft.Icons.ADMIN_PANEL_SETTINGS, content=build_admins_tab()))
        page.add(
            ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=tabs,
                expand=1,
            )
        )
        page.update()

    show_login()

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, port=8550, host="0.0.0.0")
