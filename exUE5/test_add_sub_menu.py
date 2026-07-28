import unreal

unreal.log("=" * 80)
unreal.log("DEBUG: Testing add_sub_menu parameters")
unreal.log("=" * 80)

try:
    menus = unreal.ToolMenus.get()
    main_menu_bar = menus.find_menu("MainFrame.MainMenu")
    
    if not main_menu_bar:
        unreal.log("ERROR: MainFrame.MainMenu not found")
    else:
        # Try different parameter combinations
        unreal.log("\nAttempt 1: add_sub_menu with 4 string params")
        try:
            test1 = main_menu_bar.add_sub_menu("Test1", "Test1", "", "")
            unreal.log(f"  Result: {test1}")
            unreal.log(f"  Name: {test1.menu_name if test1 else 'None'}")
        except Exception as e:
            unreal.log(f"  Error: {e}")
        
        unreal.log("\nAttempt 2: add_sub_menu with 2 params")
        try:
            test2 = main_menu_bar.add_sub_menu("Test2", "Test 2 Label")
            unreal.log(f"  Result: {test2}")
            unreal.log(f"  Name: {test2.menu_name if test2 else 'None'}")
        except Exception as e:
            unreal.log(f"  Error: {e}")
        
        unreal.log("\nAttempt 3: add_sub_menu with 1 param")
        try:
            test3 = main_menu_bar.add_sub_menu("Test3")
            unreal.log(f"  Result: {test3}")
            unreal.log(f"  Name: {test3.menu_name if test3 else 'None'}")
        except Exception as e:
            unreal.log(f"  Error: {e}")
        
        # Check what method signature add_sub_menu expects
        unreal.log("\n\nAll methods that might add menu:")
        methods = [m for m in dir(main_menu_bar) if 'add' in m.lower() or 'menu' in m.lower()]
        for m in methods:
            unreal.log(f"  - {m}")
        
        # Try extend_menu
        unreal.log("\nAttempt 4: Try extend_menu")
        try:
            # First register the menu
            owner = unreal.ToolMenuOwner()
            owner_str = str(owner)
            unreal.log(f"  ToolMenuOwner: {owner_str}")
        except Exception as e:
            unreal.log(f"  Error: {e}")

except Exception as e:
    unreal.log(f"ERROR: {e}")
    import traceback
    unreal.log(traceback.format_exc())

unreal.log("=" * 80)
