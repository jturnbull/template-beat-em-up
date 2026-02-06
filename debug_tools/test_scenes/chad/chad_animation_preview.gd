extends Node2D

const STEP_IDLE := ^"Ground/Move/Idle"
const STEP_WALK := ^"Ground/Move/Walk"
const STEP_HURT := ^"Ground/Hurt"
const STEP_COMBO_1 := ^"Ground/Combo1"
const STEP_COMBO_2 := ^"Ground/Combo2"
const STEP_COMBO_3 := ^"Ground/Combo3"
const STEP_JUMP := ^"Air/Jump/Impulse"
const STEP_AIR_ATTACK := ^"Air/Jump/Attack"
const STEP_KO := ^"Air/Knockout/Launch"
const STEP_DIE := ^"Die"
const KO_LAUNCH_VECTOR := Vector2(1.0, -0.9)
const KO_PREVIEW_KNOCKBACK := 1200.0
const TIME_SCALE_NORMAL := 1.0
const TIME_SCALE_SLOW := 0.25

@onready var _state_machine := $Chad/StateMachine as QuiverStateMachine
@onready var _character := $Chad as QuiverCharacter
@onready var _help := $CanvasLayer/Help as Label
@onready var _anim_tree := $Chad/ChadSkin/AnimationTree as AnimationTree
@onready var _sprite := $Chad/ChadSkin/AnimatedSprite2D as AnimatedSprite2D

var _auto_cycle := false
var _cycle_running := false
var _last_state := "initializing..."
var _slow_motion := false


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
			_transition_to(STEP_COMBO_1)
		KEY_2:
			_transition_to(STEP_COMBO_2)
		KEY_3:
			_transition_to(STEP_COMBO_3)
		KEY_J:
			_transition_to(STEP_JUMP)
		KEY_A:
			_transition_to(STEP_AIR_ATTACK)
		KEY_K:
			_trigger_knockout()
		KEY_D:
			_transition_to(STEP_DIE)
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
		_transition_to(STEP_COMBO_1)
		await get_tree().create_timer(0.6).timeout
		_transition_to(STEP_COMBO_2)
		await get_tree().create_timer(0.6).timeout
		_transition_to(STEP_COMBO_3)
		await get_tree().create_timer(0.8).timeout
		_transition_to(STEP_HURT)
		await get_tree().create_timer(0.6).timeout
		_transition_to(STEP_JUMP)
		await get_tree().create_timer(0.8).timeout
		_transition_to(STEP_AIR_ATTACK)
		await get_tree().create_timer(0.9).timeout
		_trigger_knockout()
		await get_tree().create_timer(2.2).timeout
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
	_set_walk_input(path == STEP_WALK)
	_state_machine.transition_to(path, msg)


func _trigger_knockout() -> void:
	if _character == null or _character.attributes == null:
		push_error("Missing character attributes in preview scene.")
		return
	_character.attributes.knockback_amount = KO_PREVIEW_KNOCKBACK
	_transition_to(STEP_KO, {"launch_vector": KO_LAUNCH_VECTOR.normalized()})


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
	_help.text = "SPACE start/stop cycle | I idle | W walk | H hurt | 1/2/3 combos | J jump | A air attack | K knockout | D die | T 1/4 speed\nState: %s | Tree: %s | Anim: %s #%d | TimeScale: %.2f" % [_last_state, tree_active, anim_name, frame, speed]


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
	_set_walk_input(false)
	Engine.time_scale = TIME_SCALE_NORMAL


func _walk_action_name() -> StringName:
	if _character != null:
		var scoped_action := _character.get_input_action(&"move_right")
		if InputMap.has_action(scoped_action):
			return scoped_action
	if InputMap.has_action(&"move_right"):
		return &"move_right"
	return StringName("")


func _set_walk_input(enabled: bool) -> void:
	var action := _walk_action_name()
	if action.is_empty():
		return
	if enabled:
		Input.action_press(action)
	else:
		Input.action_release(action)
