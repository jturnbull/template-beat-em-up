extends Node

## Handles score tracking, persistence, and pending name entries for runs.

const SAVE_PATH := "user://scores.json"

const MAX_SCORE := 10000.0
const DAMAGE_SCORE_WEIGHT := 9000.0
const HEALTH_BONUS_WEIGHT := 1000.0

var _run_start_ms := 0
var _run_active := false
var _p2_joined := false
var _requested_player_count := 1
var _pending_entries: Array = []
var _scores: Array = []
var _total_enemy_health_pool := 0.0
var _enemy_damage_dealt := 0.0
var _tracked_enemies := {}

func _ready() -> void:
	_load_scores()


func start_run() -> void:
	_run_start_ms = Time.get_ticks_msec()
	_run_active = true
	_p2_joined = false
	_pending_entries.clear()
	_total_enemy_health_pool = 0.0
	_enemy_damage_dealt = 0.0
	_clear_tracked_enemies()


func set_total_enemy_health_pool(total_health: float) -> void:
	if total_health < 0.0:
		push_error("Enemy health pool cannot be negative: %s" % total_health)
		return
	_total_enemy_health_pool = total_health


func register_enemy(enemy: QuiverEnemyCharacter) -> void:
	if enemy == null or not is_instance_valid(enemy):
		push_error("Tried to register invalid enemy: %s" % enemy)
		return
	if enemy.attributes == null:
		push_error("Enemy has no attributes: %s" % enemy)
		return

	var instance_id: int = enemy.get_instance_id()
	if _tracked_enemies.has(instance_id):
		return

	var attributes: QuiverAttributes = enemy.attributes
	var health_changed_callable := _on_enemy_health_changed.bind(instance_id)
	var health_depleted_callable := _on_enemy_health_depleted.bind(instance_id)
	_tracked_enemies[instance_id] = {
		attributes = attributes,
		last_health = float(attributes.health_current),
		max_health = float(attributes.health_max),
		health_changed_callable = health_changed_callable,
		health_depleted_callable = health_depleted_callable,
	}
	attributes.health_changed.connect(health_changed_callable)
	attributes.health_depleted.connect(health_depleted_callable)


func request_player_count(player_count: int) -> void:
	if player_count != 1 and player_count != 2:
		push_error("Invalid requested player count: %s" % player_count)
		return
	_requested_player_count = player_count


func consume_requested_player_count() -> int:
	var player_count := _requested_player_count
	_requested_player_count = 1
	return player_count


func set_p2_joined() -> void:
	_p2_joined = true


func finish_run(p1, p2, p2_joined: bool, is_victory: bool) -> void:
	if not _run_active:
		return
	_run_active = false
	var duration_ms := max(0, Time.get_ticks_msec() - _run_start_ms)
	_pending_entries.clear()
	_pending_entries.append(_build_entry("p1", p1, p2, p2_joined, duration_ms, is_victory))
	if p2_joined:
		_pending_entries.append(_build_entry("p2", p1, p2, p2_joined, duration_ms, is_victory))
	_clear_tracked_enemies()


func has_pending_entries() -> bool:
	return _pending_entries.size() > 0


func peek_pending_entry() -> Dictionary:
	if _pending_entries.is_empty():
		return {}
	return _pending_entries.front()


func commit_pending_entry(name: String) -> Dictionary:
	if _pending_entries.is_empty():
		return {}
	var entry := _pending_entries.pop_front()
	entry.name = name
	_scores.append(entry)
	_save_scores()
	return entry


func get_sorted_scores() -> Array:
	var list := _scores.duplicate(true)
	list.sort_custom(_score_sort)
	return list


func get_placement_index(entry: Dictionary) -> int:
	var list := get_sorted_scores()
	list.append(entry)
	list.sort_custom(_score_sort)
	for index in list.size():
		if list[index].id == entry.id:
			return index
	return list.size() - 1


func get_score_count() -> int:
	return _scores.size()


