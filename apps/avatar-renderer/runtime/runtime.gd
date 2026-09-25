extends Node3D
## Fruit-Fly avatar runtime: loads one staged character scene, applies
## procedural idle (breath/sway/blink), polls the brain HTTP endpoint for
## validated command messages, and logs state changes. Parse/render evidence
## only — visual correctness always needs human observation.
##
## Usage: godot --path apps/avatar-renderer/runtime -- --model res://local/FurinaV2.fbx --brain http://127.0.0.1:8771

var brain_url := "http://127.0.0.1:8771"
var model_res := "res://local/FurinaV2.fbx"
var avatar: Node = null
var camera: Camera3D = null
var skeleton: Skeleton3D = null
var head_bone := -1
var blink_meshes: Array[MeshInstance3D] = []
var blink_shape := -1
var elapsed := 0.0
var poll_cooldown := 0.0
var last_seen_id := 0
var rng := RandomNumberGenerator.new()

const POLL_EVERY_S := 0.5
const SWAY_RAD := 0.03
const BREATH_HZ := 0.25


func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--model="):
			model_res = arg.trim_prefix("--model=")
		elif arg.begins_with("--brain="):
			brain_url = arg.trim_prefix("--brain=")
	if not (model_res.begins_with("res://local/") and model_res.to_lower().ends_with(".fbx")):
		push_error("FF_RUNTIME REJECTED model (must be res://local/*.fbx)")
		model_res = ""
	if not brain_url.begins_with("http://127.0.0.1:") and brain_url != "http://localhost:8771":
		push_warning("FF_RUNTIME non-loopback brain ignored")
		brain_url = "http://127.0.0.1:8771"
	rng.randomize()
	_load_model()
	_frame_model()
	print("FF_RUNTIME ready model=", model_res, " brain=", brain_url)


func _load_model() -> void:
	if model_res.is_empty():
		push_error("FF_RUNTIME LOAD_FAILED: no valid model")
		return
	var resource := ResourceLoader.load(model_res)
	if not (resource is PackedScene):
		push_error("FF_RUNTIME LOAD_FAILED: " + model_res)
		return
	avatar = (resource as PackedScene).instantiate()
	add_child(avatar)
	var pending: Array[Node] = [avatar]
	while not pending.is_empty():
		var node: Node = pending.pop_back()
		for child in node.get_children():
			pending.push_back(child)
		if node is Skeleton3D and skeleton == null:
			skeleton = node as Skeleton3D
			head_bone = skeleton.find_bone("Head")
		if node is MeshInstance3D:
			var mesh: Mesh = (node as MeshInstance3D).mesh
			if mesh != null:
				for i in mesh.get_blend_shape_count():
					if str(mesh.get_blend_shape_name(i)) == "まばたき":
						blink_meshes.append(node as MeshInstance3D)
						blink_shape = i
	print("FF_RUNTIME loaded skeleton=", skeleton != null, " head_bone=", head_bone,
		" blink_targets=", blink_meshes.size())


func _frame_model() -> void:
	camera = get_node_or_null("Camera3D") as Camera3D
	if camera == null or avatar == null:
		return
	var bounds := AABB()
	var found := false
	var pending: Array[Node] = [avatar]
	while not pending.is_empty():
		var node: Node = pending.pop_back()
		for child in node.get_children():
			pending.push_back(child)
		if node is MeshInstance3D:
			var box: AABB = (node as MeshInstance3D).get_aabb()
			if not found:
				bounds = box
				found = true
			else:
				bounds = bounds.merge(box)
	if not found or bounds.size.length() < 0.01:
		push_warning("FF_RUNTIME FRAME_FAILED: no visible bounds")
		return
	var center := bounds.get_center()
	var span := maxf(maxf(bounds.size.x, bounds.size.y), bounds.size.z)
	var dist := (span / (2.0 * tan(deg_to_rad(camera.fov * 0.5)))) * 1.3
	camera.position = center + Vector3(span * 0.2, span * 0.08, dist)
	camera.look_at(center)
	print("FF_RUNTIME framed center=", center, " span=", snappedf(span, 0.001))


func _process(delta: float) -> void:
	elapsed += delta
	_apply_idle()
	poll_cooldown -= delta
	if poll_cooldown <= 0.0:
		poll_cooldown = POLL_EVERY_S
		_poll_brain()


func _apply_idle() -> void:
	if skeleton != null and head_bone >= 0:
		var sway := SWAY_RAD * sin(TAU * BREATH_HZ * elapsed * 0.5)
		var nod := 0.5 * SWAY_RAD * sin(TAU * BREATH_HZ * elapsed)
		skeleton.set_bone_pose_rotation(head_bone, Quaternion(Vector3.UP, sway) * Quaternion(Vector3.RIGHT, nod))
	var blink_phase := fmod(elapsed, 4.0) / 4.0
	var blink := 1.0 - clampf(abs(blink_phase - 0.5) * 20.0, 0.0, 1.0)
	for mesh_instance in blink_meshes:
		mesh_instance.set_blend_shape_value(blink_shape, blink)


func _poll_brain() -> void:
	var request := HTTPRequest.new()
	add_child(request)
	request.request_completed.connect(_on_commands.bind(request))
	var err := request.request(brain_url + "/commands?since=" + str(last_seen_id))
	if err != OK:
		request.queue_free()


func _on_commands(_result: int, code: int, _headers: PackedStringArray, body: PackedByteArray, request: Node) -> void:
	request.queue_free()
	if code != 200:
		return
	if body.size() > 65536:
		push_warning("FF_RUNTIME oversized command body ignored")
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	for cmd in parsed.get("commands", []):
		if typeof(cmd) != TYPE_DICTIONARY or typeof(cmd.get("type", "")) != TYPE_STRING:
			continue
		last_seen_id = maxi(last_seen_id, int(cmd.get("id", last_seen_id)))
		_apply_command(cmd)


func _apply_command(cmd: Dictionary) -> void:
	match cmd.get("type", ""):
		"avatar.expression":
			print("FF_RUNTIME expression=", cmd.get("expression"), " intensity=", cmd.get("intensity", 0.7))
		"avatar.animation.play":
			print("FF_RUNTIME animation.play name=", cmd.get("name"), " (no clips: procedural idle continues)")
		"avatar.look_at":
			print("FF_RUNTIME look_at x=", cmd.get("x"), " y=", cmd.get("y"))
		_:
			print("FF_RUNTIME ignored type=", cmd.get("type"))
