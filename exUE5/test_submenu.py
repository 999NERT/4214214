import unreal

unreal.log("=" * 80)
unreal.log("TESTING REGISTER_MENU WITH DIFFERENT PARAMETERS")
unreal.log("=" * 80)

try:
    menus = unreal.ToolMenus.get()
    
    # Get the main menu bar
    main_menu = menus.find_menu("LevelEditor.MainMenu")
    unreal.log(f"Found main menu: {main_menu}")
    
    if main_menu:
        unreal.log("\nTrying to add submenu to main menu:")
        
        # Try add_sub_menu
        try:
            # Create the new menu first with different approaches
            unreal.log("\nAttempt 1: Direct add_sub_menu")
            result = main_menu.add_sub_menu("Exporter", "Exporter", "", "")
            unreal.log(f"  Result: {result}")
        except Exception as e:
            unreal.log(f"  Error: {e}")
        
        # Try using register_menu with just name and type
        unreal.log("\nAttempt 2: register_menu with name and type")
        try:
            # Maybe register_menu expects (name, type, parent_name)?
            result = menus.register_menu("LevelEditor.MainMenu.Exporter", unreal.MultiBoxType.MENU_BAR)
            unreal.log(f"  Result: {result}")
        except Exception as e:
            unreal.log(f"  Error: {e}")
        
        # Check if add_sub_menu_object exists
        unreal.log("\nAttempt 3: Using direct properties/objects")
        try:
            # Create a menu entry for submenu
            entry = unreal.ToolMenuEntry(type_=unreal.MultiBlockType.SEPARATOR)
            unreal.log(f"  Created entry: {entry}")
        except Exception as e:
            unreal.log(f"  Error: {e}")
    
    # Check what methods exist for creation
    unreal.log("\n\nAll ToolMenus methods again:")
    methods = [m for m in dir(menus) if not m.startswith('_') and callable(getattr(menus, m))]
    for m in methods:
        if 'menu' in m.lower() or 'add' in m.lower() or 'register' in m.lower():
            unreal.log(f"  - {m}")
    
except Exception as e:
    unreal.log(f"ERROR: {e}")
    import traceback
    unreal.log(traceback.format_exc())

unreal.log("=" * 80)
