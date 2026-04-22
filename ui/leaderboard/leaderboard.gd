class_name Leaderboard
extends Control

signal entry_flow_finished

@export var rows_count := 6
@export var show_date := false
@export var show_time := false
@export var font_scale := 1.5
@export var title_scale := 0.5
@export var subtitle_scale := 0.6
@export var blink_interval := 0.4
@export var auto_close_seconds := 3.0
@export var auto_hide_on_close := true
@export var use_monospace := true
@export var viewport_margin := 24.0

@onready var _panel := $Panel as PanelContainer
@onready var _title := $Panel/Content/Frame/Header/Title as Label
@onready var _subtitle := $Panel/Content/Frame/Header/Subtitle as Label
@onready var _rows_scroll := $Panel/Content/Frame/RowsPanel/RowsMargin/RowsScroll as ScrollContainer
@onready var _rows_container := $Panel/Content/Frame/RowsPanel/RowsMargin/RowsScroll/Rows as VBoxContainer
@onready var _footer := $Panel/Content/Frame/Footer as Label

var _rows: Array = []
var _display_list: Array = []
var _display_offset: int = 0
var _entry_active := false
var _entry_row_index := -1
var _entry_letters := [0, 0, 0]
var _entry_cursor := 0
var _active_prefix := "p1"
var _pending_entry: Dictionary = {}
var _column_keys: Array[String] = []
var _header_row: HBoxContainer
var _blink_timer: Timer
var _blink_on := true
var _auto_close_timer: Timer
var _mono_font: Font

const _LETTERS := "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

func _ready() -> void:
	_setup_font()
	_setup_blink_timer()
	_setup_auto_close_timer()
	_build_rows()
	_apply_font_scale(_title, title_scale)
	_apply_font_scale(_subtitle, subtitle_scale)
	_apply_font_scale(_footer)
	_show_title("FINAL RESULTS", "TOP CREW SCORES")
	_update_footer("")
	get_viewport().size_changed.connect(_fit_panel_to_viewport)
	_fit_panel_to_viewport()


func show_top10() -> void:
	_entry_active = false
	_pending_entry = {}
	_stop_blink()
	_stop_auto_close()
	_show_title("FINAL RESULTS", "TOP CREW SCORES")
	_update_footer("")
	_display_scores(ScoreManager.get_sorted_scores(), 0, rows_count)


func start_entry_flow() -> void:
	if not ScoreManager.has_pending_entries():
		show_top10()
		emit_signal("entry_flow_finished")
		return
	_stop_auto_close()
	_pending_entry = ScoreManager.peek_pending_entry()
	_active_prefix = _pending_entry.get("player_id", "p1")
	_entry_letters = [0, 0, 0]
	_entry_cursor = 0
	_entry_active = true
	_start_blink()
	_show_title("FINAL RESULTS", _get_entry_subtitle())
	_update_footer("UP / DOWN TO CHANGE LETTERS   ATTACK TO CONFIRM")
	_render_entry()


func _unhandled_input(event: InputEvent) -> void:
	if not _entry_active:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_UP:
			_step_letter(1)
			return
		if event.keycode == KEY_DOWN:
			_step_letter(-1)
			return
	if event.is_action_pressed(_action_name("move_up")):
		_step_letter(1)
	elif event.is_action_pressed(_action_name("move_down")):
		_step_letter(-1)
	elif event.is_action_pressed(_action_name("attack")):
		_lock_letter()


func _build_rows() -> void:
	_rows.clear()
	for child in _rows_container.get_children():
		child.queue_free()
	_build_columns()
	_header_row = _create_header_row()
	_rows_container.add_child(_header_row)
	_ensure_row_count(rows_count)


func _ensure_row_count(required_count: int) -> void:
	while _rows.size() < required_count:
		var row := _create_row()
		_rows_container.add_child(row)
		_rows.append(row)
	while _rows.size() > required_count:
		var row := _rows.pop_back() as HBoxContainer
		row.queue_free()


func _create_header_row() -> HBoxContainer:
	var row := HBoxContainer.new()
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.custom_minimum_size = Vector2(0, 30 * font_scale)
	row.modulate = Color(0.97, 0.82, 0.44, 1)
	row.add_theme_constant_override("separation", int(18 * font_scale))

	for key in _column_keys:
		var label := _make_label(_column_width(key), _column_align(key))
		label.text = _column_header(key)
		row.add_child(label)
	return row


