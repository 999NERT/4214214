import os
import sys
from pathlib import Path

try:
    import unreal
except ModuleNotFoundError:
    unreal = None

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent
for path in (str(ROOT), str(PARENT)):
    if path not in sys.path:
        sys.path.insert(0, path)


def _log(message):
    if unreal is not None:
        try:
            unreal.log(f"[exUE5] {message}")
        except Exception:
            print(f"[exUE5] {message}")

try:
    from exUE5.exporter import export_current_sequence, load_config, build_output_path
except ModuleNotFoundError:
    from exporter import export_current_sequence, load_config, build_output_path

try:
    from exUE5.cleanup_menu import MENU_NAMES_TO_CLEAN
except ModuleNotFoundError:
    from cleanup_menu import MENU_NAMES_TO_CLEAN


def build_exporter_submenu_params():
    """Return the correct parameters for adding the PLUGSY_Exporter submenu.

    `name` must be RELATIVE to the parent menu this is added to (e.g.
    'MainFrame.MainMenu') -- UE prefixes it with the parent's own full path
    automatically. Passing an already-full path here doubles the prefix.
    """
    return {
        "owner": "exUE5",
        "section_name": "PLUGSY_Exporter",
        "name": "PLUGSY_Exporter",
        "label": "PLUGSY Exporter",
        "tool_tip": "PLUGSY export tools",
    }


PLUGIN_VERSION = "v1.0"


def _try_remove_menu_member(menu_obj, name):
    if not menu_obj:
        return False

    method_names = [
        "remove_menu_entry",
        "remove_entry",
        "remove_sub_menu",
        "remove_submenu",
        "remove_menu",
        "remove_section",
        "remove_section_by_name",
        "remove_menu_section",
        "remove_menu_entry_by_name",
    ]

    for method_name in method_names:
        method = getattr(menu_obj, method_name, None)
        if callable(method):
            try:
                method(name)
                _log(f"Removed menu member '{name}' using {method_name}")
                return True
            except Exception as exc:
                _log(f"Could not remove menu member '{name}' with {method_name}: {exc}")
    return False


def _get_menu_entry_label(entry):
    if not entry:
        return None
    for getter in ('get_label', 'get_name', 'get_tool_tip', 'get_section_name'):
        if hasattr(entry, getter):
            try:
                value = getattr(entry, getter)()
                if value:
                    return str(value)
            except Exception:
                continue
    return getattr(entry, 'name', None) or getattr(entry, 'label', None)


def _clear_menu_entries(menu_obj):
    if not menu_obj:
        return

    def _clear_entries_from_menu(target_menu):
        if not target_menu:
            return

        entries = []
        if hasattr(target_menu, 'get_menu_entries'):
            try:
                entries = target_menu.get_menu_entries()
            except Exception as exc:
                _log(f"get_menu_entries failed on target_menu: {exc}")
        elif hasattr(target_menu, 'get_entries'):
            try:
                entries = target_menu.get_entries()
            except Exception as exc:
                _log(f"get_entries failed on target_menu: {exc}")

        for entry in entries:
            entry_name = None
            if hasattr(entry, 'get_name'):
                try:
                    entry_name = entry.get_name()
                except Exception:
                    entry_name = None
            if not entry_name:
                entry_name = getattr(entry, 'name', None)
            entry_label = _get_menu_entry_label(entry)
            if entry_name in ('ExportFBX',) or entry_label in ('Export Sequence FBX', 'ExportFBX'):
                remove_name = entry_name or entry_label
                _log(f"Removing duplicate entry '{remove_name}' (label={entry_label})")
                _try_remove_menu_member(target_menu, remove_name)
                _try_remove_menu_member(target_menu, 'ExportFBX')
                _try_remove_menu_member(target_menu, 'Export Sequence FBX')

    if hasattr(menu_obj, 'get_sections'):
        try:
            sections = menu_obj.get_sections()
        except Exception as exc:
            _log(f"get_sections failed on menu_obj: {exc}")
            sections = []
    elif hasattr(menu_obj, 'find_section'):
        sections = []
        try:
            for section_name in ('PLUGSY_Exporter', 'Exporter'):
                section = menu_obj.find_section(section_name)
                if section:
                    sections.append(section)
        except Exception as exc:
            _log(f"find_section failed on menu_obj: {exc}")
    else:
        sections = []

    for section in sections:
        if section:
            _clear_entries_from_menu(section)

    _clear_entries_from_menu(menu_obj)


