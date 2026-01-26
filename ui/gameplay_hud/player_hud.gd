extends VBoxContainer

## Write your doc string for this file here

### Member Variables and Dependencies -------------------------------------------------------------
#--- signals --------------------------------------------------------------------------------------

#--- enums ----------------------------------------------------------------------------------------

#--- constants ------------------------------------------------------------------------------------

#--- public variables - order: export > normal var > onready --------------------------------------

#--- private variables - order: export > normal var > onready -------------------------------------

@onready var _player_life_bar := $PlayerLifeBar as QuiverLifeBar
@onready var _enemy_life_bar := $EnemyHealthBar as QuiverLifeBar
var _is_inactive := false

### -----------------------------------------------------------------------------------------------


### Built in Engine Methods -----------------------------------------------------------------------

func _ready() -> void:
	QuiverEditorHelper.connect_between(Events.enemy_data_sent, _on_Events_enemy_data_sent)

### -----------------------------------------------------------------------------------------------


### Public Methods --------------------------------------------------------------------------------

func set_player_attributes(p_attributes: QuiverAttributes) -> void:
	_player_life_bar.attributes = p_attributes
	_player_life_bar.set_inactive(_is_inactive)


func set_player_inactive(is_inactive: bool) -> void:
	_is_inactive = is_inactive
	_player_life_bar.set_inactive(is_inactive)


func set_player_name(name: String) -> void:
	_player_life_bar.set_name_override(name)

### -----------------------------------------------------------------------------------------------


### Private Methods -------------------------------------------------------------------------------

func _on_Events_enemy_data_sent(p_enemy: QuiverAttributes, p_player: QuiverAttributes) -> void:
	if _player_life_bar.attributes != p_player:
		return
	
	if p_enemy != null and not p_enemy.is_alive():
		return
	
	_enemy_life_bar.attributes = p_enemy

### -----------------------------------------------------------------------------------------------