func _create_row() -> HBoxContainer:
	var row := HBoxContainer.new()
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.custom_minimum_size = Vector2(0, 34 * font_scale)
	row.add_theme_constant_override("separation", int(18 * font_scale))

	for key in _column_keys:
		row.add_child(_make_label(_column_width(key), _column_align(key)))

	return row


func _make_label(min_width: int, align: HorizontalAlignment) -> Label:
	var label := Label.new()
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.custom_minimum_size = Vector2(min_width, 0)
	label.horizontal_alignment = align as HorizontalAlignment
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER as VerticalAlignment
	label.add_theme_color_override("font_outline_color", Color(0.03, 0.03, 0.08, 1))
	label.add_theme_constant_override("outline_size", 12)
	label.text = ""
	_apply_font_scale(label)
	return label


func _display_scores(scores: Array, offset: int, count: int) -> void:
	_display_list = scores
	_display_offset = int(clamp(offset, 0, max(0, scores.size() - count)))
	_ensure_row_count(max(rows_count, scores.size()))
	for i in range(_rows.size()):
		var row_index := int(i)
		var row := _rows[i] as HBoxContainer
		if row_index < scores.size():
			_update_row(row, row_index, scores[row_index], row_index == _entry_row_index)
		else:
			_update_row(row, -1, {}, false)
	call_deferred("_sync_scroll_position", _display_offset)


func _update_row(row: HBoxContainer, index: int, entry: Dictionary, highlight: bool) -> void:
	var labels := row.get_children()
	var label_map := _labels_by_key(labels)

	if index < 0:
		for label in labels:
			(label as Label).text = ""
		row.modulate = Color(1, 1, 1, 0.5)
		return

	if label_map.has("rank"):
		label_map.rank.text = "%02d" % (index + 1)
	if label_map.has("name"):
		label_map.name.text = entry.get("name", "---")
	if label_map.has("score"):
		label_map.score.text = _format_score(entry.get("score", 0))
	if label_map.has("time"):
		label_map.time.text = _format_duration(entry.get("duration_ms", 0))
	if label_map.has("date"):
		label_map.date.text = entry.get("date_time", "")
	row.modulate = Color(1, 0.95, 0.72, 1) if highlight else Color(0.93, 0.96, 1.0, 0.9)


func _render_entry() -> void:
	if _pending_entry.is_empty():
		return
	var placement := ScoreManager.get_placement_index(_pending_entry)
	_entry_row_index = placement
	var scores := ScoreManager.get_sorted_scores()
	var display := scores.duplicate(true)
	var placeholder := _pending_entry.duplicate(true)
	placeholder.name = _get_entry_name()
	display.insert(placement, placeholder)

	var window_size := rows_count
	var offset := placement - int(float(window_size) / 2.0)
	_display_scores(display, offset, window_size)


func _step_letter(delta: int) -> void:
	_entry_letters[_entry_cursor] = (_entry_letters[_entry_cursor] + delta) % 26
	if _entry_letters[_entry_cursor] < 0:
		_entry_letters[_entry_cursor] = 25
	_render_entry()


func _lock_letter() -> void:
	_entry_cursor += 1
	if _entry_cursor >= 3:
		_commit_entry()
		return
	_render_entry()


func _commit_entry() -> void:
	var entry_name := _get_entry_name()
	ScoreManager.commit_pending_entry(entry_name)
	_entry_active = false
	_entry_row_index = -1
	_stop_blink()
	if ScoreManager.has_pending_entries():
		start_entry_flow()
	else:
		show_top10()
		_start_auto_close()


func _get_entry_name() -> String:
	var letters := []
	for i in range(3):
		if i > _entry_cursor:
			letters.append(" ")
			continue
		if i == _entry_cursor and _entry_active and not _blink_on:
			letters.append(" ")
			continue
		letters.append(_LETTERS[_entry_letters[i]])
	return "%s%s%s" % letters


func _get_entry_subtitle() -> String:
	return "ENTER NAME - %s" % (_active_prefix.to_upper())


func _format_duration(ms: int) -> String:
	var total_seconds := int(float(ms) / 1000.0)
	var minutes := int(float(total_seconds) / 60.0)
	var seconds := int(total_seconds % 60)
	return "%02d:%02d" % [minutes, seconds]


func _show_title(title: String, subtitle: String) -> void:
	_title.text = title
	_subtitle.text = subtitle


func _update_footer(text: String) -> void:
	_footer.text = text
	_footer.visible = not text.is_empty()


