extends Node2D

const STEP_IDLE := ^"Ground/Move/IdleAi"
const STEP_WALK := ^"Ground/Move/Follow"
const STEP_HURT := ^"Ground/Hurt"
const STEP_ATTACK_AREA := ^"Ground/AttackArea"
const STEP_ATTACK_COMBO := ^"Ground/AttackCombo"
const STEP_ATTACK_SLAP := ^"Ground/AttackRetaliate"
const STEP_KNEELED := ^"Ground/KnockoutKneeled"
const STEP_SEATED := ^"Seated"
const STEP_DIE := ^"DieAi"
const TIME_SCALE_NORMAL := 1.0
const TIME_SCALE_SLOW := 0.25
const SEATED_REVEAL_SIGNAL_DELAY := 0.05
const SEATED_REVEAL_FINISH_DELAY := 0.35
const CONTROL_MOVE_SPEED := 900.0
const WALK_PREVIEW_DISTANCE := 260.0

@onready var _state_machine := $TaxMan/StateMachine as QuiverStateMachine
@onready var _character := $TaxMan as QuiverCharacter
@onready var _help := $CanvasLayer/Help as Label
@onready var _anim_tree := $TaxMan/Skin/AnimationTree as AnimationTree
@onready var _sprite := $TaxMan/Skin/Body as AnimatedSprite2D
@onready var _skin := $TaxMan/Skin

var _auto_cycle := false
var _cycle_running := false
var _last_state := "initializing..."
var _slow_motion := false
var _start_position := Vector2.ZERO
var _control_enabled := false
var _control_walking := false
var _control_target: Marker2D = null


func _ready() -> void:
	if Engine.is_editor_hint():
		return
	Engine.time_scale = TIME_SCALE_NORMAL
	set_process(true)
	_render_help()
	await _await_state_machine_ready()
	if _state_machine != null:
		# Preview scene owns keyboard input.
		_state_machine.should_process_input = false
		_state_machine.transitioned.connect(_on_state_transitioned)
	if _character != null:
		_start_position = _character.global_position
	_control_target = Marker2D.new()
	_control_target.name = "ControlTarget"
	add_child(_control_target)
	_control_target.global_position = _start_position
	_transition_to(STEP_IDLE)


func _input(event: InputEvent) -> void:
	if not (event is InputEventKey):
		return
	if not event.pressed or event.echo:
		return

	var handled := true
	match event.keycode:
		KEY_SPACE:
			_auto_cycle = not _auto_cycle
			if _auto_cycle:
				_start_cycle()
		KEY_C:
			_toggle_control_mode()
		KEY_I:
			_transition_to(STEP_IDLE)
		KEY_W:
			_transition_to(STEP_WALK)
		KEY_Y:
			_preview_turn()
		KEY_H:
			_transition_to(STEP_HURT)
		KEY_7:
			_preview_hurt_skin(&"hurt_light", "Preview/HurtLight")
		KEY_8:
			_preview_hurt_skin(&"hurt_medium", "Preview/HurtMedium")
		KEY_9:
			_preview_hurt_skin(&"hurt_knockout", "Preview/HurtKnockout")
		KEY_1:
			_transition_to(STEP_ATTACK_AREA)
		KEY_2:
			_transition_to(STEP_ATTACK_COMBO)
		KEY_4:
			_transition_to(STEP_ATTACK_SLAP)
		KEY_K:
			_transition_to(STEP_KNEELED)
		KEY_D:
			_transition_to(STEP_DIE)
		KEY_E:
			_preview_seated_engage()
		KEY_R:
			_preview_seated_reveal()
		KEY_S:
			_preview_seated_swirl()
		KEY_T:
			_toggle_slow_motion()
		_:
			handled = false

	if handled:
		get_viewport().set_input_as_handled()


func _start_cycle() -> void:
	if _cycle_running:
		return
	_control_enabled = false
	_control_walking = false
	_auto_cycle = true
	_cycle_running = true
	_run_cycle()


