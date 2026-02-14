extends Node2D

const STEP_IDLE := ^"Ground/Move/IdleAi"
const STEP_WALK := ^"Ground/Move/Follow"
const STEP_HURT := ^"Ground/Hurt"
const STEP_ATTACK_AREA := ^"Ground/AttackArea"
const STEP_ATTACK_COMBO := ^"Ground/AttackCombo"
const STEP_ATTACK_DASH := ^"Ground/AttackDash"
const STEP_ATTACK_SLAP := ^"Ground/AttackRetaliate"
const STEP_KNEELED := ^"Ground/KnockoutKneeled"
const STEP_SEATED := ^"Seated"
const STEP_DIE := ^"DieAi"
const TIME_SCALE_NORMAL := 1.0
const TIME_SCALE_SLOW := 0.25
const DASH_AUTO_SUCCEED_DELAY := 0.12
const SEATED_REVEAL_SIGNAL_DELAY := 0.05
const SEATED_REVEAL_FINISH_DELAY := 2.8

@onready var _state_machine := $TaxMan/StateMachine as QuiverStateMachine
@onready var _character := $TaxMan as QuiverCharacter
@onready var _help := $CanvasLayer/Help as Label
@onready var _anim_tree := $TaxMan/Skin/AnimationTree as AnimationTree
@onready var _sprite := $TaxMan/Skin/Body as AnimatedSprite2D
@onready var _skin := $TaxMan/Skin
@onready var _seated_state := $TaxMan/StateMachine/Seated

var _auto_cycle := false
var _cycle_running := false
var _last_state := "initializing..."
var _slow_motion := false
var _start_position := Vector2.ZERO


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
		KEY_I:
			_transition_to(STEP_IDLE)
		KEY_W:
			_transition_to(STEP_WALK)
		KEY_H:
			_transition_to(STEP_HURT)
		KEY_1:
			_transition_to(STEP_ATTACK_AREA)
		KEY_2:
			_transition_to(STEP_ATTACK_COMBO)
		KEY_3:
			_preview_dash_combined()
		KEY_4:
			_transition_to(STEP_ATTACK_SLAP)
		KEY_5:
			_preview_dash_begin_only()
		KEY_6:
			_preview_dash_end_only()
		KEY_K:
			_transition_to(STEP_KNEELED)
		KEY_D:
			_transition_to(STEP_DIE)
		KEY_E:
			_preview_seated_engage()
		KEY_L:
			_preview_seated_laugh()
		KEY_R:
			_preview_seated_drink()
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
	_auto_cycle = true
	_cycle_running = true
	_run_cycle()


func _run_cycle() -> void:
	while _auto_cycle and is_inside_tree():
		_transition_to(STEP_IDLE)
		await get_tree().create_timer(0.8).timeout
		_transition_to(STEP_WALK)
		await get_tree().create_timer(1.0).timeout
		_transition_to(STEP_ATTACK_AREA)
		await get_tree().create_timer(0.8).timeout
		_transition_to(STEP_ATTACK_COMBO)
		await get_tree().create_timer(1.0).timeout
		_preview_dash_combined()
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


func _transition_to(path: NodePath, msg := {}) -> void:
	if _state_machine == null:
		push_error("Missing state machine in preview scene.")
		return
	if _state_machine.state == null:
		push_warning("State machine not ready yet.")
		return
	_reset_preview_actor()
	if path == STEP_WALK and msg.is_empty():
		msg = {"target_node": _character}
	_state_machine.transition_to(path, msg)


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
	if state_path == STEP_IDLE:
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
		"SPACE cycle | I idle(8f) | W walk(16f) | H hurt | 1 attack_area_body(34f) | 2 attack_combo(15f)\n"
		+ "3 attack_dash combined(7f+8f) | 4 attack_retaliate(4f) | 5 attack_dash_begin | 6 attack_dash_end\n"
		+ "K kneeled(1f) | D death_explosion_body(15f) | E engage | L laugh | R drink | S swirl | T 1/4 speed\n"
		+ "Dash note: keys 3/5/6 all use AttackDash state machine path (no direct skin travel).\n"
		+ "State: %s | Tree: %s | Anim: %s #%d | TimeScale: %.2f"
	) % [_last_state, tree_active, anim_name, frame, speed]


func _process(_delta: float) -> void:
	if _anim_tree != null and not _anim_tree.active:
		_anim_tree.active = true
	if Engine.get_process_frames() % 10 == 0:
		_render_help()


func _toggle_slow_motion() -> void:
	_slow_motion = not _slow_motion
	Engine.time_scale = TIME_SCALE_SLOW if _slow_motion else TIME_SCALE_NORMAL
	_render_help()


func _exit_tree() -> void:
	Engine.time_scale = TIME_SCALE_NORMAL


func _reset_preview_actor() -> void:
	if _character == null:
		return
	_character.global_position = _start_position
	_character.velocity = Vector2.ZERO


func _preview_dash_combined() -> void:
	_transition_to(STEP_ATTACK_DASH)
	var timer := get_tree().create_timer(DASH_AUTO_SUCCEED_DELAY)
	timer.timeout.connect(_emit_dash_success, CONNECT_ONE_SHOT)


func _preview_dash_begin_only() -> void:
	_transition_to(STEP_ATTACK_DASH)


func _preview_dash_end_only() -> void:
	_transition_to(STEP_ATTACK_DASH)
	var timer := get_tree().create_timer(DASH_AUTO_SUCCEED_DELAY)
	timer.timeout.connect(_emit_dash_success, CONNECT_ONE_SHOT)


func _emit_dash_success() -> void:
	if _skin == null:
		return
	if _last_state != str(STEP_ATTACK_DASH):
		return
	_skin.emit_signal("dash_attack_succeeded")


func _preview_seated_drink() -> void:
	_preview_seated_base(0, 0)
	var timer := get_tree().create_timer(SEATED_REVEAL_FINISH_DELAY)
	timer.timeout.connect(_on_seated_force_anim.bind(&"seated_drink", "Seated/Drink"), CONNECT_ONE_SHOT)


func _preview_seated_swirl() -> void:
	_preview_seated_base(8, 8)
	var timer := get_tree().create_timer(SEATED_REVEAL_FINISH_DELAY)
	timer.timeout.connect(_on_seated_force_anim.bind(&"seated_swirl", "Seated/Swirl"), CONNECT_ONE_SHOT)


func _preview_seated_laugh() -> void:
	_preview_seated_base(8, 8)
	var timer := get_tree().create_timer(SEATED_REVEAL_FINISH_DELAY)
	timer.timeout.connect(_on_seated_emit_signal.bind("tax_man_laughed", "Seated/Laugh"), CONNECT_ONE_SHOT)


func _preview_seated_engage() -> void:
	_preview_seated_base(8, 8)
	var timer := get_tree().create_timer(SEATED_REVEAL_FINISH_DELAY)
	timer.timeout.connect(_on_seated_emit_signal.bind("tax_man_engaged", "Seated/Engage"), CONNECT_ONE_SHOT)


func _preview_seated_base(swirl_min: int, swirl_max: int) -> void:
	if _seated_state != null:
		# Order matters due custom setters clamping each other.
		_seated_state.set("_swirl_min", swirl_min)
		_seated_state.set("_swirl_max", swirl_max)
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
