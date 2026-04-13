@tool
extends QuiverCharacterAction

## Write your doc string for this file here

### Member Variables and Dependencies -------------------------------------------------------------
#--- signals --------------------------------------------------------------------------------------

#--- enums ----------------------------------------------------------------------------------------

#--- constants ------------------------------------------------------------------------------------

const THRONE_NAME := "__tax_man_throne_remnant"
const THRONE_TEXTURE := preload("res://characters/enemies/tax_man/resources/sprites/seated/throne/throne_only.png")
const IDLE_BODY_POSITION := Vector2(0, -281)

#--- public variables - order: export > normal var > onready --------------------------------------

#--- private variables - order: export > normal var > onready -------------------------------------

var _path_idle := "Ground/Move/IdleAi"

var _skin_reveal := &"seated_reveal"
var _skin_swirl := &"seated_swirl"
var _skin_engage := &"seated_engage"
var _current_animation: StringName:
	set(value):
		_current_animation = value
		if is_instance_valid(_skin):
			_skin.transition_to(_current_animation)

### -----------------------------------------------------------------------------------------------


### Built in Engine Methods -----------------------------------------------------------------------

func _ready() -> void:
	super()
	if Engine.is_editor_hint():
		QuiverEditorHelper.disable_all_processing(self)
		return

### -----------------------------------------------------------------------------------------------


### Public Methods --------------------------------------------------------------------------------

func enter(msg: = {}) -> void:
	super(msg)
	_clear_spawned_throne()
	_character._disable_collisions()
	await _character.tax_man_revealed
	QuiverEditorHelper.connect_between(_character.tax_man_engaged, _on_tax_man_engaged)
	_current_animation = _skin_reveal


func exit() -> void:
	super()
	_character._enable_collisions()

### -----------------------------------------------------------------------------------------------


### Private Methods -------------------------------------------------------------------------------

func _connect_signals() -> void:
	super()
	QuiverEditorHelper.connect_between(_skin.skin_animation_finished, _on_skin_animation_finished)


func _disconnect_signals() -> void:
	super()
	if _skin != null:
		QuiverEditorHelper.disconnect_between(
			_skin.skin_animation_finished, _on_skin_animation_finished
		)
	
	if _character != null:
		QuiverEditorHelper.disconnect_between(_character.tax_man_engaged, _on_tax_man_engaged)


func _on_tax_man_engaged() -> void:
	_current_animation = _skin_engage


func _on_skin_animation_finished() -> void:
	if _current_animation == _skin_reveal:
		_current_animation = _skin_swirl
	elif _current_animation == _skin_engage:
		_spawn_throne_remnant()
		_align_character_to_idle()
		_state_machine.transition_to(_path_idle)


func _spawn_throne_remnant() -> void:
	var body: AnimatedSprite2D = _get_body()
	var parent: Node = _character.get_parent()
	assert(parent != null, "Tax Man requires a parent node to leave the throne behind.")
	var throne: Sprite2D = Sprite2D.new()
	throne.name = THRONE_NAME
	throne.texture = THRONE_TEXTURE
	throne.centered = true
	throne.flip_h = body.flip_h
	parent.add_child(throne)
	throne.global_transform = body.global_transform
	throne.z_index = _character.z_index - 1


func _align_character_to_idle() -> void:
	var body: AnimatedSprite2D = _get_body()
	var sprite_frames: SpriteFrames = body.sprite_frames
	assert(sprite_frames != null, "Expected SpriteFrames on Tax Man body.")
	var engage_texture: Texture2D = sprite_frames.get_frame_texture(body.animation, body.frame)
	var idle_texture: Texture2D = sprite_frames.get_frame_texture(&"idle", 0)
	assert(engage_texture != null, "Expected a valid engage texture for Tax Man handoff.")
	assert(idle_texture != null, "Expected a valid idle texture for Tax Man handoff.")

	var engage_anchor: Vector2 = _engage_body_anchor_local(engage_texture, body.position, body.flip_h)
	var idle_anchor: Vector2 = _texture_anchor_local(idle_texture, IDLE_BODY_POSITION, body.flip_h)
	_character.global_position += engage_anchor - idle_anchor


func _texture_anchor_local(texture: Texture2D, body_position: Vector2, flip_h: bool) -> Vector2:
	var image: Image = texture.get_image()
	assert(image != null, "Expected to read image data from Tax Man texture.")
	var texture_size: Vector2 = Vector2(texture.get_width(), texture.get_height())
	return _ground_anchor_local_from_image(image, texture_size, body_position, flip_h)


func _engage_body_anchor_local(texture: Texture2D, body_position: Vector2, flip_h: bool) -> Vector2:
	var image: Image = texture.get_image()
	assert(image != null, "Expected to read image data from Tax Man engage texture.")
	var body_only: Image = image.duplicate()
	var throne_image: Image = THRONE_TEXTURE.get_image()
	assert(throne_image != null, "Expected to read image data from Tax Man throne texture.")
	assert(
		throne_image.get_size() == body_only.get_size(),
		"Expected throne remnant texture to match engage texture size."
	)

	for y in range(body_only.get_height()):
		for x in range(body_only.get_width()):
			if throne_image.get_pixel(x, y).a > 0.0:
				var pixel: Color = body_only.get_pixel(x, y)
				body_only.set_pixel(x, y, Color(pixel.r, pixel.g, pixel.b, 0.0))

	var texture_size: Vector2 = Vector2(texture.get_width(), texture.get_height())
	return _ground_anchor_local_from_image(body_only, texture_size, body_position, flip_h)