def _clear_existing_exporter_menu(menus, main_menu):
    for name in MENU_NAMES_TO_CLEAN:
        try:
            if menus.is_menu_registered(name):
                _log(f"Removing old exporter registration: {name}")
                menus.remove_menu(name)
        except Exception as exc:
            _log(f"Failed to remove old exporter registration {name}: {exc}")
        try:
            if hasattr(menus, 'unregister_menu'):
                menus.unregister_menu(name)
                _log(f"Unregistered old exporter menu: {name}")
        except Exception as exc:
            _log(f"Failed to unregister old exporter menu {name}: {exc}")

    if main_menu:
        _try_remove_menu_member(main_menu, "PLUGSY_Exporter")
        _try_remove_menu_member(main_menu, "ExportFBX")
        _clear_menu_entries(main_menu)
        try:
            if hasattr(menus, 'refresh_all_widgets'):
                menus.refresh_all_widgets()
                _log("Refreshed widgets after clearing existing menu")
        except Exception as exc:
            _log(f"Failed to refresh widgets after clearing existing menu: {exc}")


def _show_export_dialog(config):
    """Show a Tkinter dialog to choose filename and destination folder."""
    try:
        import tkinter as tk
        from tkinter import filedialog, ttk
    except Exception as exc:
        if unreal is not None:
            unreal.log(f"[exUE5] Tkinter dialog unavailable: {exc}")
        return None

    root = tk.Tk()
    root.title("Export Sequence FBX")
    root.geometry("520x260")
    root.resizable(False, False)
    root.configure(bg="#2b2b2b")

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TButton", background="#2f7f3f", foreground="white", borderwidth=0)
    style.configure("TEntry", fieldbackground="#1e1e1e", foreground="white")
    style.configure("TLabel", background="#2b2b2b", foreground="white")
    style.configure("TMenubutton", background="#2f7f3f", foreground="white")

    default_filename = config.get("default_output_filename", "exported_sequence.fbx")
    default_folder = config.get("default_output_folder") or os.path.join(os.path.expanduser("~"), "Exports")

    filename_var = tk.StringVar(value=default_filename)
    folder_var = tk.StringVar(value=default_folder)
    result = {"filename": None, "folder": None}

    def choose_folder():
        folder = filedialog.askdirectory(initialdir=folder_var.get(), title="Wybierz folder zapisu")
        if folder:
            folder_var.set(folder)

    def confirm():
        result["filename"] = filename_var.get().strip() or default_filename
        result["folder"] = folder_var.get().strip() or default_folder
        root.quit()
        root.destroy()

    def cancel():
        result["filename"] = None
        result["folder"] = None
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", cancel)

    ttk.Label(root, text="Nazwa pliku:").grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))
    ttk.Entry(root, textvariable=filename_var, width=52, style="TEntry").grid(row=1, column=0, columnspan=2, padx=14, pady=(0, 10))

    ttk.Label(root, text="Folder docelowy:").grid(row=2, column=0, sticky="w", padx=14, pady=(0, 6))
    ttk.Entry(root, textvariable=folder_var, width=44, style="TEntry").grid(row=3, column=0, padx=14, pady=(0, 10), sticky="ew")
    ttk.Button(root, text="Browse", command=choose_folder).grid(row=3, column=1, padx=(6, 14), pady=(0, 10), sticky="w")

    ttk.Button(root, text="GO EXPORT", command=confirm, width=18).grid(row=4, column=0, padx=14, pady=(6, 14), sticky="w")
    ttk.Button(root, text="Cancel", command=cancel, width=14).grid(row=4, column=1, padx=(6, 14), pady=(6, 14), sticky="e")

    version_label = ttk.Label(root, text=f"{PLUGIN_VERSION} — zmienia liczba", foreground="#9f9f9f")
    version_label.grid(row=5, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 8))

    root.columnconfigure(0, weight=1)
    root.mainloop()

    if result["filename"] is None and result["folder"] is None:
        return None
    return result


