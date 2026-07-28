import unreal

unreal.log("=" * 80)
unreal.log("DEBUG: Looking for main menu bar structure")
unreal.log("=" * 80)

try:
    menus = unreal.ToolMenus.get()
    
    # Check main menu bar
    unreal.log("\n1. Check MainFrame.MainMenu:")
    if menus.is_menu_registered("MainFrame.MainMenu"):
        mm = menus.find_menu("MainFrame.MainMenu")
        unreal.log(f"   Found: {mm}")
        unreal.log(f"   Type: {mm.menu_type if mm else 'N/A'}")
    
    # Check what menus are part of main bar
    unreal.log("\n2. Looking for MainMenuBar:")
    menu_names = [
        "MainFrame.MainMenuBar",
        "LevelEditor.MainMenuBar", 
        "LevelEditor.MainMenu.Bar",
        "MainFrame.MainMenu",
    ]
    
    for name in menu_names:
        exists = menus.is_menu_registered(name)
        unreal.log(f"   {'✓' if exists else '✗'} {name}")
    
    # Try to see existing top-level menus
    unreal.log("\n3. Trying extend_menu on MainFrame.MainMenu:")
    try:
        mmm = menus.find_menu("MainFrame.MainMenu")
        if mmm:
            unreal.log(f"   Found MainFrame.MainMenu")
            # Try extend_menu
            result = menus.extend_menu("MainFrame.MainMenu")
            unreal.log(f"   extend_menu result: {result}")
    except Exception as e:
        unreal.log(f"   Error: {e}")
    
    # Look at Exporter menu directly
    unreal.log("\n4. Check if Exporter menu exists:")
    for name in ["LevelEditor.MainMenu.Exporter", "MainFrame.MainMenu.Exporter"]:
        if menus.is_menu_registered(name):
            unreal.log(f"   ✓ Found: {name}")
            exp_menu = menus.find_menu(name)
            unreal.log(f"     Type: {exp_menu.menu_type if exp_menu else 'N/A'}")
    
    # Try adding to MainFrame.MainMenu instead
    unreal.log("\n5. Trying add_sub_menu on MainFrame.MainMenu:")
    try:
        mf_menu = menus.find_menu("MainFrame.MainMenu")
        if mf_menu:
            test_menu = mf_menu.add_sub_menu("TestExporter", "Test Exporter", "", "")
            unreal.log(f"   Result: {test_menu}")
    except Exception as e:
        unreal.log(f"   Error: {e}")

except Exception as e:
    unreal.log(f"ERROR: {e}")
    import traceback
    unreal.log(traceback.format_exc())

unreal.log("=" * 80)
