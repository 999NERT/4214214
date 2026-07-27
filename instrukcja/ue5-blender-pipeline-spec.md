# UE5 → Blender — transfer sceny (Sequencer + Level) — specyfikacja techniczna

Wersje docelowe: **Unreal Engine 5.8.0**, **Blender 5.0.1**.
Rola tego dokumentu: kontekst do wygenerowania implementacji (np. przez Copilota). Zawiera architekturę, format wymiany, szkielety funkcji i checklistę testową.

---

## 1. Zakres

Dwa niezależne narzędzia:

1. **UE5 Export Tool** — plugin/skrypt uruchamiany w edytorze UE5. Bierze wybrany Level Sequence + poziom, pozwala zaznaczyć co eksportować, zapisuje do folderu: plik(i) USD + manifest JSON.
2. **Blender Import Add-on** — extension na Blendera 5.0. Wskazujesz folder wygenerowany przez narzędzie #1, klikasz import, dostajesz scenę 1:1 (bez materiałów/tekstur/shaderów).

Nośnik danych między nimi: **USD** (nie FBX — powody w sekcji 3).

---

## 2. Architektura

```
UE5: Sequencer + Level (źródło)
        │
        ▼
UE5 Export Tool (Editor Utility Widget + Python)
  - odczyt zaznaczonych bindingów w Sequencerze
  - bake do USD (poziom + sekwencja + subsekwencje)
  - zapis manifest.json
        │
        ▼
Folder wymiany: /export_XXXX/
  ├── scene.usd (lub .usda do debugowania)
  ├── manifest.json
        │
        ▼
Blender Import Add-on (extension, bpy)
  - wczytanie manifestu
  - bpy.ops.wm.usd_import(...)
  - korekta kamer, jednostek, kolekcji
  - markery kamer z camera-cuts
        │
        ▼
Scena w Blenderze (geometria + animacje + kamery, bez materiałów)
```

---

## 3. Format wymiany: dlaczego USD

- Eksport/import FBX z Sequencera **nie działa** z Master Sequences, shotami w Masterze ani z Subscenes (ograniczenie udokumentowane przez Epic). Jeśli w projekcie są pod-sekwencje/shoty — FBX odpada jako główna ścieżka.
- `unreal.LevelSequenceExporterUsdOptions` ma dokładnie potrzebne opcje: `export_level` (dołącza poziom), `export_subsequences_as_layers` (obsługa zagnieżdżonych sekwencji), `override_export_range` + `start_frame`/`end_frame`.
- Morph targety (kluczowe dla twarzy MetaHumana) eksportują się przez USD jako **USD BlendShapes** — natywnie obsługiwane. Ścieżka FBX ma udokumentowany, historyczny problem ze zgodnością blend shape'ów przy imporcie do Blendera — **do przetestowania**, nie zakładać, że działa.
- Blender 4.0+ ma natywny importer `UsdSkel`: szkielety → Armatures, blend shape'y → shape keys, kamery z poprawkami sensor-fit.

**FBX zostaje jako fallback wyłącznie dla prostych scen bez subsekwencji i bez animacji blend shape** (np. samo Body MetaHumana albo statyczne mesh transformy).

### 3.1 Manifest JSON — schema

Manifest niesie metadane, których sam plik USD nie przenosi wygodnie (jednostki, typy aktorów, camera cuts, mapowanie MetaHuman Body/Face).

```json
{
  "schema_version": "1.0",
  "source": {
    "ue_version": "5.8.0",
    "level_path": "/Game/Maps/MyLevel",
    "sequence_path": "/Game/Cinematics/MySequence"
  },
  "frame_rate": 30.0,
  "frame_range": { "start": 0, "end": 240 },
  "units": { "ue_unit": "cm", "scale_to_blender_m": 0.01 },
  "objects": [
    {
      "id": "actor_0001",
      "label": "Cube_150",
      "type": "static_mesh",
      "usd_prim_path": "/Root/Level/Cube_150",
      "binding_type": "possessable"
    },
    {
      "id": "actor_0002",
      "label": "BP_MetaHuman_01",
      "type": "metahuman",
      "shared_skeleton_root_bone": "head",
      "components": [
        {
          "role": "body",
          "usd_prim_path": "/Root/Sequence/BP_MetaHuman_01/Body",
          "has_bone_animation": true,
          "bone_count": 341,
          "is_leader_pose_source": true
        },
        {
          "role": "face",
          "usd_prim_path": "/Root/Sequence/BP_MetaHuman_01/Face",
          "has_bone_animation": true,
          "has_blendshape_animation": false,
          "bone_count_total": 874,
          "bone_count_shared_with_body": 31,
          "bone_count_facial_only": 843,
          "blendshape_channel_count": 858,
          "blendshape_curves_path": null,
          "leader_pose_component_target": "Body"
        }
      ]
    },
    {
      "id": "actor_0003",
      "label": "CineCamera_A",
      "type": "camera",
      "usd_prim_path": "/Root/Sequence/CineCamera_A",
      "lens": { "focal_length_mm": 35.0, "sensor_width_mm": 23.76, "sensor_height_mm": 13.365 }
    }
  ],
  "camera_cuts": [
    { "frame": 0,   "camera_id": "actor_0003" },
    { "frame": 120, "camera_id": "actor_0004" }
  ]
}
```

