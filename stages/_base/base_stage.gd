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
@onready var _characters_root := $Level/Characters as Node2D

var _player_two_active := false
var _player_one_active := true
var _player_two_dead := false
var _player_two_joined := false
var _has_finished_run := false

### -----------------------------------------------------------------------------------------------


### Built in Engine Methods -----------------------------------------------------------------------

func _ready() -> void:
	randomize()
	var requested_player_count := ScoreManager.consume_requested_player_count()
	ScoreManager.start_run()
	ScoreManager.set_total_enemy_health_pool(_calculate_total_enemy_health_pool())
	if is_instance_valid(_player_one):
		_player_hud.set_player_attributes(_player_one.attributes)
		_player_hud.set_player_name(_get_player_display_name(_player_one, "Player 1"))
		_player_one.attributes.health_depleted.connect(_on_player_health_depleted.bind(_player_one))
	
	if is_instance_valid(_player_two):
		_player_two_hud.set_player_attributes(_player_two.attributes)
		_player_two_hud.set_player_name(_get_player_display_name(_player_two, "Player 2"))
		_player_two.attributes.health_depleted.connect(_on_player_health_depleted.bind(_player_two))
		_set_player_two_active(false)
		if requested_player_count == 2:
			_set_player_two_active(true)
	else:
		_player_two_hud.visible = false
	if _characters_root != null:
		_characters_root.child_entered_tree.connect(_on_characters_root_child_entered_tree)
		for child in _characters_root.get_children():
			call_deferred("_register_enemy_if_needed", child)
	QuiverEditorHelper.connect_between(Events.player_died, _on_Events_player_died)


func _unhandled_input(event: InputEvent) -> void:
	if OS.has_feature("debug") and event.is_action_pressed("debug_restart"):
		reload_prototype()
	
	if not _player_two_active and not _player_two_dead and event.is_action_pressed("p2_start"):
		_set_player_two_active(true)

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
	var p1_alive := _is_player_alive(_player_one)
	var p2_alive := _player_two_joined and _is_player_alive(_player_two)
	if p1_alive or p2_alive:
		return
	finish_run(false)


func _limit_player_separation() -> void:
	if _camera == null:
		return
	
	var viewport_size := get_viewport_rect().size
	var zoom := _camera.zoom
	if zoom.x == 0.0 or zoom.y == 0.0:
		return
	
	var alive_players := _get_alive_players()
	if alive_players.size() < 2:
		return
	
	var p1 := alive_players[0] as Node2D
	var p2 := alive_players[1] as Node2D
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


func _set_player_two_active(is_active: bool) -> void:
	if _player_two == null:
		_player_two_hud.visible = false
		return
	if is_active and _player_two_dead:
		_player_two_active = false
		_player_two_hud.visible = true
		_player_two_hud.set_player_inactive(true, "DEAD")
		return
	
	_player_two_active = is_active
	var player_two_is_dead := _player_two_dead or (_player_two.attributes != null and not _player_two.attributes.is_alive())
	_player_two_hud.visible = true
	_player_two_hud.set_player_inactive(not is_active, "DEAD" if player_two_is_dead else "PRESS START")
	
	if is_active:
		if not _player_two_joined:
			_player_two_joined = true
			ScoreManager.set_p2_joined()
		_player_two.visible = true
		_player_two.set_process(true)
		_player_two.set_physics_process(true)
		_player_two.set_process_input(true)
		_player_two.set_process_unhandled_input(true)
		_player_two.add_to_group("players")
		var collision := _player_two.get_node_or_null("Collision") as CollisionShape2D
		if collision != null:
			collision.set_deferred("disabled", false)
		if _player_two.attributes != null:
			_player_two.attributes.reset()
		if _player_one != null:
			_player_two.global_position = _player_one.global_position + Vector2(100, 0)
	else:
		_player_two.visible = player_two_is_dead
		_player_two.set_process(false)
		_player_two.set_physics_process(false)
		_player_two.set_process_input(false)
		_player_two.set_process_unhandled_input(false)
		if _player_two.is_in_group("players"):
			_player_two.remove_from_group("players")
		var collision := _player_two.get_node_or_null("Collision") as CollisionShape2D
		if collision != null:
			collision.set_deferred("disabled", true)


