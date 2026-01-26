# Downtown Beatdown: Beat-em-up game template
An open source 2D beat-em-up game template for Godot 4, to make games like *Streets of Rage*.
Created by [Quiver](https://quiver.dev).

## Trailer
[![Downtown Beatdown Trailer](https://image.mux.com/V79F1t5LueA43ChEhn5nbAV013mD2JmFnPATeb402389Q/animated.gif?start=8&end=14)](https://quiver.dev/assets/game-templates/downtown-beatdown-beat-em-up-godot-4-template/#lg=1&slide=0)

(click to watch the full trailer!)

## Features
- Customizable player and enemy characters
- Configurable attacks
- Detailed environments with background and foreground elements
- Day and night effects
- Level blocking to constrain fights to particular areas
- Customizable enemy AI
- Custom inspectors and debugging tools
- Fully open source!
- Free assets!

## Topics covered
- Advanced animations using ```AnimationPlayer``` and ```AnimationTree```
- State machines
- Custom inspectors
- Custom overlays

## Documentation
Coming soon!

## Spawner logic (Stage 01)
The game uses `QuiverEnemySpawner` nodes triggered by `QuiverPlayerDetector` areas:
- Player enters a detector → fight room camera limits apply and spawners start.
- Each spawner runs waves in order and emits `all_waves_completed` when done.
- FightRoom2 uses two spawners; the stage script waits for both to complete before unlocking.
- FightRoom1/FightRoom3 unlock immediately after their single spawner completes.
- FightRoom4 triggers the boss reveal; FightRoom5 starts after FightRoom4 waves complete.

Core implementation:
- Spawner: `addons/quiver.beat_em_up/utilities/custom_nodes/enemy_spawner/quiver_enemy_spawner.gd`
- Player detector: `addons/quiver.beat_em_up/utilities/custom_nodes/quiver_player_detector.gd`
- Stage orchestration: `stages/stage_01/stage_01.gd` and `stages/stage_01/stage_01.tscn`

## Requirements
* Godot 4.0 RC6 or higher

## Installation instructions
* This project uses [Git Large File Storage](https://git-lfs.github.com/) (LFS) to store asset binaries. To initialize it make sure you have LFS installed, then simply run ```git lfs install```
* Clone this repository from Github
* Open the Godot project file in Godot 4 (Beta or higher) and run it to play the demo!

## Questions/Bugs/Suggestions
For bugs and feature requests, feel free to file an issue here or comment on this template's [project page](https://quiver.dev/assets/game-templates/downtown-beatdown-beat-em-up-godot-4-template/).

## Share with the community!
If you manage to incorporate this template into your next project, please share with the [Quiver community](https://quiver.dev/)!

## More game templates
Want more game templates? Check out our growing collection [here](https://quiver.dev/assets/game-templates/).