`type` w `objects[]`: `static_mesh | skeletal_mesh | metahuman | camera | light` (light pomijamy w MVP, bo user nie chce materiałów/oświetlenia, ale zostawiamy pole na przyszłość).

**Face ma dwa niezależne pola `has_bone_animation` i `has_blendshape_animation`, nie jedno `animation_kind`.** To zmiana względem wcześniejszej wersji tej specyfikacji i wynika z realnej analizy plików źródłowych (sekcja 8) — twarz MetaHumana rusza się jednocześnie kośćmi (szczęka, gałki oczne, język — ok. 843 kości `FACIAL_*`) i wagami blend shape'ów (858 kanałów, głównie skóra/mimika). `blendshape_curves_path` to opcjonalna ścieżka do osobnego pliku z krzywymi wag blend shape'ów — patrz sekcja 8.3, to zalecany plan B, gdyby transfer blend shape'ów przez USD zawiódł.

---

## 4. UE5 Export Tool

### 4.1 Struktura

Plugin UE5 (`/Plugins/SceneToBlenderExporter/`):

```
SceneToBlenderExporter/
├── SceneToBlenderExporter.uplugin
├── Content/
│   ├── Python/
│   │   ├── export_core.py       # cała logika, bez zależności od UI
│   │   ├── metahuman_export.py  # obsługa Body/Face
│   │   └── manifest_builder.py
│   └── EUW_SceneExporter.uasset # Editor Utility Widget (UI, Blueprint)
└── Source/                      # puste w MVP — nie potrzebujesz C++, EUW+Python wystarczy
```

UI robimy jako **Editor Utility Widget** (Blueprint), bo to najszybsza droga do checkboxów/listy/przycisków bez pisania Slate w C++. EUW wywołuje funkcje z `export_core.py` przez `unreal.py` bridge.

### 4.2 Wymagania UI (EUW)

- Dropdown/picker: Level Sequence (domyślnie: aktualnie otwarty w Sequencerze)
- Pole: ścieżka folderu wyjściowego (File Dialog)
- Lista bindingów z aktualnego Sequencera z checkboxami — **ale w MVP korzystamy z natywnego zaznaczenia w Sequencerze zamiast budować to od zera**: przycisk "Eksportuj zaznaczone" czyta `unreal.LevelSequenceEditorBlueprintLibrary.get_selected_bindings()`. Jeśli nic nie zaznaczono → eksportuj wszystko.
- Checkbox: "Dołącz poziom" (`export_level`)
- Checkbox: "Rozwiń subsekwencje jako warstwy" (`export_subsequences_as_layers`)
- Przycisk: Eksportuj → wywołuje `export_core.run_export(...)`
- Pole tekstowe/log na wynik (sukces/błąd, ścieżka pliku)

### 4.3 `export_core.py` — szkielet

```python
import unreal
import json
import os

def get_bindings_to_export(sequence: unreal.LevelSequence) -> list:
    """Zwraca zaznaczone bindingi w Sequencerze; jeśli brak zaznaczenia, wszystkie."""
    selected = unreal.LevelSequenceEditorBlueprintLibrary.get_selected_bindings()
    if selected:
        return selected
    return sequence.get_bindings()


def export_to_usd(world: unreal.World, sequence: unreal.LevelSequence,
                   output_dir: str, export_level: bool = True,
                   export_subsequences_as_layers: bool = True,
                   start_frame: int = None, end_frame: int = None) -> str:
    """Eksportuje sekwencję (+ poziom) do USD. Zwraca ścieżkę do pliku .usd."""
    options = unreal.LevelSequenceExporterUsdOptions()
    options.export_level = export_level
    options.export_subsequences_as_layers = export_subsequences_as_layers
    if start_frame is not None and end_frame is not None:
        options.override_export_range = True
        options.start_frame = start_frame
        options.end_frame = end_frame

    os.makedirs(output_dir, exist_ok=True)
    usd_path = os.path.join(output_dir, "scene.usd")

    # UWAGA: dokładna nazwa funkcji eksportu USD zmieniała się między wersjami UE
    # (np. unreal.SequencerTools / unreal.UsdConversionLibrary / unreal.LevelSequenceExporterUsd
    #  w zależności od wersji 5.x) — sprawdzić dokładną sygnaturę w:
    # https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/?application_version=5.8
    # przed implementacją; to jest miejsce na weryfikację przez Copilota/testy w edytorze.
    success = unreal.LevelSequenceExporterUsdOptions.export_level_sequence(
        world, sequence, options, usd_path
    )
    if not success:
        raise RuntimeError(f"USD export failed for {sequence.get_name()}")
    return usd_path


def export_fallback_fbx(world: unreal.World, sequence: unreal.LevelSequence,
                         bindings: list, output_dir: str) -> str:
    """Fallback dla prostych scen bez subsekwencji/blend shape'ów."""
    fbx_path = os.path.join(output_dir, "scene_fallback.fbx")
    export_options = unreal.FbxExportOption()
    success = unreal.SequencerTools.export_level_sequence_fbx(
        world, sequence, bindings, [], export_options, fbx_path
    )
    if not success:
        raise RuntimeError("FBX fallback export failed")
    return fbx_path
```