def _show_export_progress(output_path, config):
    try:
        import threading
        import tkinter as tk
        from tkinter import ttk
    except Exception as exc:
        if unreal is not None:
            unreal.log(f"[exUE5] Tkinter progress dialog unavailable: {exc}")
        return

    unreal.log(f"[exUE5] _show_export_progress running in thread: {threading.current_thread().name}")
    status = {
        "done": False,
        "success": False,
        "message": "Starting export...",
    }

    root = tk.Tk()
    root.title("Export Sequence FBX")
    root.geometry("520x240")
    root.resizable(False, False)
    root.configure(bg="#2b2b2b")

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TButton", background="#2f7f3f", foreground="white", borderwidth=0)
    style.configure("TLabel", background="#2b2b2b", foreground="white")
    style.configure("Horizontal.TProgressbar", troughcolor="#3a3a3a", background="#2f7f3f", bordercolor="#2b2b2b", lightcolor="#5bbf5b", darkcolor="#267226")

    ttk.Label(root, text="Trwa eksport...").pack(padx=16, pady=(18, 8), anchor="w")
    progress = ttk.Progressbar(root, style="Horizontal.TProgressbar", mode="indeterminate", length=472)
    progress.pack(padx=16, pady=(0, 14))
    progress.start(10)

    status_label = ttk.Label(root, text=status["message"])
    status_label.pack(padx=16, pady=(0, 12), anchor="w")

    button_frame = ttk.Frame(root, style="TFrame")
    button_frame.pack(fill="x", padx=16, pady=(0, 14))

    ok_button = ttk.Button(button_frame, text="OK", state="disabled", command=root.destroy, width=16)
    ok_button.pack(side="right")

    def check_status():
        status_label.config(text=status["message"])
        if status["done"]:
            progress.stop()
            ok_button.config(state="normal")
            if status["success"]:
                status_label.config(text="Eksport zakończony pomyślnie.")
            else:
                status_label.config(text=status["message"])
        else:
            root.after(100, check_status)

    def run_export_worker():
        # Runs on a real background thread now (not inside Tkinter's event
        # loop), so the progress bar / UI thread stays responsive during a
        # long export. NOTE: this calls into the `unreal` Python API from a
        # non-main thread, and Epic does NOT officially guarantee
        # thread-safety for arbitrary Python API calls -- this is UNVERIFIED,
        # test it on a real export in your environment. If it causes
        # instability/crashes, the safe fallback is calling
        # export_current_sequence() synchronously on the main thread instead
        # (i.e. accept the UI freeze) rather than guessing at further
        # threading workarounds.
        try:
            unreal.log(f"[exUE5] run_export started in thread: {threading.current_thread().name}")
            export_current_sequence(output_path, config)
            status["success"] = True
            status["message"] = "Eksport zakończony pomyślnie."
        except Exception as exc:
            status["success"] = False
            status["message"] = f"Błąd eksportu: {exc}"
        finally:
            status["done"] = True

    worker = threading.Thread(target=run_export_worker, name="exUE5-export-worker", daemon=True)
    worker.start()

    root.after(100, check_status)
    root.mainloop()


def _run_export():
    """Export callback function"""
    if unreal is None:
        raise RuntimeError("unreal module not available")

    config = load_config()

    unreal.log("[exUE5] Menu callback _run_export() invoked")

    dialog_result = _show_export_dialog(config)
    if not dialog_result:
        unreal.log("[exUE5] Export cancelled by user")
        return

    filename = dialog_result.get("filename")
    folder = dialog_result.get("folder")
    output_path = build_output_path(config=config, filename=filename, folder=folder)
    unreal.log(f"[exUE5] Selected output path: {output_path}")

    try:
        _show_export_progress(output_path, config)
    except Exception as exc:
        unreal.log(f"[exUE5] ERROR Export failed: {exc}")


