extends SceneTree
## Read-only importer inspection: run AFTER `godot --headless --path ... --import`.
## Parsing a scene cannot establish visual quality or humanoid correctness.

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1 or not args[0].begins_with("res://local/") or not args[0].to_lower().ends_with(".fbx"):
		printerr("Usage: godot --headless --path <probe/godot> --script res://probe.gd -- res://local/<model.fbx>")
		quit(2)
		return
	var resource := ResourceLoader.load(args[0])
	if not resource is PackedScene:
		printerr("FF02_IMPORT_FAILED: Could not load imported PackedScene: ", args[0])
		quit(1)
		return
	var root := (resource as PackedScene).instantiate()
	var report := {
		"importer": "Godot " + Engine.get_version_info().get("string", "unknown") + " (scene importer)",
		"asset": args[0],
		"import_status": "parsed",
		"imported_mesh_instances": 0,
		"imported_surface_materials": 0,
		"imported_skeletons": [],
		"imported_morph_names": [],
		"imported_clips": [],
		"note": "Parse evidence only; texture fidelity, bone mapping, animation quality, facial/eye control, physics, FPS and Wayland overlay remain untested."
	}
	var pending: Array[Node] = [root]
	while not pending.is_empty():
		var node: Node = pending.pop_back()
		for child in node.get_children():
			pending.push_back(child)
		if node is MeshInstance3D:
			report["imported_mesh_instances"] += 1
			var mesh: Mesh = (node as MeshInstance3D).mesh
			if mesh != null:
				for surface in mesh.get_surface_count():
					if (node as MeshInstance3D).get_active_material(surface) != null:
						report["imported_surface_materials"] += 1
				for shape in mesh.get_blend_shape_count():
					report["imported_morph_names"].append(str(mesh.get_blend_shape_name(shape)))
		elif node is Skeleton3D:
			var skeleton := node as Skeleton3D
			var bone_names: Array[String] = []
			for bone in skeleton.get_bone_count():
				bone_names.append(skeleton.get_bone_name(bone))
			report["imported_skeletons"].append({"name": skeleton.name, "bone_names": bone_names})
		elif node is AnimationPlayer:
			var player := node as AnimationPlayer
			for name in player.get_animation_list():
				var clip: Animation = player.get_animation(name)
				report["imported_clips"].append({"name": name, "duration_s": clip.length, "tracks": clip.get_track_count()})
	print("FF02_RESULT ", JSON.stringify(report))
	root.free()
	quit(0)
