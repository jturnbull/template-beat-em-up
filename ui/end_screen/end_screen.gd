class_name EndScreen
extends Control

## Write your doc string for this file here

### Member Variables and Dependencies -------------------------------------------------------------
#--- signals --------------------------------------------------------------------------------------

#--- enums ----------------------------------------------------------------------------------------

#--- constants ------------------------------------------------------------------------------------

const TITLE_GAMEOVER = "GAME OVER!"
const TITLE_VICTORY = "CONGRATULATIONS!"

#--- public variables - order: export > normal var > onready --------------------------------------

@export var victory_leaderboard_delay := 2.0
@export var gameover_leaderboard_delay := 0.0

#--- private variables - order: export > normal var > onready -------------------------------------

@onready var _title := $PanelContainer/Control/Title as Label
@onready var _animator := $AnimationPlayer as AnimationPlayer
@onready var _buttons := $PanelContainer/Buttons as VBoxContainer
@onready var _replay_button := $PanelContainer/Buttons/MarginContainer/Replay as TextureButton
@onready var _leaderboard := $Leaderboard as Leaderboard
var _leaderboard_timer: Timer

### -----------------------------------------------------------------------------------------------


### Built in Engine Methods -----------------------------------------------------------------------

func _ready() -> void:
	if QuiverEditorHelper.is_standalone_run(self):
		var is_victory = randi() % 2 as bool
		_title.text = TITLE_VICTORY if is_victory else TITLE_GAMEOVER
		_animator.play("open")
	_start_leaderboard_timer(0.5)
	_leaderboard.entry_flow_finished.connect(_on_leaderboard_finished)
	_setup_leaderboard_timer()

### -----------------------------------------------------------------------------------------------


### Public Methods --------------------------------------------------------------------------------

func open_end_screen(is_victory: bool) -> void:
	if is_inside_tree():
		var tree := Engine.get_main_loop() as SceneTree
		if tree != null:
			tree.paused = true
		_title.text = TITLE_VICTORY if is_victory else TITLE_GAMEOVER
		_animator.play("open")
		_buttons.visible = false
		var delay := victory_leaderboard_delay if is_victory else gameover_leaderboard_delay
		_start_leaderboard_timer(delay)

### -----------------------------------------------------------------------------------------------


### Private Methods -------------------------------------------------------------------------------

func _on_replay_pressed() -> void:
	if not is_inside_tree():
		return
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return
	Events.characters_reseted.emit()
	var error := tree.reload_current_scene()
	if error == OK:
		tree.paused = false
	else:
		push_error("Failed to reload current scene. Error %s"%[error])


func _on_quit_pressed() -> void:
	if not is_inside_tree():
		return
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return
	tree.quit()


func _show_leaderboard_entry() -> void:
	_buttons.visible = false
	_leaderboard.visible = true
	_leaderboard.start_entry_flow()


func _on_leaderboard_finished() -> void:
	_buttons.visible = true
	_replay_button.grab_focus()


func _setup_leaderboard_timer() -> void:
	_leaderboard_timer = Timer.new()
	_leaderboard_timer.one_shot = true
	add_child(_leaderboard_timer)
	_leaderboard_timer.timeout.connect(_show_leaderboard_entry)


func _start_leaderboard_timer(delay_seconds: float) -> void:
	if _leaderboard_timer == null:
		_setup_leaderboard_timer()
	if delay_seconds <= 0.0:
		_show_leaderboard_entry()
		return
	_leaderboard_timer.stop()
	_leaderboard_timer.wait_time = delay_seconds
	_leaderboard_timer.start()

### -----------------------------------------------------------------------------------------------
