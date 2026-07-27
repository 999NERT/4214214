import unreal


def is_metahuman_actor(actor: unreal.Actor) -> bool:
    """Detect a MetaHuman actor by the presence of Body and Face skeletal mesh components."""
    skeletal_components = actor.get_components_by_class(unreal.SkeletalMeshComponent)
    names = [component.get_name().lower() for component in skeletal_components]
    return "body" in names and "face" in names


def _get_component_bone_count(component: unreal.SkeletalMeshComponent) -> int | None:
    try:
        if hasattr(component, "get_num_bones"):
            return int(component.get_num_bones())
        skeletal_mesh = component.get_editor_property("skeletal_mesh") if hasattr(component, "get_editor_property") else getattr(component, "skeletal_mesh", None)
        if skeletal_mesh is not None and hasattr(skeletal_mesh, "skeleton"):
            skeleton = skeletal_mesh.skeleton
            if skeleton is not None and hasattr(skeleton, "get_reference_skeleton"):
                reference = skeleton.get_reference_skeleton()
                if reference is not None and hasattr(reference, "get_num"):
                    return int(reference.get_num())
    except Exception:
        pass
    return None


def _find_leader_pose_target(actor: unreal.Actor, component_name: str) -> str | None:
    for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
        name = comp.get_name().lower()
        if comp.get_name() == component_name:
            continue
        if "leader" in name or "pose" in name:
            return comp.get_name()
    return None


def describe_metahuman(actor: unreal.Actor, sequence: unreal.LevelSequence, reference_data: dict) -> dict:
    """Return MetaHuman-specific manifest metadata for the actor."""
    components = []
    has_body = False
    has_face = False
    for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
        name = component.get_name()
        role = "unknown"
        lower_name = name.lower()
        if "body" in lower_name:
            role = "body"
            has_body = True
        elif "face" in lower_name:
            role = "face"
            has_face = True

        components.append({
            "name": name,
            "role": role,
            "has_bone_animation": component_has_keyed_bone_track(component, sequence),
            "has_blendshape_animation": component_has_keyed_morph_curves(component, sequence),
            "bone_count": _get_component_bone_count(component),
            "leader_pose_component_target": _find_leader_pose_target(actor, name),
        })

    result = {
        "actor_name": actor.get_name(),
        "type": "metahuman",
        "has_body": has_body,
        "has_face": has_face,
        "components": components,
        "reference_data": reference_data,
    }
    if hasattr(actor, "get_actor_label"):
        result["actor_label"] = actor.get_actor_label()
    return result


def _track_matches_component(track, component_name: str, keywords: list[str]) -> bool:
    track_names = []
    if hasattr(track, "get_name"):
        track_names.append(track.get_name().lower())
    if hasattr(track, "get_display_name"):
        track_names.append(track.get_display_name().lower())
    key = component_name.lower()
    for track_name in track_names:
        if key in track_name and any(keyword in track_name for keyword in keywords):
            return True
    return False


def component_has_keyed_bone_track(component: unreal.SkeletalMeshComponent, sequence: unreal.LevelSequence) -> bool:
    """Check if the component has keyed bone animation in the sequence."""
    keywords = ["transform", "bone", "pose", "track", "skeleton", "control"]
    for track in sequence.get_all_tracks():
        if _track_matches_component(track, component.get_name(), keywords):
            return True
    return False


def component_has_keyed_morph_curves(component: unreal.SkeletalMeshComponent, sequence: unreal.LevelSequence) -> bool:
    """Check if the component has morph target/blendshape curves in the sequence."""
    keywords = ["morph", "blend", "shape", "curve", "weight"]
    for track in sequence.get_all_tracks():
        if _track_matches_component(track, component.get_name(), keywords):
            return True
    return False