### 4.4 Obsługa MetaHuman — `metahuman_export.py`

**To jest najbardziej ryzykowna część całego pipeline'u — przeczytaj najpierw sekcję 8, tam jest pełne uzasadnienie na podstawie realnej analizy plików FBX.** Skrót tego, co trzeba wiedzieć przed pisaniem kodu:

- Aktor MetaHuman Blueprint ma dwa komponenty skeletal mesh — `Body` i `Face` — ale **nie są to dwa niezależne szkielety**. Dzielą ten sam `MetaHuman_Base_Skeleton`: Face zawiera pełną, zdublowaną kopię wspólnego łańcucha kości ciała (pelvis → spine_01…05 → clavicle/upperarm → neck_01/neck_02 → head, **31 kości**) plus własny rig twarzy pod `FACIAL_C_FacialRoot` (**843 kości**, plus **858 kanałów blend shape**).
- W UE ten wspólny łańcuch na komponencie Face jest napędzany przez **Set Leader Pose Component** wskazujący na Body — Face go nie animuje sam, tylko kopiuje pozę z Body. Jeśli to zignorujesz przy eksporcie/imporcie, dostaniesz efekt znany z forum Epic jako "Face and Body Detached" (głowa/twarz rozjeżdża się z ciałem) — patrz sekcja 8.2.
- **Wniosek dla eksportera:** eksportuj Body i Face jako dwa osobne skeletal mesh (tak jak dotychczas), ale manifest musi jawnie oznaczyć, które kości w Face są duplikatem współdzielonego łańcucha (żeby Blender addon mógł je odrzucić i zamiast tego podłączyć rig twarzy pod `head` z Body — plan mergowania w sekcji 8.4).

```python
def is_metahuman_actor(actor: unreal.Actor) -> bool:
    """Heurystyka: aktor ma komponenty Body i Face jako SkeletalMeshComponent."""
    components = actor.get_components_by_class(unreal.SkeletalMeshComponent)
    names = {c.get_name().lower() for c in components}
    return "body" in names and "face" in names


def describe_metahuman(actor: unreal.Actor, reference_data: dict) -> dict:
    """Zwraca fragment manifestu dla jednego MetaHumana. `reference_data` to
    wczytane pliki metahuman_body_bones.json / metahuman_face_bones.json
    (sekcja 8) — używane do oznaczenia, które kości w Face są duplikatem
    wspólnego łańcucha z Body (do odrzucenia po stronie Blendera)."""
    shared_bones = set(reference_data["face_bones"]["shared_bones_with_body"])
    result = {"shared_skeleton_root_bone": "head", "components": []}

    for role in ("body", "face"):
        comp = next((c for c in actor.get_components_by_class(unreal.SkeletalMeshComponent)
                     if c.get_name().lower() == role), None)
        if comp is None:
            continue
        entry = {
            "role": role,
            "has_bone_animation": _component_has_keyed_bone_track(actor, comp),
        }
        if role == "face":
            entry["has_blendshape_animation"] = _component_has_keyed_morph_curves(actor, comp)
            entry["duplicate_shared_bones_to_ignore"] = sorted(shared_bones)
            entry["facial_rig_root_bone"] = "FACIAL_C_FacialRoot"
            entry["leader_pose_component_target"] = "Body"
        result["components"].append(entry)
    return result
```

`_component_has_keyed_bone_track` i `_component_has_keyed_morph_curves` — do dopisania: pierwsza sprawdza `get_all_tracks()` pod kątem transform/control rig tracków z kluczami w zakresie eksportu (jak poprzednio), druga sprawdza konkretnie tracki krzywych morph target/blend shape na komponencie Face (osobny typ tracka w Sequencerze niż transform kości) — **do zweryfikowania w edytorze, jaki dokładnie typ tracka/klasy Pythona to reprezentuje w 5.8**, bo to jest jednocześnie test z Fazy 5 (czy w ogóle da się to wykryć/wyeksportować przez USD).

### 4.5 `manifest_builder.py` — szkielet

