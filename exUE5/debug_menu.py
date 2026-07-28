import unreal

unreal.log("=== DEBUG MENU API ===")

try:
    menus = unreal.ToolMenus.get()
    unreal.log(f"ToolMenus.get() = {menus}")
    unreal.log(f"ToolMenus type: {type(menus)}")
    
    menu = menus.find_menu("LevelEditor.MainMenu.Tools")
    unreal.log(f"Found menu: {menu}")
    
    if menu:
        # List all methods
        unreal.log("=== ToolMenu methods ===")
        methods = [m for m in dir(menu) if not m.startswith('_')]
        for m in methods:
            unreal.log(f"  {m}")
        
        # Check add_menu_entry specifically
        if hasattr(menu, 'add_menu_entry'):
            unreal.log("add_menu_entry exists!")
            import inspect
            try:
                sig = inspect.signature(menu.add_menu_entry)
                unreal.log(f"Signature: {sig}")
            except:
                unreal.log("Could not get signature via inspect")
        
        # Try ToolMenuEntry
        unreal.log("=== ToolMenuEntry ===")
        entry = unreal.ToolMenuEntry()
        unreal.log(f"Created entry: {entry}")
        entry_methods = [m for m in dir(entry) if not m.startswith('_')]
        for m in entry_methods[:20]:  # First 20 only
            unreal.log(f"  {m}")
            
except Exception as e:
    unreal.log(f"ERROR: {e}")
    import traceback
    unreal.log(traceback.format_exc())

unreal.log("=== END DEBUG ===")
