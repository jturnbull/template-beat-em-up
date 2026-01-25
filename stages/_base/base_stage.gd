class_name BaseStage
extends Node2D

## Class that is the base script for all stages. Connects the player attributes to the hud and 
## handles game over.

### Member Variables and Dependencies -------------------------------------------------------------
#--- signals --------------------------------------------------------------------------------------

#--- enums ----------------------------------------------------------------------------------------

#--- constants ------------------------------------------------------------------------------------

#--- public variables - order: export > normal var > onready --------------------------------------

#--- private variables - order: export > normal var > onready -------------------------------------

@onready var _player_one := $Level/Characters/Chad as QuiverCharacter
@onready var _player_two := $Level/Characters/Player2 as QuiverCharacter
@onready var _player_hud := $HudLayer/PlayerHud
@onready var _player_two_hud := $HudLayer/PlayerHudP2
@onready var _end_screen := $HudLayer/EndScreen as EndScreen
@onready var _camera := $Level/Characters/Chad/LevelCamera as Camera2D

### -----------------------------------------------------------------------------------------------


### Built in Engine Methods -----------------------------------------------------------------------

func _ready() -> void:
	randomize()
	if is_instance_valid(_player_one):
		_player_hud.set_player_attributes(_player_one.attributes)
	
	if is_instance_valid(_player_two):
		_player_two_hud.set_player_attributes(_player_two.attributes)
	else:
		_player_two_hud.visible = false
	QuiverEditorHelper.connect_between(Events.player_died, _on_Events_player_died)


func _unhandled_input(event: InputEvent) -> void:
	if OS.has_feature("debug") and event.is_action_pressed("debug_restart"):
		reload_prototype()

func _physics_process(_delta: float) -> void:
	_limit_player_separation()

### -----------------------------------------------------------------------------------------------


### Public Methods --------------------------------------------------------------------------------

## Properly resets all characters and reloads game scene.
func reload_prototype() -> void:
	Events.characters_reseted.emit()
	var error := get_tree().reload_current_scene()
	if error != OK:
		push_error("Failed to reload current scene. Error %s"%[error])

### -----------------------------------------------------------------------------------------------


### Private Methods -------------------------------------------------------------------------------

func _on_Events_player_died() -> void:
	var players := get_tree().get_nodes_in_group("players")
	for node in players:
		var player := node as QuiverCharacter
		if player != null and player.attributes != null and player.attributes.is_alive():
			return
	_end_screen.open_end_screen(false)


func _limit_player_separation() -> void:
	if _camera == null:
		return
	
	var viewport_size := get_viewport_rect().size
	var zoom := _camera.zoom
	if zoom.x == 0.0 or zoom.y == 0.0:
		return
	
	var players := get_tree().get_nodes_in_group("players")
	if players.size() < 2:
		return
	
	var p1 := players[0] as Node2D
	var p2 := players[1] as Node2D
	if p1 == null or p2 == null:
		return
	
	var max_separation := viewport_size.x / zoom.x
	var left := p1
	var right := p2
	if p1.global_position.x > p2.global_position.x:
		left = p2
		right = p1
	
	if right.global_position.x - left.global_position.x > max_separation:
		var pos := right.global_position
		pos.x = left.global_position.x + max_separation
		right.global_position = pos

### -----------------------------------------------------------------------------------------------
