import unreal

unreal.log("=" * 80)
unreal.log("FINDING ALL REGISTERED MENUS IN MAIN MENU BAR")
unreal.log("=" * 80)

try:
    menus = unreal.ToolMenus.get()
    
    # Try to find main menu bar
    menu_names = [
        "LevelEditor.MainMenu",
        "LevelEditor.MainMenu.File",
        "LevelEditor.MainMenu.Edit", 
        "LevelEditor.MainMenu.Window",
        "LevelEditor.MainMenu.Tools",
        "LevelEditor.MainMenu.Build",
        "LevelEditor.MainMenu.Platforms",
        "MainFrame.MainMenu",
        "MainFrame.MainMenu.File",
        "MainFrame.MainMenu.Tools",
    ]
    
    unreal.log("\nChecking which menus exist:")
    for name in menu_names:
        exists = menus.is_menu_registered(name)
        unreal.log(f"  {'✓' if exists else '✗'} {name}")
    
    # Try to see what would be between Platforms and the end
    unreal.log("\nTrying to register test menu:")
    try:
        # This might be the way to create a new top-level menu
        result = menus.register_menu("LevelEditor.MainMenu.Exporter", unreal.ToolMenuOwner())
        unreal.log(f"  register_menu result: {result}")
    except Exception as e:
        unreal.log(f"  Error: {e}")
    
    # Check what was registered
    unreal.log("\nAfter attempting registration:")
    for name in ["LevelEditor.MainMenu.Exporter", "LevelEditor.MainMenu.File"]:
        exists = menus.is_menu_registered(name)
        unreal.log(f"  {'✓' if exists else '✗'} {name}")
    
except Exception as e:
    unreal.log(f"ERROR: {e}")
    import traceback
    unreal.log(traceback.format_exc())

unreal.log("=" * 80)
