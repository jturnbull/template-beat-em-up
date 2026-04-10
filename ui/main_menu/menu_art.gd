extends Control

@export var mouse_shift := Vector2(28.0, 16.0)
@export var idle_float := 8.0
@export var idle_speed := 0.7

var _base_positions: Dictionary = {}


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	for child in get_children():
		if child is TextureRect and child.name != "BG" and child.name != "PaintSpray":
			_base_positions[child] = child.position


func _process(_delta: float) -> void:
	var viewport_rect := get_viewport_rect()
	if viewport_rect.size == Vector2.ZERO:
		return

	var mouse_ratio := (get_viewport().get_mouse_position() / viewport_rect.size) - Vector2(0.5, 0.5)
	var time := Time.get_ticks_msec() / 1000.0

	for child in _base_positions.keys():
		var base_position: Vector2 = _base_positions[child]
		var drift := Vector2(mouse_ratio.x * mouse_shift.x, mouse_ratio.y * mouse_shift.y)
		var bob := Vector2(0.0, sin(time * idle_speed + float(child.get_index())) * idle_float)
		(child as TextureRect).position = base_position + drift + bob