func _set_player_one_active(is_active: bool) -> void:
	if _player_one == null:
		return
	
	_player_one_active = is_active
	var player_one_is_dead := _player_one.attributes != null and not _player_one.attributes.is_alive()
	
	_player_one.visible = is_active or player_one_is_dead
	_player_one.set_process(is_active)
	_player_one.set_physics_process(is_active)
	_player_one.set_process_input(is_active)
	_player_one.set_process_unhandled_input(is_active)
	
	if is_active:
		_player_one.add_to_group("players")
	else:
		if _player_one.is_in_group("players"):
			_player_one.remove_from_group("players")
		var collision := _player_one.get_node_or_null("Collision") as CollisionShape2D
		if collision != null:
			collision.set_deferred("disabled", true)


func _on_player_health_depleted(player: QuiverCharacter) -> void:
	if player == _player_two:
		_player_two_dead = true
		_player_two_active = false
		_player_two_hud.visible = true
		_player_two_hud.set_player_inactive(true, "DEAD")
	elif player == _player_one:
		_player_one_active = false
		_player_hud.set_player_inactive(true, "DEAD")


func finish_run(is_victory: bool) -> void:
	if _has_finished_run:
		return
	_has_finished_run = true
	ScoreManager.finish_run(_player_one, _player_two, _player_two_joined, is_victory)
	_end_screen.open_end_screen(is_victory)


func _get_alive_players() -> Array:
	var players := get_tree().get_nodes_in_group("players")
	var alive_players: Array = []
	for node in players:
		var player := node as QuiverCharacter
		if _is_player_alive(player):
			alive_players.append(player)
	return alive_players


func _is_player_alive(player: QuiverCharacter) -> bool:
	return player != null and player.attributes != null and player.attributes.is_alive()


func _get_player_display_name(player: QuiverCharacter, fallback: String) -> String:
	if player != null and player.attributes != null and not player.attributes.display_name.is_empty():
		return player.attributes.display_name
	
	return fallback


func _on_characters_root_child_entered_tree(node: Node) -> void:
	call_deferred("_register_enemy_if_needed", node)


func _register_enemy_if_needed(node: Node) -> void:
	var enemy := node as QuiverEnemyCharacter
	if enemy == null or not enemy.is_in_group("enemies"):
		return
	ScoreManager.register_enemy(enemy)


func _calculate_total_enemy_health_pool() -> float:
	var total := 0.0
	if _characters_root != null:
		for child in _characters_root.get_children():
			if child.is_in_group("enemies"):
				var enemy := child as QuiverEnemyCharacter
				if enemy == null or enemy.attributes == null:
					push_error("Initial enemy missing attributes: %s" % child)
					continue
				total += float(enemy.attributes.health_max)

	for spawner_node in find_children("*", "QuiverEnemySpawner", true, false):
		var spawn_waves = spawner_node.get("spawn_waves")
		if typeof(spawn_waves) != TYPE_ARRAY:
			push_error("Spawner missing spawn_waves array: %s" % spawner_node)
			continue
		for wave in spawn_waves:
			if typeof(wave) != TYPE_ARRAY:
				push_error("Invalid wave in spawner: %s" % spawner_node)
				continue
			for item in wave:
				var spawn_data := item as QuiverSpawnData
				if spawn_data == null or spawn_data.enemy_scene == null:
					push_error("Invalid spawn data in spawner: %s" % spawner_node)
					continue
				var enemy := spawn_data.enemy_scene.instantiate() as QuiverEnemyCharacter
				if enemy == null or enemy.attributes == null:
					push_error("Spawned enemy scene missing attributes: %s" % spawn_data.enemy_scene)
					continue
				total += float(enemy.attributes.health_max)
				enemy.free()

	return total

### -----------------------------------------------------------------------------------------------
