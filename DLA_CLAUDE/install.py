import os
import sys
from pathlib import Path
import importlib

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent
for path in (str(ROOT), str(PARENT)):
    if path not in sys.path:
        sys.path.insert(0, path)

# Force reload of modules to avoid caching issues
for module_name in ('exporter', 'menu', 'exUE5.exporter', 'exUE5.menu'):
    if module_name in sys.modules:
        del sys.modules[module_name]

try:
    import exUE5.menu as menu_module
    import exUE5.exporter as exporter_module
    importlib.reload(menu_module)
    importlib.reload(exporter_module)
    install_menu = menu_module.install_menu
    uninstall_menu = menu_module.uninstall_menu
except ModuleNotFoundError:
    try:
        from exUE5.menu import install_menu, uninstall_menu
        import exUE5.exporter as exporter_module
        importlib.reload(exporter_module)
    except ModuleNotFoundError:
        try:
            from menu import install_menu, uninstall_menu
        except Exception as exc:
            raise RuntimeError(
                f"[exUE5] install.py: nie udalo sie zaimportowac menu.py "
                f"(prawdopodobny blad skladni/logiki WEWNATRZ menu.py, "
                f"nie problem ze sciezka importu): {exc}"
            ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"[exUE5] install.py: blad podczas importu exUE5.menu / "
            f"exUE5.exporter (prawdopodobny blad skladni/logiki wewnatrz "
            f"tych plikow, nie problem ze sciezka importu): {exc}"
        ) from exc
except Exception as exc:
    raise RuntimeError(
        f"[exUE5] install.py: nieoczekiwany blad podczas importu "
        f"exUE5.menu / exUE5.exporter (sprawdz skladnie/logike w tych "
        f"plikach - to NIE jest problem ze sciezka importu): {exc}"
    ) from exc


def install():
    install_menu()
    print("[exUE5] Menu integration is disabled by default; PLUGSY exporter remains available via script")


def uninstall():
    uninstall_menu()
    print("[exUE5] PLUGSY Exporter menu registration removed (if it existed)")


def reinstall():
    uninstall_menu()
    install_menu()
    print("[exUE5] Reinstalled exporter menu")


if __name__ == "__main__":
    reinstall()
