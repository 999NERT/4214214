import unreal


def is_metahuman_actor(actor: unreal.Actor) -> bool:
    """Detect a MetaHuman actor by the presence of Body and Face skeletal mesh components."""
    skeletal_components = actor.get_components_by_class(unreal.SkeletalMeshComponent)
    names = [component.get_name().lower() for component in skeletal_components]
    return "body" in names and "face" in names


def describe_metahuman(actor: unreal.Actor, reference_data: dict) -> dict:
    """Return MetaHuman-specific manifest metadata for the actor."""
    result = {
        "actor_name": actor.get_name(),
        "type": "metahuman",
        "has_body": True,
        "has_face": True,
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
