import unreal
import inspect

unreal.log("=" * 80)
unreal.log("INSPECTING register_menu SIGNATURE")
unreal.log("=" * 80)

try:
    menus = unreal.ToolMenus.get()
    
    # Get signature
    unreal.log("Trying to inspect register_menu signature...")
    
    # Try different approaches
    method = menus.register_menu
    unreal.log(f"Method: {method}")
    unreal.log(f"Type: {type(method)}")
    
    try:
        sig = inspect.signature(method)
        unreal.log(f"Signature: {sig}")
    except Exception as e:
        unreal.log(f"inspect.signature failed: {e}")
    
    # Try to see docstring
    unreal.log(f"Docstring: {method.__doc__}")
    
    # Try to get parameter info using __code__
    try:
        code = method.__code__
        unreal.log(f"__code__ varnames: {code.co_varnames}")
        unreal.log(f"__code__ argcount: {code.co_argcount}")
    except:
        unreal.log("Could not access __code__")
    
    # Check is_menu_registered
    unreal.log("\nTrying is_menu_registered:")
    try:
        result = menus.is_menu_registered("LevelEditor.MainMenu.File")
        unreal.log(f"is_menu_registered('LevelEditor.MainMenu.File') = {result}")
    except Exception as e:
        unreal.log(f"Error: {e}")
    
    # Try ToolMenuOwner
    unreal.log("\nToolMenuOwner info:")
    try:
        owner = unreal.ToolMenuOwner()
        unreal.log(f"Created ToolMenuOwner: {owner}")
        owner_attrs = [a for a in dir(owner) if not a.startswith('_')]
        unreal.log(f"Attributes: {owner_attrs}")
    except Exception as e:
        unreal.log(f"Error: {e}")
    
except Exception as e:
    unreal.log(f"ERROR: {e}")
    import traceback
    unreal.log(traceback.format_exc())

unreal.log("=" * 80)
