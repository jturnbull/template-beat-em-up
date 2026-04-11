extends TextureRect

@export var bob_amount := 14.0
@export var tilt_degrees := 2.5
@export var mouse_shift := Vector2(22.0, 10.0)

var _base_position := Vector2.ZERO


func _ready() -> void:
	_base_position = position


func _process(_delta: float) -> void:
	var viewport_rect := get_viewport_rect()
	if viewport_rect.size == Vector2.ZERO:
		return

	var mouse_ratio := (get_viewport().get_mouse_position() / viewport_rect.size) - Vector2(0.5, 0.5)
	var time := Time.get_ticks_msec() / 1000.0
	position = _base_position + Vector2(mouse_ratio.x * mouse_shift.x, mouse_ratio.y * mouse_shift.y + sin(time * 1.2) * bob_amount)
	rotation_degrees = sin(time * 0.8) * tilt_degrees