```python
def build_manifest(sequence, bindings, level_path: str, output_dir: str,
                    frame_rate: float, frame_start: int, frame_end: int) -> dict:
    manifest = {
        "schema_version": "1.0",
        "source": {
            "ue_version": unreal.SystemLibrary.get_engine_version(),
            "level_path": level_path,
            "sequence_path": sequence.get_path_name(),
        },
        "frame_rate": frame_rate,
        "frame_range": {"start": frame_start, "end": frame_end},
        "units": {"ue_unit": "cm", "scale_to_blender_m": 0.01},
        "objects": [],
        "camera_cuts": [],
    }
    for binding in bindings:
        obj = binding.get_object_template()
        entry = {"id": str(binding.get_id()), "label": obj.get_name()}
        if is_metahuman_actor(obj):
            entry["type"] = "metahuman"
            entry.update(describe_metahuman(obj))
        elif isinstance(obj, unreal.CineCameraActor):
            entry["type"] = "camera"
            entry["lens"] = _extract_camera_lens(obj)
        else:
            entry["type"] = "static_mesh"
        manifest["objects"].append(entry)

    manifest["camera_cuts"] = _extract_camera_cuts(sequence)
    return manifest


def save_manifest(manifest: dict, output_dir: str) -> str:
    path = os.path.join(output_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return path
```

`_extract_camera_lens` i `_extract_camera_cuts` — do dopisania na bazie `unreal.MovieSceneCameraCutTrack` i property `CineCameraComponent` (focal length, sensor size).

### 4.6 Plan B dla blend shape'ów twarzy — `blendshape_curve_export.py`

USD/FBX blend shape export dla MetaHumana ma historię problemów (sekcja 8.2 — udokumentowany przypadek z 2022, gdzie eksporter USD w ogóle nie obsługiwał animacji komponentów twarzy). Zamiast polegać wyłącznie na tym, że USD poprawnie zapisze 858 kanałów wag, warto mieć niezależny, prosty fallback: wyeksportować wagi blend shape'ów klatka po klatce jako zwykłe liczby w JSON, z pominięciem całego mechanizmu USD BlendShapes. To trywialne dane (nazwa kanału → wartość 0.0-1.0 na klatkę), więc ryzyko błędu jest dużo mniejsze niż w całym potoku eksportu geometrii.

```python
def export_blendshape_curves(actor: unreal.Actor, face_component: unreal.SkeletalMeshComponent,
                              channel_names: list, frame_start: int, frame_end: int,
                              output_path: str) -> str:
    """Ewaluuje sekwencję klatka po klatce i zapisuje wagi morph targetów
    komponentu Face niezależnie od eksportu USD/FBX. channel_names pochodzi
    z metahuman_face_blendshapes.json (sekcja 8) — pozwala od razu wykryć,
    czy któryś kanał nie istnieje na tym konkretnym komponencie (literówka,
    inna wersja MetaHumana, LOD itd.)."""
    curves = {name: [] for name in channel_names}
    missing = []
    for frame in range(frame_start, frame_end + 1):
        # ustawienie playhead sekwencji na tej klatce — dokładna funkcja do
        # zweryfikowania (unreal.LevelSequenceEditorBlueprintLibrary.set_current_time
        # albo evaluacja przez unreal.Sequencer w trybie headless), patrz otwarte pytania
        _set_sequence_playhead(frame)
        for name in channel_names:
            value = face_component.get_morph_target_curve_value(name) \
                if hasattr(face_component, "get_morph_target_curve_value") else None
            if value is None:
                if name not in missing:
                    missing.append(name)
                value = 0.0
            curves[name].append(value)

    if missing:
        unreal.log_warning(f"Brak {len(missing)} kanałów blend shape na komponencie Face: {missing[:5]}...")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"frame_start": frame_start, "frame_end": frame_end,
                    "channels": curves, "missing_channels": missing}, f)
    return output_path
```

Po stronie Blendera to się aplikuje bez pośrednictwa USD/FBX importera — bezpośrednio jako `shape_key.value` + `keyframe_insert` na każdej klatce, po nazwie kanału (nazwy shape keys po imporcie geometrii powinny być identyczne z nazwami z `metahuman_face_blendshapes.json`, bo to te same stringi z tego samego FBX/USD). To rozwiązuje problem niezależnie od tego, czy standardowy import blend shape'ów przez `usd_import`/FBX zadziała.

---

## 5. Blender Import Add-on (Extension, Blender 5.0.1)

### 5.1 Struktura projektu

```
scene_from_ue5/
├── blender_manifest.toml
├── __init__.py
├── operators.py
├── ui.py
└── manifest_reader.py
```

`blender_manifest.toml`:

```toml
schema_version = "1.0.0"
id = "scene_from_ue5"
version = "0.1.0"
name = "Scene From UE5"
tagline = "Import a UE5 Sequencer scene exported via USD"
maintainer = "Your Name <[email protected]>"
type = "add-on"
blender_version_min = "5.0.0"
license = ["SPDX:GPL-3.0-or-later"]

[permissions]
files = "Read the exported UE5 scene folder (USD + manifest.json)"
```