def install_menu():
    """Install the PLUGSY Exporter menu on the main menu bar.

    Menu registration is disabled by default to avoid collisions in UE.
    Set enable_menu_integration to true in config.json to re-enable it.
    """
    config = load_config()
    if not config.get("enable_menu_integration", False):
        if unreal is not None:
            unreal.log("[exUE5] Menu integration disabled in config.json; skipping menu registration")
        return

    if unreal is None:
        raise RuntimeError("unreal module not available")

    unreal.log("[exUE5] ========== INSTALL MENU START ==========")
    
    if not hasattr(unreal, "ToolMenus"):
        unreal.log("[exUE5] ERROR: ToolMenus not available")
        return

    try:
        unreal.log("[exUE5] 1. Getting ToolMenus singleton...")
        menus = unreal.ToolMenus.get()
        unreal.log("[exUE5]    OK Got ToolMenus")
        
        unreal.log("[exUE5] 2. Getting MainFrame.MainMenu...")
        main_menu = menus.extend_menu("MainFrame.MainMenu")
        
        if not main_menu:
            unreal.log("[exUE5] ERROR: Could not extend MainFrame.MainMenu")
            return
        
        unreal.log("[exUE5]    OK Got main menu bar")
        
        unreal.log("[exUE5] 3. Cleaning existing PLUGSY_Exporter registration before install...")
        uninstall_menu()
        _clear_existing_exporter_menu(menus, main_menu)
        
        unreal.log("[exUE5] 4. Creating PLUGSY_Exporter submenu...")
        # NOTE: `name` must be RELATIVE to the parent menu (`main_menu`,
        # i.e. 'MainFrame.MainMenu') -- UE automatically prefixes it with
        # the parent's own full path. Passing the already-full path here
        # produced a doubled registration:
        # 'MainFrame.MainMenu.MainFrame.MainMenu.PLUGSY_Exporter', which no
        # cleanup code elsewhere (which correctly checks for the
        # non-doubled name) could ever find or remove -- so every install
        # silently stacked a new duplicate submenu instead of replacing it.
        exporter_submenu = main_menu.add_sub_menu(
            owner="exUE5",
            section_name="PLUGSY_Exporter",
            name="PLUGSY_Exporter",
            label=f"PLUGSY Exporter {PLUGIN_VERSION}",
            tool_tip="PLUGSY export tools"
        )
        
        if not exporter_submenu:
            unreal.log("[exUE5] ERROR: add_sub_menu returned None")
            return
        
        menu_name = getattr(exporter_submenu, "menu_name", "N/A")
        unreal.log("[exUE5]    OK Submenu created successfully")
        unreal.log(f"[exUE5] Zarejestrowana nazwa menu: {menu_name}")
        if menu_name != "N/A" and str(menu_name) not in MENU_NAMES_TO_CLEAN:
            unreal.log(
                f"[exUE5]    WARNING: registered menu name '{menu_name}' is "
                f"not in MENU_NAMES_TO_CLEAN -- future cleanup/uninstall "
                f"calls won't find it. If you see this, the naming bug is "
                f"back; check the add_sub_menu() call above."
            )
        
        unreal.log("[exUE5] 5. Adding 'Export Sequence FBX' entry to submenu...")
        _clear_menu_entries(exporter_submenu)
        
        if _try_remove_menu_member(exporter_submenu, "ExportFBX"):
            unreal.log("[exUE5] Removed existing ExportFBX entry from submenu before re-adding")

        export_entry = unreal.ToolMenuEntry(name="ExportFBX", type=unreal.MultiBlockType.MENU_ENTRY)
        export_entry.set_label("Export Sequence FBX")
        export_entry.set_tool_tip("Export current Level Sequence to FBX")
        
        export_entry.set_string_command(
            unreal.ToolMenuStringCommandType.PYTHON,
            "",
            "from exUE5.menu import _run_export; _run_export()"
        )
        
        unreal.log("[exUE5]    Entry object created (name='ExportFBX')")
        
        # add_menu_entry(section_name, entry) -> always returns None; the
        # first argument is the SECTION the entry is placed into inside this
        # submenu, not an entry ID. The entry's own identity comes from
        # ToolMenuEntry(name=...) above, which is what cleanup/dedup code
        # elsewhere looks up by the name 'ExportFBX'.
        exporter_submenu.add_menu_entry("PLUGSY_Exporter", export_entry)
        unreal.log("[exUE5]    OK Entry added to submenu (section='PLUGSY_Exporter', entry name='ExportFBX')")
        
        unreal.log("[exUE5] 6. Refreshing menu widgets...")
        menus.refresh_all_widgets()
        unreal.log("[exUE5]    OK Widgets refreshed")
        
        unreal.log("[exUE5] ========== INSTALL MENU SUCCESS ==========")
        unreal.log("[exUE5] OK Menu installed - 'PLUGSY Exporter' should appear on menu bar!")
        
    except Exception as e:
        unreal.log(f"[exUE5] ========== INSTALL MENU FAILED ==========")
        unreal.log(f"[exUE5] ERROR: {e}")
        import traceback
        unreal.log(traceback.format_exc())


def uninstall_menu():
    """Uninstall the PLUGSY Exporter menu."""
    if unreal is None or not hasattr(unreal, "ToolMenus"):
        return

    try:
        menus = unreal.ToolMenus.get()
        removed = False
        for name in MENU_NAMES_TO_CLEAN:
            try:
                if menus.is_menu_registered(name):
                    menus.remove_menu(name)
                    unreal.log(f"[exUE5] Removed menu registration: {name}")
                    removed = True
            except Exception as exc:
                unreal.log(f"[exUE5] Could not remove menu {name}: {exc}")
        if removed:
            menus.refresh_all_widgets()
            unreal.log("[exUE5] Menu uninstalled")
        else:
            unreal.log("[exUE5] No PLUGSY_Exporter menu registered")
    except Exception as e:
        unreal.log(f"[exUE5] Uninstall error: {e}")
        import traceback
        unreal.log(traceback.format_exc())
