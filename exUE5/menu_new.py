import os
import sys
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from exporter import export_current_sequence, load_config


def _run_export():
    """Export callback function"""
    config = load_config()
    output_dir = config.get("default_output_folder", "D:/Exports")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "exported_sequence.fbx")

    try:
        result = export_current_sequence(output_path, config)
        unreal.log(f"[exUE5] ✓ Export completed!")
        unreal.log(f"[exUE5] File: {output_path}")
    except Exception as exc:
        unreal.log(f"[exUE5] ✗ Export failed: {exc}")


def install_menu():
    """Install the Exporter menu on the main menu bar"""
    unreal.log("[exUE5] ========== INSTALL MENU START ==========")
    
    if not hasattr(unreal, "ToolMenus"):
        unreal.log("[exUE5] ERROR: ToolMenus not available")
        return

    try:
        unreal.log("[exUE5] 1. Getting ToolMenus singleton...")
        menus = unreal.ToolMenus.get()
        unreal.log(f"[exUE5]    ✓ Got ToolMenus")
        
        unreal.log("[exUE5] 2. Getting MainFrame.MainMenu...")
        main_menu = menus.extend_menu("MainFrame.MainMenu")
        
        if not main_menu:
            unreal.log("[exUE5] ERROR: Could not extend MainFrame.MainMenu")
            return
        
        unreal.log("[exUE5]    ✓ Got main menu bar")
        
        unreal.log("[exUE5] 3. Checking if Exporter submenu already exists...")
        try:
            if menus.is_menu_registered("MainFrame.MainMenu.Exporter"):
                unreal.log("[exUE5]    Removing old Exporter menu...")
                menus.remove_menu("MainFrame.MainMenu.Exporter")
        except:
            pass
        
        unreal.log("[exUE5] 4. Creating Exporter submenu...")
        exporter_submenu = main_menu.add_sub_menu(
            "Exporter",
            "Exporter",
            "Export tools",
            ""
        )
        
        if not exporter_submenu:
            unreal.log("[exUE5] ERROR: add_sub_menu returned None")
            return
        
        unreal.log("[exUE5]    ✓ Submenu created successfully")
        
        unreal.log("[exUE5] 5. Adding 'Export Sequence FBX' entry to submenu...")
        
        export_entry = unreal.ToolMenuEntry()
        export_entry.type = unreal.MultiBlockType.MENU_ENTRY
        export_entry.set_label("Export Sequence FBX")
        export_entry.set_tool_tip("Export current Level Sequence to FBX")
        
        export_entry.set_string_command(
            unreal.ToolMenuStringCommandType.PYTHON,
            "",
            "from exUE5.menu import _run_export; _run_export()"
        )
        
        unreal.log("[exUE5]    Entry object created")
        
        result = exporter_submenu.add_menu_entry("ExportFBX", export_entry)
        unreal.log(f"[exUE5]    add_menu_entry returned: {result}")
        unreal.log("[exUE5]    ✓ Entry added to submenu")
        
        unreal.log("[exUE5] 6. Refreshing menu widgets...")
        menus.refresh_all_widgets()
        unreal.log("[exUE5]    ✓ Widgets refreshed")
        
        unreal.log("[exUE5] ========== INSTALL MENU SUCCESS ==========")
        unreal.log("[exUE5] ✓ Menu installed - 'Exporter' should appear on menu bar!")
        
    except Exception as e:
        unreal.log(f"[exUE5] ========== INSTALL MENU FAILED ==========")
        unreal.log(f"[exUE5] ERROR: {e}")
        import traceback
        unreal.log(traceback.format_exc())


def uninstall_menu():
    """Uninstall the Exporter menu"""
    if not hasattr(unreal, "ToolMenus"):
        return
    try:
        menus = unreal.ToolMenus.get()
        if menus.is_menu_registered("MainFrame.MainMenu.Exporter"):
            menus.remove_menu("MainFrame.MainMenu.Exporter")
            unreal.log("[exUE5] Menu uninstalled")
    except Exception as e:
        unreal.log(f"[exUE5] Uninstall error: {e}")
