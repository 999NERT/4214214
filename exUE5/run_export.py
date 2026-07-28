import os
import sys
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from exporter import export_current_sequence, load_config


if __name__ == "__main__":
    unreal.log("[exUE5] Starting export...")
    
    config = load_config()
    output_dir = config.get("default_output_folder", "D:/Exports")
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "exported_sequence.fbx")
        
        result = export_current_sequence(output_path, config)
        
        unreal.log(f"[exUE5] ✓ Export completed successfully!")
        unreal.log(f"[exUE5] File saved to: {output_path}")
        
    except Exception as exc:
        unreal.log(f"[exUE5] ✗ Export failed: {exc}")
        import traceback
        unreal.log(traceback.format_exc())
