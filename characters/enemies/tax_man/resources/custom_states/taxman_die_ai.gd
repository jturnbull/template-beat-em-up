@tool
extends QuiverActionDieAi

const CORPSE_NAME := "TaxManCorpse"


func _on_skin_animation_finished() -> void:
	_spawn_corpse_sprite()
	_character.queue_free()
	var enemy_defeated_event := Callable(Events, "emit_signal").bind("enemy_defeated")
	QuiverEditorHelper.connect_between(tree_exited, enemy_defeated_event, CONNECT_ONE_SHOT)


func _spawn_corpse_sprite() -> void:
	if _character == null or _skin == null:
		return
	var parent := _character.get_parent() as Node2D
	if parent == null:
		return
	var existing := parent.get_node_or_null(CORPSE_NAME)
	if existing != null:
		existing.queue_free()
	var body := _skin.get_node_or_null(^"Body") as AnimatedSprite2D
	if body == null or body.sprite_frames == null:
		return
	var texture := body.sprite_frames.get_frame_texture(body.animation, body.frame)
	if texture == null:
		return
	var corpse := Sprite2D.new()
	corpse.name = CORPSE_NAME
	corpse.texture = texture
	corpse.centered = body.centered
	corpse.offset = body.offset
	corpse.flip_h = body.flip_h
	corpse.modulate = body.modulate
	corpse.z_index = body.z_index
	corpse.z_as_relative = body.z_as_relative
	parent.add_child(corpse, true)
	corpse.global_transform = body.global_transform