func _run_cycle() -> void:
	while _auto_cycle and is_inside_tree():
		_transition_to(STEP_IDLE)
		await get_tree().create_timer(0.8).timeout
		_transition_to(STEP_WALK)
		await get_tree().create_timer(1.0).timeout
		_preview_turn()
		await get_tree().create_timer(0.8).timeout
		_transition_to(STEP_ATTACK_AREA)
		await get_tree().create_timer(0.8).timeout
		_transition_to(STEP_ATTACK_COMBO)
		await get_tree().create_timer(1.0).timeout
		_transition_to(STEP_ATTACK_SLAP)
		await get_tree().create_timer(0.9).timeout
		_transition_to(STEP_HURT)
		await get_tree().create_timer(0.9).timeout
		_transition_to(STEP_KNEELED)
		await get_tree().create_timer(1.2).timeout
		_transition_to(STEP_DIE)
		await get_tree().create_timer(0.8).timeout

	_cycle_running = false


func _transition_to(path: NodePath, msg := {}, reset_actor := true) -> void:
	if _state_machine == null:
		push_error("Missing state machine in preview scene.")
		return
	if _state_machine.state == null:
		push_warning("State machine not ready yet.")
		return
	if reset_actor:
		_reset_preview_actor()
	if path == STEP_WALK and msg.is_empty():
		if _control_target == null or _character == null:
			push_error("Missing control target for walk preview.")
			return
		var direction := 1.0
		if _skin != null:
			direction = float(_skin.skin_direction)
			if direction == 0.0:
				direction = 1.0
		_control_target.global_position = _character.global_position + Vector2(direction * WALK_PREVIEW_DISTANCE, 0.0)
		msg = {"target_node": _control_target}
	_state_machine.transition_to(path, msg)
	if path != STEP_WALK:
		_control_walking = false


func _await_state_machine_ready(max_frames := 120) -> void:
	var frames := 0
	while is_inside_tree() and (_state_machine == null or _state_machine.state == null) and frames < max_frames:
		frames += 1
		await get_tree().process_frame
	if _state_machine == null or _state_machine.state == null:
		_last_state = "state machine not ready"
		_render_help()
		push_warning("Preview state machine did not initialize in time.")


func _on_state_transitioned(state_path: NodePath) -> void:
	_last_state = str(state_path)
	if state_path == STEP_IDLE and not _control_enabled:
		_reset_preview_actor()
	_render_help()


func _render_help() -> void:
	var tree_active := false
	var anim_name := "n/a"
	var frame := -1
	var speed := Engine.time_scale
	if _anim_tree != null:
		tree_active = _anim_tree.active
	if _sprite != null:
		anim_name = str(_sprite.animation)
		frame = _sprite.frame
	_help.text = (
		"SPACE cycle | C control mode | Arrows move (control mode) | I idle(8f) | W walk(16f) | Y turn(3f)\n"
		+ "H gameplay hurt | 7 hurt_light | 8 hurt_medium | 9 hurt_knockout | 1 attack_area_body(33f) | 2 attack_combo(15f)\n"
		+ "4 attack_retaliate(4f)\n"
		+ "K kneeled(1f) | D death_explosion_body(15f) | R seated reveal(1f) | S seated swirl(7f) | E seated engage(24f) | T 1/4 speed\n"
		+ "Rush / dash attack is disabled for Snakeoil in gameplay AI.\n"
		+ "State: %s | Tree: %s | Anim: %s #%d | TimeScale: %.2f | Control: %s"
	) % [_last_state, tree_active, anim_name, frame, speed, _control_enabled]


func _process(_delta: float) -> void:
	if _anim_tree != null and not _anim_tree.active:
		_anim_tree.active = true
	if Engine.get_process_frames() % 10 == 0:
		_render_help()


func _physics_process(delta: float) -> void:
	if not _control_enabled:
		return
	if _state_machine == null or _state_machine.state == null:
		return
	if _character == null or _control_target == null:
		return

	var direction := _control_vector()
	if direction == Vector2.ZERO:
		if _control_walking:
			_transition_to(STEP_IDLE, {}, false)
			_control_walking = false
		return

	_control_target.global_position += direction * CONTROL_MOVE_SPEED * delta
	if not _control_walking:
		_transition_to(STEP_WALK, {"target_node": _control_target}, false)
		_control_walking = true


