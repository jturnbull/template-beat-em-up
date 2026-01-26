extends Node

## Handles score tracking, persistence, and pending name entries for runs.

const SAVE_PATH := "user://scores.json"

# Tunables
var par_time_seconds := 900.0
var health_bonus_multiplier := 50
var time_bonus_divisor := 10.0

var _run_start_ms := 0
var _run_active := false
var _p2_joined := false
var _pending_entries: Array = []
var _scores: Array = []

func _ready() -> void:
	_load_scores()


func start_run() -> void:
	_run_start_ms = Time.get_ticks_msec()
	_run_active = true
	_p2_joined = false
	_pending_entries.clear()


func set_p2_joined() -> void:
	_p2_joined = true


func finish_run(p1, p2, p2_joined: bool) -> void:
	if not _run_active:
		return
	_run_active = false
	var duration_ms := max(0, Time.get_ticks_msec() - _run_start_ms)
	_pending_entries.clear()
	_pending_entries.append(_build_entry("p1", p1, duration_ms))
	if p2_joined:
		_pending_entries.append(_build_entry("p2", p2, duration_ms))


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


func _build_entry(player_id: String, player, duration_ms: int) -> Dictionary:
	var health := 0
	if is_instance_valid(player) and player.attributes != null:
		health = int(player.attributes.health_current)
	var score := _calculate_score(health, duration_ms)
	return {
		id = str(Time.get_ticks_usec()),
		player_id = player_id,
		name = "___",
		score = score,
		duration_ms = duration_ms,
		health = health,
		date_time = Time.get_datetime_string_from_system(true),
		created_at_ms = Time.get_ticks_msec(),
	}


func _calculate_score(health: int, duration_ms: int) -> int:
	var par_time_ms := int(par_time_seconds * 1000.0)
	var time_bonus := max(0.0, float(par_time_ms - duration_ms) / time_bonus_divisor)
	var health_bonus := float(health) * float(health_bonus_multiplier)
	return int(time_bonus + health_bonus)


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