### 5.2 `operators.py` — szkielet

```python
import bpy
import json
import os


class SCENEUE5_OT_import(bpy.types.Operator):
    """Import a scene folder exported by the UE5 Export Tool"""
    bl_idname = "sceneue5.import_folder"
    bl_label = "Import UE5 Scene"
    bl_options = {'REGISTER', 'UNDO'}

    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    match_ue_units: bpy.props.BoolProperty(
        name="Zachowaj surowe jednostki UE (cm)",
        description="Jeśli włączone, liczby transformów zgadzają się 1:1 z UE "
                    "(150 -> 150), zamiast konwersji na metry Blendera",
        default=False,
    )

    def execute(self, context):
        manifest_path = os.path.join(self.directory, "manifest.json")
        if not os.path.exists(manifest_path):
            self.report({'ERROR'}, f"Nie znaleziono manifest.json w {self.directory}")
            return {'CANCELLED'}

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        usd_path = os.path.join(self.directory, "scene.usd")

        if self.match_ue_units:
            context.scene.unit_settings.system = 'NONE'
        # scale w usd_import poniżej dopasowana do wyboru jednostek

        bpy.ops.wm.usd_import(
            filepath=usd_path,
            import_skeletons=True,
            import_blendshapes=True,
            import_cameras=True,
            import_materials=False,   # user nie chce materiałów/tekstur
            scale=1.0 if self.match_ue_units else 0.01,
        )

        _apply_scene_settings(context, manifest)
        _fix_camera_sensor_fit(manifest)
        _organize_into_collections(manifest)
        _build_camera_cut_markers(context, manifest)

        self.report({'INFO'}, "Import zakończony")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def _apply_scene_settings(context, manifest: dict):
    context.scene.render.fps = int(manifest["frame_rate"])
    context.scene.frame_start = manifest["frame_range"]["start"]
    context.scene.frame_end = manifest["frame_range"]["end"]


def _fix_camera_sensor_fit(manifest: dict):
    """Ustawia Sensor Fit na Horizontal/Vertical zamiast Auto —
    inaczej proporcje kadru z UE bywają zniekształcone po imporcie USD."""
    for obj in manifest["objects"]:
        if obj["type"] != "camera":
            continue
        cam_obj = bpy.data.objects.get(obj["label"])
        if cam_obj is None or cam_obj.type != 'CAMERA':
            continue
        cam_obj.data.sensor_fit = 'HORIZONTAL'


def _organize_into_collections(manifest: dict):
    """Grupuje zaimportowane obiekty w kolekcje wg roli (Body/Face osobno itd.)."""
    pass  # do dopisania: mapowanie manifest["objects"] -> bpy.data.collections


def _build_camera_cut_markers(context, manifest: dict):
    """Odtwarza UE Camera Cuts Track jako markery kamer na osi czasu Blendera."""
    for cut in manifest.get("camera_cuts", []):
        cam_label = next(o["label"] for o in manifest["objects"] if o["id"] == cut["camera_id"])
        cam_obj = bpy.data.objects.get(cam_label)
        if cam_obj is None:
            continue
        marker = context.scene.timeline_markers.new(name=cam_label, frame=cut["frame"])
        marker.camera = cam_obj
        context.scene.render.use_multiview = False  # noop placeholder, keep camera markers active
    # Blender wymaga też: context.scene.camera = <pierwsza kamera> i włączenia
    # "markers used for camera" — patrz UI panel timeline, ewentualnie ustawić przez
    # context.scene.timeline_markers oraz context.scene.camera dla klatki 0
```

### 5.3 `ui.py` — szkielet

```python
import bpy


class SCENEUE5_PT_panel(bpy.types.Panel):
    bl_label = "Scene From UE5"
    bl_idname = "SCENEUE5_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UE5 Import"

    def draw(self, context):
        layout = self.layout
        layout.operator("sceneue5.import_folder", text="Wybierz folder i importuj")
```

### 5.4 `__init__.py`

```python
import bpy
from .operators import SCENEUE5_OT_import
from .ui import SCENEUE5_PT_panel

classes = (SCENEUE5_OT_import, SCENEUE5_PT_panel)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
```

### 5.5 `metahuman_merge.py` — mergowanie szkieletu Face do Body

Implementuje plan z sekcji 8.4. Uruchamiane po imporcie geometrii, dla każdego obiektu typu `metahuman` z manifestu.