func _build_entry(player_id: String, p1, p2, p2_joined: bool, duration_ms: int, is_victory: bool) -> Dictionary:
	var average_health_ratio := _calculate_average_health_ratio(p1, p2, p2_joined)
	var damage_ratio := _calculate_damage_ratio()
	var score := _calculate_score(damage_ratio, average_health_ratio, is_victory)
	return {
		id = str(Time.get_ticks_usec()),
		player_id = player_id,
		name = "___",
		score = score,
		duration_ms = duration_ms,
		average_health_ratio = average_health_ratio,
		damage_ratio = damage_ratio,
		is_victory = is_victory,
		date_time = Time.get_datetime_string_from_system(true),
		created_at_ms = Time.get_ticks_msec(),
	}


func _calculate_score(damage_ratio: float, average_health_ratio: float, is_victory: bool) -> int:
	var damage_score: float = DAMAGE_SCORE_WEIGHT * clamp(damage_ratio, 0.0, 1.0)
	var health_bonus: float = 0.0
	if is_victory:
		health_bonus = HEALTH_BONUS_WEIGHT * clamp(average_health_ratio, 0.0, 1.0)
	return int(round(min(MAX_SCORE, damage_score + health_bonus)))


func _calculate_average_health_ratio(p1, p2, p2_joined: bool) -> float:
	var players: Array = []
	if is_instance_valid(p1) and p1.attributes != null:
		players.append(p1)
	if p2_joined and is_instance_valid(p2) and p2.attributes != null:
		players.append(p2)
	if players.is_empty():
		return 0.0

	var total: float = 0.0
	for player in players:
		total += clamp(player.attributes.get_health_as_percentage(), 0.0, 1.0)
	return total / float(players.size())


func _calculate_damage_ratio() -> float:
	if _total_enemy_health_pool <= 0.0:
		return 0.0
	return clamp(_enemy_damage_dealt / _total_enemy_health_pool, 0.0, 1.0)


func _on_enemy_health_changed(instance_id: int) -> void:
	if not _tracked_enemies.has(instance_id):
		return
	var tracked: Dictionary = _tracked_enemies[instance_id]
	var attributes := tracked.attributes as QuiverAttributes
	if attributes == null:
		return
	var previous_health := float(tracked.last_health)
	var current_health := float(attributes.health_current)
	if current_health < previous_health:
		_enemy_damage_dealt += previous_health - current_health
	tracked.last_health = current_health
	_tracked_enemies[instance_id] = tracked


func _on_enemy_health_depleted(instance_id: int) -> void:
	_on_enemy_health_changed(instance_id)
	_disconnect_tracked_enemy(instance_id)


func _clear_tracked_enemies() -> void:
	for instance_id in _tracked_enemies.keys():
		_disconnect_tracked_enemy(int(instance_id))


func _disconnect_tracked_enemy(instance_id: int) -> void:
	if not _tracked_enemies.has(instance_id):
		return
	var tracked: Dictionary = _tracked_enemies[instance_id]
	var attributes := tracked.attributes as QuiverAttributes
	var health_changed_callable := tracked.get("health_changed_callable", Callable())
	var health_depleted_callable := tracked.get("health_depleted_callable", Callable())
	if attributes != null:
		if health_changed_callable.is_valid() and attributes.health_changed.is_connected(health_changed_callable):
			attributes.health_changed.disconnect(health_changed_callable)
		if health_depleted_callable.is_valid() and attributes.health_depleted.is_connected(health_depleted_callable):
			attributes.health_depleted.disconnect(health_depleted_callable)
	_tracked_enemies.erase(instance_id)


func _score_sort(a: Dictionary, b: Dictionary) -> bool:
	if a.score == b.score:
		return a.created_at_ms < b.created_at_ms
	return a.score > b.score


func _load_scores() -> void:
	_scores.clear()
	if not FileAccess.file_exists(SAVE_PATH):
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		return
	var data := file.get_as_text()
	file.close()
	if data.is_empty():
		return
	var parsed = JSON.parse_string(data)
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	if parsed.has("scores") and typeof(parsed.scores) == TYPE_ARRAY:
		_scores = parsed.scores


func _save_scores() -> void:
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file == null:
		return
	var payload := {
		scores = _scores,
	}
	file.store_string(JSON.stringify(payload))
	file.close()
