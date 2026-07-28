import unreal

unreal.log("=" * 80)
unreal.log("UNREAL PYTHON API DEBUG - ToolMenus & ToolMenu")
unreal.log("=" * 80)

try:
    # Get ToolMenus
    tool_menus = unreal.ToolMenus.get()
    unreal.log(f"\n1. ToolMenus.get() returned: {type(tool_menus)}")
    
    # Find Tools menu
    menu = tool_menus.find_menu("LevelEditor.MainMenu.Tools")
    unreal.log(f"2. find_menu('LevelEditor.MainMenu.Tools') returned: {type(menu)}")
    
    if menu:
        unreal.log("\n3. AVAILABLE METHODS ON ToolMenu OBJECT:")
        unreal.log("-" * 80)
        
        # Get all attributes/methods
        attrs = dir(menu)
        methods = [a for a in attrs if not a.startswith('_')]
        
        for i, method in enumerate(methods, 1):
            unreal.log(f"   {i:2d}. {method}")
        
        # Try to get more details about important methods
        unreal.log("\n4. DETAILED METHOD INFO:")
        unreal.log("-" * 80)
        
        # Check AddMenuEntry (might be different name)
        for name in ['add_menu_entry', 'AddMenuEntry', 'add_section', 'AddSection', 
                     'add_sub_menu', 'AddSubMenu', 'insert_menu_entry', 'InsertMenuEntry']:
            if hasattr(menu, name):
                unreal.log(f"   ✓ Found: {name}")
                try:
                    method_obj = getattr(menu, name)
                    unreal.log(f"     Type: {type(method_obj)}")
                    unreal.log(f"     Callable: {callable(method_obj)}")
                except Exception as e:
                    unreal.log(f"     Error getting details: {e}")
        
        # List properties
        unreal.log("\n5. PROPERTIES:")
        unreal.log("-" * 80)
        props = [a for a in attrs if not callable(getattr(menu, a)) and not a.startswith('_')]
        for prop in props[:10]:
            try:
                val = getattr(menu, prop)
                unreal.log(f"   {prop}: {val}")
            except:
                unreal.log(f"   {prop}: <error reading>")
    
    # Check ToolMenuEntry
    unreal.log("\n6. ToolMenuEntry CLASS:")
    unreal.log("-" * 80)
    try:
        entry = unreal.ToolMenuEntry()
        unreal.log(f"   Created: {type(entry)}")
        
        entry_methods = [m for m in dir(entry) if not m.startswith('_')]
        unreal.log(f"   Methods/Properties count: {len(entry_methods)}")
        unreal.log("   Available:")
        for method in entry_methods[:20]:
            unreal.log(f"     - {method}")
    except Exception as e:
        unreal.log(f"   Error: {e}")
    
    # Check what constants are available
    unreal.log("\n7. MultiBlockType enum values:")
    unreal.log("-" * 80)
    try:
        if hasattr(unreal, 'MultiBlockType'):
            block_types = dir(unreal.MultiBlockType)
            types = [t for t in block_types if not t.startswith('_')]
            for t in types[:15]:
                unreal.log(f"     - {t}")
    except Exception as e:
        unreal.log(f"   Error: {e}")
    
    # Try ToolMenuStringCommandType
    unreal.log("\n8. ToolMenuStringCommandType enum values:")
    unreal.log("-" * 80)
    try:
        if hasattr(unreal, 'ToolMenuStringCommandType'):
            cmd_types = dir(unreal.ToolMenuStringCommandType)
            types = [t for t in cmd_types if not t.startswith('_')]
            for t in types[:15]:
                unreal.log(f"     - {t}")
    except Exception as e:
        unreal.log(f"   Error: {e}")
    
except Exception as e:
    unreal.log(f"\nERROR: {e}")
    import traceback
    unreal.log(traceback.format_exc())

unreal.log("\n" + "=" * 80)
unreal.log("END DEBUG")
unreal.log("=" * 80)
