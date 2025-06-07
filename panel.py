import flet as ft
import subprocess
import json
import os
import sys
import requests

BOT_PROCESS = None
BOT_PATH = "bot.py"
SETTINGS_PATH = "settings.json"
LOG_PATH = os.path.join("logs", "bot.log")

def start_bot(page):
    global BOT_PROCESS
    if BOT_PROCESS is None or BOT_PROCESS.poll() is not None:
        BOT_PROCESS = subprocess.Popen([sys.executable, BOT_PATH])
        page.snack_bar = ft.SnackBar(ft.Text("Бот запущен!"))
        page.snack_bar.open = True
        page.update()

def stop_bot(page):
    global BOT_PROCESS
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
            # Добавляем кнопку 'Выйти' справа
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
                        exit_btn
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
        bot_status = ft.Text("Статус: Остановлен", color=ft.Colors.GREY_400)
        def update_bot_status():
            global BOT_PROCESS
            if BOT_PROCESS and BOT_PROCESS.poll() is None:
                bot_status.value = "Статус: Запущен"
                bot_status.color = ft.Colors.GREEN_400
            else:
                bot_status.value = "Статус: Остановлен"
                bot_status.color = ft.Colors.GREY_400

        def start_bot_ui(e):
            start_bot(page)
            update_bot_status()
            page.update()
        def stop_bot_ui(e):
            stop_bot(page)
            update_bot_status()
            page.update()

        start_btn = ft.ElevatedButton(
            "Запустить бота",
            icon=ft.Icons.PLAY_ARROW,
            on_click=start_bot_ui,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.DEEP_PURPLE_400,
                color=ft.Colors.WHITE  # Белый текст для читаемости
            )
        )
        stop_btn = ft.ElevatedButton(
            "Остановить бота",
            icon=ft.Icons.STOP,
            on_click=stop_bot_ui,
            style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE)
        )
        bot_tab = ft.Container(
            content=ft.Column([
                ft.Text("Управление ботом", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200),
                bot_status,
                ft.Row([start_btn, stop_btn], alignment=ft.MainAxisAlignment.START),
            ], spacing=20),
            padding=30,
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
            page.update()

        save_btn = ft.FilledButton("Сохранить настройки", icon=ft.Icons.SAVE, on_click=save_settings_click, style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_PURPLE_400, color=ft.Colors.WHITE))
        guild_tab = ft.Container(
            content=ft.Column([
                ft.Text("Настройки серверов", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200),
                guild_dropdown,
                settings_column,
                save_btn
            ], spacing=20),
            padding=30,
        )

        # --- Логи ---
        log_text = ft.Text(read_logs(), selectable=True, size=12, color=ft.Colors.GREY_200)
        def refresh_logs(e):
            log_text.value = read_logs()
            page.update()
        refresh_btn = ft.ElevatedButton("Обновить логи", icon=ft.Icons.REFRESH, on_click=refresh_logs, style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_PURPLE_400))
        logs_tab = ft.Container(
            content=ft.Column([
                ft.Text("Логи бота", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_PURPLE_200),
                log_text,
                refresh_btn
            ], spacing=20),
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
    ft.app(target=main, view=ft.WEB_BROWSER)