func _action_name(action: String) -> String:
	return "%s_%s" % [_active_prefix, action]


func _setup_blink_timer() -> void:
	_blink_timer = Timer.new()
	_blink_timer.wait_time = blink_interval
	_blink_timer.one_shot = false
	_blink_timer.ignore_time_scale = true
	_blink_timer.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(_blink_timer)
	_blink_timer.timeout.connect(_on_blink_timeout)


func _start_blink() -> void:
	_blink_on = true
	if _blink_timer:
		_blink_timer.start()


func _stop_blink() -> void:
	if _blink_timer:
		_blink_timer.stop()
	_blink_on = true


func _on_blink_timeout() -> void:
	if not _entry_active:
		return
	_blink_on = not _blink_on
	_render_entry()


func _apply_font_scale(label: Label, scale: float = font_scale) -> void:
	var base_size := label.get_theme_font_size("font_size")
	if base_size <= 0:
		base_size = 16
	label.add_theme_font_size_override("font_size", int(base_size * scale))
	if _mono_font != null:
		label.add_theme_font_override("font", _mono_font)


func _build_columns() -> void:
	_column_keys.clear()
	_column_keys.append("rank")
	_column_keys.append("name")
	_column_keys.append("score")
	if show_time:
		_column_keys.append("time")
	if show_date:
		_column_keys.append("date")


func _column_width(key: String) -> int:
	match key:
		"rank":
			return int(60 * font_scale)
		"name":
			return int(120 * font_scale)
		"score":
			return int(120 * font_scale)
		"date":
			return int(120 * font_scale)
		_:
			return int(90 * font_scale)


func _column_align(key: String) -> HorizontalAlignment:
	match key:
		"rank", "name":
			return HORIZONTAL_ALIGNMENT_LEFT as HorizontalAlignment
		_:
			return HORIZONTAL_ALIGNMENT_RIGHT as HorizontalAlignment


func _column_header(key: String) -> String:
	match key:
		"rank":
			return "RANK"
		"name":
			return "NAME"
		"score":
			return "SCORE"
		"date":
			return "DATE"
		_:
			return ""


func _format_score(value) -> String:
	var score := int(round(float(value)))
	var digits := str(abs(score))
	var parts: Array[String] = []
	while digits.length() > 3:
		parts.push_front(digits.substr(digits.length() - 3, 3))
		digits = digits.substr(0, digits.length() - 3)
	parts.push_front(digits)
	var formatted := ",".join(parts)
	return "-%s" % formatted if score < 0 else formatted


func _labels_by_key(labels: Array) -> Dictionary:
	var map := {}
	var max_index: int = int(min(labels.size(), _column_keys.size()))
	for i in range(max_index):
		map[_column_keys[i]] = labels[i]
	return map


func _setup_font() -> void:
	if not use_monospace:
		return
	var font := SystemFont.new()
	font.font_names = ["Menlo", "Consolas", "Monaco", "Courier New"]
	_mono_font = font


func _setup_auto_close_timer() -> void:
	_auto_close_timer = Timer.new()
	_auto_close_timer.one_shot = true
	_auto_close_timer.ignore_time_scale = true
	_auto_close_timer.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(_auto_close_timer)
	_auto_close_timer.timeout.connect(_on_auto_close_timeout)


func _start_auto_close() -> void:
	if auto_close_seconds <= 0.0:
		_on_auto_close_timeout()
		return
	if _auto_close_timer:
		_auto_close_timer.wait_time = auto_close_seconds
		_auto_close_timer.start()


func _stop_auto_close() -> void:
	if _auto_close_timer:
		_auto_close_timer.stop()


func _on_auto_close_timeout() -> void:
	if auto_hide_on_close:
		visible = false
	emit_signal("entry_flow_finished")


func _fit_panel_to_viewport() -> void:
	var viewport_size := get_viewport_rect().size
	var target_size := _panel.size
	target_size.x = min(720.0, viewport_size.x - 64.0)
	target_size.y = max(320.0, viewport_size.y - (viewport_margin * 2.0))
	_panel.custom_minimum_size = target_size
	_panel.size = target_size
	_panel.position = (viewport_size - target_size) * 0.5


func _sync_scroll_position(row_index: int) -> void:
	if _rows.is_empty():
		_rows_scroll.scroll_vertical = 0
		return
	var clamped_index := int(clamp(row_index, 0, _rows.size() - 1))
	var row := _rows[clamped_index] as HBoxContainer
	_rows_scroll.scroll_vertical = int(row.position.y)
