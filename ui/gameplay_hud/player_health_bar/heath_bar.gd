class_name QuiverLifeBar
extends TextureRect

## Write your doc string for this file here

### Member Variables and Dependencies -------------------------------------------------------------
#--- signals --------------------------------------------------------------------------------------

#--- enums ----------------------------------------------------------------------------------------

#--- constants ------------------------------------------------------------------------------------

#--- public variables - order: export > normal var > onready --------------------------------------

@export var attributes: QuiverAttributes = null : set = _set_attributes

#--- private variables - order: export > normal var > onready -------------------------------------

@onready var _profile := $Profile as TextureRect
@onready var _progress := $TextureProgressBar as TextureProgressBar
@onready var _heart_icon := $HeartIcon as TextureRect
@onready var _name_label := $NameLabel as Label
@onready var _prompt_label := $PromptLabel as Label
@onready var _default_gradient := material.get_shader_parameter(&"gradient") as Texture2D
var _name_override := ""

### -----------------------------------------------------------------------------------------------


### Built in Engine Methods -----------------------------------------------------------------------

func _ready() -> void:
	pass

### -----------------------------------------------------------------------------------------------


### Public Methods --------------------------------------------------------------------------------

### -----------------------------------------------------------------------------------------------


### Private Methods -------------------------------------------------------------------------------

func _set_attributes(value: QuiverAttributes) -> void:
	if attributes == value:
		return
	
	_disconnect_attributes_signals()
	attributes = value
	
	if attributes != null:
		_update_lifebar_visuals()
	else:
		_reset_lifebar_visuals()


func set_inactive(is_inactive: bool, prompt_text: String = "PRESS START") -> void:
	if not is_inside_tree():
		await ready
	
	_prompt_label.text = prompt_text
	_prompt_label.visible = is_inactive and not prompt_text.is_empty()
	_prompt_label.modulate = Color(1, 1, 1, 1)
	var alpha := 0.45 if is_inactive else 1.0
	_profile.modulate = Color(1, 1, 1, alpha)
	_progress.modulate = Color(1, 1, 1, alpha)
	_heart_icon.modulate = Color(1, 1, 1, alpha)
	_name_label.modulate = Color(1, 1, 1, alpha)


func set_name_override(name: String) -> void:
	_name_override = name
	if is_inside_tree():
		_name_label.text = name


func _update_lifebar_visuals() -> void:
	if not is_inside_tree():
		await ready
	
	_recover_nodes_on_editor()
	_profile.texture = attributes.profile_texture
	var display_name := _name_override
	if display_name.is_empty():
		display_name = attributes.display_name
	if display_name.is_empty():
		if attributes.character_node != null and attributes.character_node.is_in_group("players"):
			display_name = "PLAYER"
		else:
			display_name = "ENEMY"
	_name_label.text = display_name
	material.set_shader_parameter("gradient", attributes.life_bar_gradient)
	_progress.value = attributes.get_health_as_percentage()
	_connect_attributes_signals()


func _reset_lifebar_visuals() -> void:
	_profile.texture = null
	_name_label.text = ""
	material.set_shader_parameter("gradient", _default_gradient)
	_progress.value = 0


func _disconnect_attributes_signals() -> void:
	if is_instance_valid(attributes):
		QuiverEditorHelper.disconnect_between(attributes.health_changed, _on_health_changed)
		QuiverEditorHelper.disconnect_between(attributes.health_depleted, _on_health_depleted)


func _connect_attributes_signals() -> void:
	QuiverEditorHelper.connect_between(attributes.health_changed, _on_health_changed)
	QuiverEditorHelper.connect_between(attributes.health_depleted, _on_health_depleted)


func _on_health_changed() -> void:
	_progress.value = attributes.get_health_as_percentage()


func _on_health_depleted() -> void:
	_progress.value = 0


func _recover_nodes_on_editor() -> void:
	if Engine.is_editor_hint():
		_profile = $Profile
		_progress = $TextureProgressBar
		_heart_icon = $HeartIcon
		_name_label = $NameLabel
		_prompt_label = $PromptLabel

### -----------------------------------------------------------------------------------------------