```python
import bpy


def merge_face_into_body_armature(body_armature_obj: bpy.types.Object,
                                    face_armature_obj: bpy.types.Object,
                                    face_mesh_obj: bpy.types.Object,
                                    duplicate_shared_bones: list,
                                    facial_rig_root_bone: str = "FACIAL_C_FacialRoot",
                                    attach_to_bone: str = "head"):
    """Laczy szkielet Face z Body w jeden Armature, zgodnie z architektura
    Leader Pose Component opisana w sekcji 8. Po wykonaniu: face_mesh_obj
    jest zwiazany z body_armature_obj, face_armature_obj mozna usunac."""

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = body_armature_obj
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = body_armature_obj.data.edit_bones
    if facial_rig_root_bone not in edit_bones:
        # kopiowanie podrzewa FACIAL_* z face_armature_obj do body_armature_obj
        # jest wymagane przed re-parentowaniem — nie da się po prostu "przepiac"
        # kosci pomiedzy roznymi obiektami Armature w Blenderze, trzeba je
        # fizycznie skopiowac (np. przez bpy.ops.object.join po ustawieniu
        # face_armature_obj jako selected + body_armature_obj jako active,
        # PRZED tym usuwajac z face_armature_obj kosci z duplicate_shared_bones,
        # zeby join nie tworzyl duplikatow o sufiksie '.001')
        raise NotImplementedError(
            "Krok 1: usun z face_armature_obj kosci z duplicate_shared_bones "
            "(edit_bones.remove), potem bpy.ops.object.join(body+face armature), "
            "dopiero potem ten re-parenting."
        )

    edit_bones[facial_rig_root_bone].parent = edit_bones[attach_to_bone]
    edit_bones[facial_rig_root_bone].use_connect = False

    bpy.ops.object.mode_set(mode='OBJECT')

    # face_mesh_obj po polaczeniu armatures wskazuje juz na body_armature_obj
    # (jesli join zrobiony poprawnie) — modifier Armature powinien sam
    # rozwiazac sie po nazwie, bo vertex groups na face_mesh_obj maja te
    # same nazwy kosci co w polaczonym szkielecie. Do weryfikacji w testach.
    for mod in face_mesh_obj.modifiers:
        if mod.type == 'ARMATURE':
            mod.object = body_armature_obj
    face_mesh_obj.parent = body_armature_obj
```

**To jest szkielet, nie gotowy kod** — krok z `bpy.ops.object.join` na danych Armature (nie mesh) wymaga uważnego przetestowania w Blenderze 5.0.1 (zachowanie się nazw kości przy konflikcie, zachowanie animacji obu armatures podczas łączenia). To jedno z najważniejszych miejsc do rozbudowania przez Copilota z realnym testowaniem w edytorze, nie na sucho.

---

## 6. Checklista testowa (zrobić PRZED budową pełnej wersji, na małej scenie testowej)

Zbuduj scenę testową: 1 cube (transform), 1 statyczna kamera z animowanym focal length, 1 MetaHuman z animacją tylko na Body, potem osobno test z animacją blend shape na Face.

- [ ] Cube 150×150×150 w UE → sprawdzić czy w Blenderze wychodzi 1.5×1.5×1.5 (domyślnie) albo 150×150×150 (przy `match_ue_units=True`)
- [ ] Animacja transformu cube'a — czy krzywe się zgadzają klatka po klatce (porównać kilka klatek ręcznie)
- [ ] Kamera: sprawdzić Sensor Fit po imporcie, porównać FOV wizualnie w UE vs Blender
- [ ] MetaHuman Body: czy szkielet + animacja kości importują się jako Armature z akcją (oczekiwane: 341 pose bones, patrz `metahuman_body_bones.json`)
- [ ] MetaHuman Face bez animacji: czy mesh twarzy jest statyczny (zgodnie z oczekiwaniem)
- [ ] MetaHuman Face z animacją blend shape: czy shape keys mają klucze animacji (test USD; jeśli nie działa — użyj Plan B z sekcji 4.6)
- [ ] **Kość `root`**: czy wierzchołki skinowane bezpośrednio do `root` (potwierdzone w obu plikach źródłowych, sekcja 8.1) deformują się poprawnie po imporcie — Blender FBX-importer nie tworzy `root` jako pose_bone, ryzyko cichego błędu bez komunikatu
- [ ] **Merge Body+Face**: po scaleniu szkieletów (sekcja 5.5) sprawdź, czy `FACIAL_C_FacialRoot` faktycznie podąża za `head` z Body podczas animacji, i czy mesh twarzy nie "pływa" względem ciała
- [ ] **Walidacja nazw**: po eksporcie z UE porównaj programowo listę wyeksportowanych kości/blend shape'ów z `metahuman_body_bones.json` / `metahuman_face_bones.json` / `metahuman_face_blendshapes.json` — każda rozbieżność (brakująca/dodatkowa nazwa) sygnalizuje błąd w eksporcie, zanim dojdzie do Blendera
- [ ] Subsekwencje/shoty: eksport sceny z pod-sekwencją, sprawdzić czy `export_subsequences_as_layers` faktycznie je przenosi
- [ ] Camera cuts: 2 kamery przełączające się w połowie sekwencji → sprawdzić markery w Blenderze
- [ ] Framerate i zakres klatek: czy scena w Blenderze ma ten sam FPS i długość