func _ground_anchor_local_from_image(image: Image, texture_size: Vector2, body_position: Vector2, flip_h: bool) -> Vector2:
	var used_rect: Rect2i = image.get_used_rect()
	assert(used_rect.size != Vector2i.ZERO, "Expected visible pixels in Tax Man texture.")
	var foot_region_top: int = int(used_rect.position.y + used_rect.size.y * 0.82)
	var sum_x: float = 0.0
	var count: int = 0
	var max_y: int = used_rect.position.y
	for y in range(foot_region_top, used_rect.position.y + used_rect.size.y):
		for x in range(used_rect.position.x, used_rect.position.x + used_rect.size.x):
			if image.get_pixel(x, y).a > 0.0:
				sum_x += x
				count += 1
				if y > max_y:
					max_y = y
	assert(count > 0, "Expected foot pixels in Tax Man texture.")
	var anchor_x: float = sum_x / count - texture_size.x / 2.0
	if flip_h:
		anchor_x = -anchor_x
	var anchor_y: float = max_y - texture_size.y / 2.0
	return body_position + Vector2(anchor_x, anchor_y)


func _get_body() -> AnimatedSprite2D:
	var body: AnimatedSprite2D = _skin.get_node("Body") as AnimatedSprite2D
	assert(body != null, "Expected AnimatedSprite2D Body on Tax Man skin.")
	return body


func _clear_spawned_throne() -> void:
	var parent: Node = _character.get_parent()
	if parent == null:
		return
	var throne: Node = parent.get_node_or_null(THRONE_NAME)
	if throne != null:
		throne.queue_free()

### -----------------------------------------------------------------------------------------------

###################################################################################################
# Custom Inspector ################################################################################
###################################################################################################

func _get_custom_properties() -> Dictionary:
	return {
		"Seated State":{
			type = TYPE_NIL,
			usage = PROPERTY_USAGE_CATEGORY,
			hint = PROPERTY_HINT_NONE,
		},
		"_path_idle": {
			default_value = "Ground/Move/IdleAi",
			type = TYPE_STRING,
			usage = PROPERTY_USAGE_DEFAULT | PROPERTY_USAGE_SCRIPT_VARIABLE,
			hint = PROPERTY_HINT_NONE,
			hint_string = QuiverState.HINT_STATE_LIST,
		},
		"Animations":{
			type = TYPE_NIL,
			usage = PROPERTY_USAGE_GROUP,
			hint_string = "_skin_",
		},
		"_skin_reveal": {
			default_value = &"seated_reveal",
			type = TYPE_STRING,
			usage = PROPERTY_USAGE_DEFAULT | PROPERTY_USAGE_SCRIPT_VARIABLE,
			hint = PROPERTY_HINT_ENUM,
			hint_string = \
					'ExternalEnum{"property": "_skin", "property_name": "_animation_list"}'
		},
		"_skin_swirl": {
			default_value = &"seated_swirl",
			type = TYPE_STRING,
			usage = PROPERTY_USAGE_DEFAULT | PROPERTY_USAGE_SCRIPT_VARIABLE,
			hint = PROPERTY_HINT_ENUM,
			hint_string = \
					'ExternalEnum{"property": "_skin", "property_name": "_animation_list"}'
		},
		"_skin_engage": {
			default_value = &"seated_engage",
			type = TYPE_STRING,
			usage = PROPERTY_USAGE_DEFAULT | PROPERTY_USAGE_SCRIPT_VARIABLE,
			hint = PROPERTY_HINT_ENUM,
			hint_string = \
					'ExternalEnum{"property": "_skin", "property_name": "_animation_list"}'
		},
#		"": {
#			backing_field = "", # use if dict key and variable name are different
#			default_value = "", # use if you want property to have a default value
#			type = TYPE_NIL,
#			usage = PROPERTY_USAGE_DEFAULT,
#			hint = PROPERTY_HINT_NONE,
#			hint_string = "",
#		},
	}

### Custom Inspector built in functions -----------------------------------------------------------

func _get_property_list() -> Array:
	var properties: Array = []
	
	var custom_properties: Dictionary = _get_custom_properties()
	for key in custom_properties:
		var dict: Dictionary = custom_properties[key]
		if not dict.has("name"):
			dict.name = key
		properties.append(dict)
	
	return properties


func _property_can_revert(property: StringName) -> bool:
	var custom_properties: Dictionary = _get_custom_properties()
	if property in custom_properties and custom_properties[property].has("default_value"):
		return true
	else:
		return false


func _property_get_revert(property: StringName):
	var value: Variant = null
	
	var custom_properties: Dictionary = _get_custom_properties()
	if property in custom_properties and custom_properties[property].has("default_value"):
		value = custom_properties[property]["default_value"]
	
	return value


func _get(property: StringName):
	var value: Variant = null
	
	var custom_properties: Dictionary = _get_custom_properties()
	if property in custom_properties and custom_properties[property].has("backing_field"):
		value = get(custom_properties[property]["backing_field"])
	
	return value


func _set(property: StringName, value) -> bool:
	var has_handled: bool = false
	
	var custom_properties: Dictionary = _get_custom_properties()
	if property in custom_properties and custom_properties[property].has("backing_field"):
		set(custom_properties[property]["backing_field"], value)
		has_handled = true
	
	return has_handled

### -----------------------------------------------------------------------------------------------
