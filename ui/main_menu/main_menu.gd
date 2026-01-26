extends Control

## Write your doc string for this file here

### Member Variables and Dependencies -------------------------------------------------------------
#--- signals --------------------------------------------------------------------------------------

signal transition_started

#--- enums ----------------------------------------------------------------------------------------

#--- constants ------------------------------------------------------------------------------------

const GAMEPLAY_SCENE = "res://stages/stage_01/stage_01.tscn"

#--- public variables - order: export > normal var > onready --------------------------------------

@export var idle_delay_seconds := 6.0
@export var leaderboard_show_seconds := 6.0

#--- private variables - order: export > normal var > onready -------------------------------------

@onready var _button_how_to_play := $MenuButtons/HowToPlay as TextureButton
@onready var _button_start := $MenuButtons/Start as TextureButton
@onready var _how_to_play := $HowToPlay as HowToPlay
@onready var _animator := $AnimationPlayer as AnimationPlayer
@onready var _leaderboard := $Leaderboard as Leaderboard
@onready var _menu_buttons := $MenuButtons as Control

var _idle_timer: Timer
var _leaderboard_timer: Timer
var _idle_active := false
var _leaderboard_showing := false

### -----------------------------------------------------------------------------------------------


### Built in Engine Methods -----------------------------------------------------------------------

func _ready() -> void:
	BackgroundLoader.load_resource(GAMEPLAY_SCENE)
	ScreenTransitions.fade_out_transition()
	_button_start.grab_focus()
	_setup_idle_timers()
	_restart_idle()


func _input(event: InputEvent) -> void:
	if _animator.assigned_animation == "game_started":
		return
	if event is InputEventKey and event.pressed and not event.echo:
		_restart_idle()
	elif event is InputEventJoypadButton and event.pressed:
		_restart_idle()
	elif event is InputEventMouseButton and event.pressed:
		_restart_idle()

### -----------------------------------------------------------------------------------------------


### Public Methods --------------------------------------------------------------------------------

### -----------------------------------------------------------------------------------------------


### Private Methods -------------------------------------------------------------------------------

func _on_start_pressed() -> void:
	if _animator.assigned_animation == "game_started":
		return
	_pause_idle()
	_animator.play("game_started")
	await transition_started
	ScreenTransitions.transition_to_scene(GAMEPLAY_SCENE)


func _start_transition() -> void:
	transition_started.emit()


func _on_how_to_play_pressed() -> void:
	_pause_idle()
	_how_to_play.open_how_to_play()


func _on_quit_pressed() -> void:
	get_tree().quit()


func _on_how_to_play_how_to_play_closed() -> void:
	_button_how_to_play.grab_focus()
	_restart_idle()


func _setup_idle_timers() -> void:
	_idle_timer = Timer.new()
	_idle_timer.one_shot = true
	add_child(_idle_timer)
	_idle_timer.timeout.connect(_on_idle_timeout)

	_leaderboard_timer = Timer.new()
	_leaderboard_timer.one_shot = true
	add_child(_leaderboard_timer)
	_leaderboard_timer.timeout.connect(_on_leaderboard_timer_timeout)


func _restart_idle() -> void:
	_idle_active = false
	_leaderboard_showing = false
	if _idle_timer:
		_idle_timer.stop()
	if _leaderboard_timer:
		_leaderboard_timer.stop()
	_hide_leaderboard()
	if _idle_timer:
		_idle_timer.wait_time = idle_delay_seconds
		_idle_timer.start()


func _pause_idle() -> void:
	_idle_active = false
	if _idle_timer:
		_idle_timer.stop()
	if _leaderboard_timer:
		_leaderboard_timer.stop()
	_hide_leaderboard()


func _on_idle_timeout() -> void:
	_idle_active = true
	_show_leaderboard()


func _on_leaderboard_timer_timeout() -> void:
	if not _idle_active:
		return
	if _leaderboard_showing:
		_hide_leaderboard()
	else:
		_show_leaderboard()


func _show_leaderboard() -> void:
	_leaderboard.show_top10()
	_leaderboard.visible = true
	_menu_buttons.visible = false
	_leaderboard_showing = true
	if _leaderboard_timer:
		_leaderboard_timer.wait_time = leaderboard_show_seconds
		_leaderboard_timer.start()


func _hide_leaderboard() -> void:
	if _leaderboard:
		_leaderboard.visible = false
	if _menu_buttons:
		_menu_buttons.visible = true
	_leaderboard_showing = false
	if _idle_active and _leaderboard_timer:
		_leaderboard_timer.wait_time = leaderboard_show_seconds
		_leaderboard_timer.start()

### -----------------------------------------------------------------------------------------------
