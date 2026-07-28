import unreal

unreal.log("=" * 80)
unreal.log("INSPECTING ToolMenus CLASS METHODS")
unreal.log("=" * 80)

try:
    menus = unreal.ToolMenus.get()
    unreal.log(f"Type: {type(menus)}")
    
    unreal.log("\nAvailable methods on ToolMenus instance:")
    methods = [m for m in dir(menus) if not m.startswith('_')]
    for i, m in enumerate(methods, 1):
        unreal.log(f"  {i:2d}. {m}")
    
    # Check for register_menu specifically
    unreal.log("\nChecking for key methods:")
    for name in ['register_menu', 'RegisterMenu', 'register_top_level_menu', 'add_menu']:
        if hasattr(menus, name):
            unreal.log(f"  ✓ Found: {name}")
    
    # Try to see what MultiBoxType has
    unreal.log("\nMultiBoxType enum values:")
    if hasattr(unreal, 'MultiBoxType'):
        types = [t for t in dir(unreal.MultiBoxType) if not t.startswith('_')]
        for t in types[:15]:
            unreal.log(f"  - {t}")
    
except Exception as e:
    unreal.log(f"ERROR: {e}")
    import traceback
    unreal.log(traceback.format_exc())

unreal.log("=" * 80)