---

## 7. Plan wdrożenia (fazowany, do rozbicia na taski dla Copilota)

**Faza 1 — szkielet:** oba projekty się rejestrują/ładują bez błędów (pusty eksport i pusty import), UI się wyświetla.

**Faza 2 — statyczne transformy:** cube z transformem statycznym, przejście przez cały pipeline, weryfikacja pozycji.

**Faza 3 — animacja transformu + kamera:** animowany cube, animowana kamera, camera cuts.

**Faza 4 — MetaHuman Body:** szkielet + animacja kości.

**Faza 5 — MetaHuman Face (blend shapes):** najbardziej ryzykowna faza — zacząć od testu na małej scenie zanim zintegrujesz z resztą.

**Faza 6 — subsekwencje/shoty + porządkowanie kolekcji w Blenderze.**

**Faza 7 — dopracowanie UI** (lista bindingów z checkboxami zamiast polegania na zaznaczeniu w Sequencerze, progress bar, walidacja ścieżek).

---

## 8. MetaHuman "1REAL" — dane zweryfikowane bezpośrednio z surowych plików FBX

Ta sekcja podsumowuje analizę realnych plików źródłowych (`SKM_1REAL_BodyMesh.FBX`, `SKM_1REAL_FaceMesh.FBX`, plus test z animacją `RAYIN.FBX`), nie dokumentacji ogólnej. Cztery pliki referencyjne wygenerowane z tej analizy leżą obok tego dokumentu i są **danymi wejściowymi dla kodu**, nie tylko opisem:

- `metahuman_body_bones.json` — 341 pose bones Body w kolejności hierarchii + mapa rodzic→dziecko
- `metahuman_face_bones.json` — 874 kości Face: 31 współdzielonych z Body + 843 `FACIAL_*`, plus mapa rodzic→dziecko
- `metahuman_face_blendshapes.json` — 858 kanałów blend shape, pogrupowane wg części siatki (head/teeth/eyeLeft/eyeRight/cartilage)
- `metahuman_body_face_merge_plan.json` — plan scalenia szkieletów w formie maszynowo czytelnej (to samo co sekcja 8.4, ale jako dane)

### 8.1 Fakty o geometrii/deformerach (potwierdzone bezpośrednio z bajtów FBX)

| | Body | Face |
|---|---|---|
| Wierzchołki | 32 334 | 34 657 |
| Trójkąty (siatka w 100% zatriangulowana u źródła) | 60 816 | 64 094 |
| Kości (Model/LimbNode+Root) | 342 (341 LimbNode + root) | 875 (874 LimbNode + root) |
| Blend shape'y | 0 | 858 (potwierdzone 1:1 kanał↔shape przez graf Connections, nie założone) |
| UV / normalne | `ByVertice`/`Direct` (1 na control point, nie per-corner) | tak samo |
| Materiały | 1 (`MI_Body_Baked_VT`) | 15 (skóra LOD0-7, zęby, oczy, rzęsy, itd.) |
| **Kość `root` skinowana własnym Clusterem** | **tak** | **tak** |

Konsekwencja dla pluginu: jeśli gdziekolwiek w kodzie zakładasz "tylko LimbNode ma wagi skinningu, root nie" — to założenie jest błędne dla tych plików i trzeba to uwzględnić przy eksporcie/imporcie (patrz checklista, sekcja 6).

### 8.2 Body i Face dzielą jeden szkielet — to jest źródło największego ryzyka w całym pipeline

Hierarchia kości Face (`FACE_full_bone_hierarchy.txt`) zaczyna się identycznie jak Body: `root → pelvis → spine_01…05 → clavicle/upperarm (obie strony) → neck_01 → neck_02 → head`. Dopiero pod `head` pojawia się `FACIAL_C_FacialRoot` i cały rig twarzy. To nie przypadek — Body i Face w MetaHumanie <cite index="52-1">dzielą ten sam MetaHuman_Base_Skeleton, a Face ma jego rozszerzenie o rig twarzy</cite>, a wspólny łańcuch jest w UE napędzany przez **Set Leader Pose Component** na Face wskazujący na Body — <cite index="50-1">co wystarcza do podstawowego współdzielenia animacji ciała, ale nie do animacji twarzy, którą trzeba prowadzić osobnym pipeline'em (Live Link / Control Rig).</cite>

Historyczne potwierdzenie, że to realny, a nie teoretyczny problem: na forum Epic zgłaszano dokładnie ten objaw — <cite index="34-1">twarz i ciało MetaHumana "odklejają się" od siebie przy używaniu Control Rig, jakby control rig nie wpływał na twarz.</cite> To symptom niezsynchronizowania dwóch kopii tego samego łańcucha kości.