func _toggle_slow_motion() -> void:
	_slow_motion = not _slow_motion
	Engine.time_scale = TIME_SCALE_SLOW if _slow_motion else TIME_SCALE_NORMAL
	_render_help()


func _exit_tree() -> void:
	_control_enabled = false
	_control_walking = false
	Engine.time_scale = TIME_SCALE_NORMAL


func _reset_preview_actor() -> void:
	if _character == null:
		return
	_character.global_position = _start_position
	_character.velocity = Vector2.ZERO
	if _control_target != null:
		_control_target.global_position = _start_position
	_control_walking = false


func _preview_turn() -> void:
	if _skin == null:
		return
	if not _control_enabled:
		_reset_preview_actor()
	# Force a facing flip, then play the explicit turn animation clip for frame-accurate preview.
	_skin.skin_direction = -1 if _skin.skin_direction > 0 else 1
	_skin.transition_to(&"turn")
	_last_state = "Preview/Turn"
	_render_help()


func _preview_hurt_skin(anim_name: StringName, label: String) -> void:
	if _skin == null:
		return
	if not _control_enabled:
		_reset_preview_actor()
	_force_skin_transition(anim_name)
	_last_state = label
	_render_help()


func _preview_seated_reveal() -> void:
	_preview_seated_base()


func _preview_seated_swirl() -> void:
	_preview_seated_base()
	var timer := get_tree().create_timer(SEATED_REVEAL_FINISH_DELAY)
	timer.timeout.connect(_on_seated_force_anim.bind(&"seated_swirl", "Seated/Swirl"), CONNECT_ONE_SHOT)


func _preview_seated_engage() -> void:
	_preview_seated_base()
	var timer := get_tree().create_timer(SEATED_REVEAL_FINISH_DELAY)
	timer.timeout.connect(_on_seated_emit_signal.bind("tax_man_engaged", "Seated/Engage"), CONNECT_ONE_SHOT)


func _preview_seated_base() -> void:
	_transition_to(STEP_SEATED)
	var timer := get_tree().create_timer(SEATED_REVEAL_SIGNAL_DELAY)
	timer.timeout.connect(func() -> void: _emit_taxman_signal("tax_man_revealed"), CONNECT_ONE_SHOT)


func _emit_taxman_signal(signal_name: String) -> void:
	if _character == null:
		return
	if not _character.has_signal(signal_name):
		return
	_character.emit_signal(signal_name)


func _force_skin_transition(anim_name: StringName) -> void:
	if _skin == null:
		return
	if not _skin.has_method("transition_to"):
		return
	_skin.transition_to(anim_name)


func _on_seated_force_anim(anim_name: StringName, label: String) -> void:
	_force_skin_transition(anim_name)
	_last_state = label
	_render_help()


func _on_seated_emit_signal(signal_name: String, label: String) -> void:
	_emit_taxman_signal(signal_name)
	_last_state = label
	_render_help()


func _toggle_control_mode() -> void:
	_control_enabled = not _control_enabled
	_auto_cycle = false
	if _control_target != null and _character != null:
		_control_target.global_position = _character.global_position
	if _control_enabled:
		_transition_to(STEP_IDLE, {}, false)
		_last_state = "Control/Enabled"
	else:
		if _control_walking:
			_transition_to(STEP_IDLE, {}, false)
		_control_walking = false
		_last_state = "Control/Disabled"
	_render_help()


func _control_vector() -> Vector2:
	var value := Vector2.ZERO
	if Input.is_physical_key_pressed(KEY_LEFT):
		value.x -= 1.0
	if Input.is_physical_key_pressed(KEY_RIGHT):
		value.x += 1.0
	if Input.is_physical_key_pressed(KEY_UP):
		value.y -= 1.0
	if Input.is_physical_key_pressed(KEY_DOWN):
		value.y += 1.0
	if value == Vector2.ZERO:
		return value
	return value.normalized()
