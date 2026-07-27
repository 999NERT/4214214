import bpy


def create_metahuman_merge_collection(collection_name: str) -> bpy.types.Collection:
    existing = bpy.data.collections.get(collection_name)
    if existing:
        return existing
    return bpy.data.collections.new(collection_name)


def move_objects_to_collection(objects, collection: bpy.types.Collection) -> None:
    for obj in objects:
        for parent_col in obj.users_collection[:]:
            parent_col.objects.unlink(obj)
        collection.objects.link(obj)


def import_usd_actor_metadata(manifest: dict, parent_collection: bpy.types.Collection) -> None:
    if not manifest:
        return
    actors = manifest.get("actors", [])
    if not actors:
        return
    for actor_meta in actors:
        name = actor_meta.get("name") or actor_meta.get("actor_name") or "metahuman_actor"
        actor_collection = bpy.data.collections.new(name)
        parent_collection.children.link(actor_collection)
        body_skeleton = actor_meta.get("body_skeleton")
        face_skeleton = actor_meta.get("face_skeleton")
        if body_skeleton:
            body_collection = bpy.data.collections.new(f"{name}_body")
            actor_collection.children.link(body_collection)
            body_collection["metahuman_body_skeleton"] = body_skeleton
        if face_skeleton:
            face_collection = bpy.data.collections.new(f"{name}_face")
            actor_collection.children.link(face_collection)
            face_collection["metahuman_face_skeleton"] = face_skeleton


def apply_metahuman_merge(manifest: dict, target_collection: bpy.types.Collection) -> None:
    actors = manifest.get("actors", [])
    if not actors:
        return
    for actor_meta in actors:
        actor_name = actor_meta.get("actor_name") or actor_meta.get("name")
        if not actor_name:
            continue
        body_name = actor_meta.get("body_skeleton")
        face_name = actor_meta.get("face_skeleton")
        if not body_name or not face_name:
            components = actor_meta.get("components", [])
            body_name = body_name or next((comp.get("name") for comp in components if comp.get("role") == "body"), None)
            face_name = face_name or next((comp.get("name") for comp in components if comp.get("role") == "face"), None)

        body_obj = bpy.data.objects.get(body_name) if body_name else None
        face_obj = bpy.data.objects.get(face_name) if face_name else None
        if body_obj and face_obj:
            merged_name = f"{actor_name}_merged"
            merged_collection = bpy.data.collections.new(merged_name)
            if merged_collection.name not in [c.name for c in target_collection.children]:
                target_collection.children.link(merged_collection)
            if body_obj.name not in merged_collection.objects:
                merged_collection.objects.link(body_obj)
            if face_obj.name not in merged_collection.objects:
                merged_collection.objects.link(face_obj)
            # Keep existing transform linkage by leaving original objects in place.
        elif body_obj or face_obj:
            if body_obj and body_obj.name not in target_collection.objects:
                target_collection.objects.link(body_obj)
            if face_obj and face_obj.name not in target_collection.objects:
                target_collection.objects.link(face_obj)