**Dla eksportu przez USD/Sequencer jest to dodatkowo potwierdzone jako słaby punkt historycznie**: w starszym, ale wciąż pouczającym zgłoszeniu do konektora Omniverse/USD dla UE, <cite index="56-1">animacja mapy testowej MetaHumana była sterowana komponentami animacji twarzy, których ówczesny eksporter USD w ogóle nie obsługiwał.</cite> Nie zakładaj więc, że eksport blend shape'ów/animacji twarzy przez USD "po prostu zadziała" — to najbardziej niepewny element całego planu i dlatego sekcja 4.6 opisuje niezależny fallback.

### 8.3 Blend shape'y — pełna lista zweryfikowana krzyżowo, gotowa jako dane

`metahuman_face_blendshapes.json` zawiera wszystkie 858 nazw kanałów, każdy ze zweryfikowaną liczbą wierzchołków w delcie (co można wykorzystać jako dodatkowy test integralności — jeśli po eksporcie/imporcie delta ma inną liczbę wierzchołków niż w tym pliku, coś poszło nie tak). Nazwy mają prefiks części siatki (`head_lod0_mesh__`, `teeth_lod0_mesh__`, `eyeLeft_lod0_mesh__`, `eyeRight_lod0_mesh__`, `cartilage_lod0_mesh__`) mimo że to jedna połączona geometria w FBX — wygodne do grupowania w UI Blendera (np. zakładki "Twarz / Zęby / Oczy" w panelu shape keys).

### 8.4 Plan scalenia szkieletów Body + Face (implementacja: sekcja 5.5)

1. Zaimportuj Body — to jest **prawda referencyjna** dla wspólnego łańcucha kości (bo w UE steruje nim Leader Pose Component).
2. Z Face weź **tylko** podrzewo `FACIAL_C_FacialRoot` (843 kości) — to jest w `metahuman_face_bones.json → facial_only_bones`.
3. Odetnij `FACIAL_C_FacialRoot` od jego zdublowanej kopii `head` w Face i podepnij pod prawdziwy `head` z Body.
4. Usuń pozostałe 31 zdublowanych kości Face (`metahuman_face_bones.json → shared_bones_with_body`).
5. Podmień modifier Armature na mesh'u Face, żeby wskazywał na połączony Armature z Body — grupy wierzchołków już mają poprawne nazwy kości (bo to te same stringi), więc nie trzeba remapować nazw, tylko obiekt docelowy.
6. Zwaliduj: kość `root` (8.1) i jej wpływ na skinning w obu meshach.

To jest jednocześnie plan implementacyjny dla `metahuman_merge.py` (sekcja 5.5) i przepis na test w Fazie 5 planu wdrożenia (sekcja 7).

---

## Otwarte pytania do zweryfikowania podczas implementacji (nie do rozstrzygnięcia z dokumentacji na sucho)

1. Dokładna nazwa/sygnatura funkcji eksportu USD z poziomu Pythona w 5.8 (API `unreal.LevelSequenceExporterUsdOptions` + towarzysząca funkcja eksportu zmieniała nazwę/lokalizację między wersjami 5.x) — sprawdzić w edytorze przez `help(unreal.SequencerTools)` / `help(unreal)` i w Output Log.
2. Czy blend shape'y MetaHumana faktycznie trafiają do USD BlendShapes przy eksporcie z poziomu Sequencera (a nie tylko przy eksporcie pojedynczego Skeletal Mesh Asset) — sekcja 8.2 pokazuje, że historycznie akurat to bywało niewspierane, więc to kluczowy test w Fazie 5, z Planem B (sekcja 4.6) gotowym na wypadek porażki.
3. Czy `import_blendshapes` to dokładna nazwa parametru `bpy.ops.wm.usd_import` w 5.0.1 — zweryfikować przez `bpy.ops.wm.usd_import.get_rna_type().properties` w konsoli Pythona Blendera przed pisaniem finalnego kodu.
4. **Czy import przez USD (a nie FBX) tworzy `root` jako prawdziwą kość armatury w Blenderze**, zamiast promować go do nazwy obiektu Armature (to udokumentowane zachowanie jest specyficzne dla importera FBX Blendera, patrz plik źródłowy pose bones — dla USD może być inaczej, bo `UsdSkel` jawnie wylicza tablicę `joints`). Ma to bezpośredni wpływ na to, czy problem ze skinowaniem `root` z sekcji 8.1 w ogóle wystąpi przy ścieżce USD.
5. Dokładna nazwa API do odczytu wagi pojedynczej krzywej morph target z `SkeletalMeshComponent` w Pythonie UE 5.8, potrzebna dla Planu B z sekcji 4.6 (`get_morph_target_curve_value` w szkielecie kodu to nazwa robocza, nie potwierdzona sygnatura).
