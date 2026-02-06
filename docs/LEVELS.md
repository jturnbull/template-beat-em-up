# Levels

## Stage 01 — Spaceport Streets → Docked Pirate Ship (Boss)

### Confirmed art direction
- Final dock is **open to space** (no hangar roof), with a **simple repeating safety railing** silhouette like the reference illustration.
- The boss ship is a **full pirate galleon… in space** (rigging/sails read clearly, with space-tech details).

### High-level flow (player-facing)
1. **Spaceport streets (wide establishing stretch)** — stars overhead, port traffic, neon/terminal signage.
2. **Spaceport concourse/market (denser props)** — kiosks, cargo crates, security lights.
3. **Dock approach (industrial)** — gantries/rails, warning markings, the pirate ship is visible ahead.
4. **Dock boarding moment** — the gangplank lowers / ship entrance opens.
5. **Throne room boss fight** — inside the ship; the captain is seated on a throne; fight ends the stage.

This matches the template’s “streets → door → throne room” pacing, but swaps:
- **Door** → **gangplank/ship entrance**
- **City streets** → **spaceport streets**
- **Tax-man room** → **pirate ship throne room**

### How this maps to the current template implementation (dev-facing)
`stages/stage_01/stage_01.tscn` is a **single continuous scrolling stage** with “rooms” implemented as `FightRoom1..5` (camera locks + waves). You can keep that structure and reskin the art/props.

Recommended re-theme by existing “room” boundaries:

| Template node | Approx X-range | New scene/theme name | Purpose / beat |
| --- | --- | --- | --- |
| `FightRoom1` | 267 → 2526 | **Spaceport Street A** | First brawl; establish stars/port vibe. |
| `FightRoom2` | 2924 → 6259 | **Spaceport Street B (Market/Concourse)** | Second brawl; denser props/signage. |
| `FightRoom3` | 6838 → 9734 | **Dock Approach** | Third brawl; pivot to industrial + ship in distance. |
| `ToriGate` (object) | ~10233 | **Security checkpoint / scanner arch** | Visual mid-point landmark before boarding. |
| `DirtyBrickWallGate` (object) | ~11039 | **Gangplank / ship entrance** | “Door replacement”: plays open animation when player reaches it. |
| `FightRoom4` | 13499 → 15815 | **Dock (ship-side, open space)** | Pre-boss reveal / guard wave; “you made it to the ship”. |
| `FightRoom5` | 12587 → 15827 | **Ship Throne Room (Boss)** | Boss engagement + fight finish. |

Notes:
- `FightRoom4` and `FightRoom5` overlap by design in the template (pre-boss wave → boss engage).
- The “boarding” is a *visual transition*; gameplay remains side-scrolling. The gangplank art should suggest “up and onto the ship” while the player continues moving right.

### Art/prop swap plan (use existing filenames; re-theme the content)
You already have per-image replacement tasks under `docs/reskin/tasks/backgrounds/stage_01/`. Treat those as the inventory; the plan below is how to group them by story-beat.

**Always-visible / global mood**
- Sky: `stages/stage_01/stage_elements/skyboxes/area_1_skybox_1_*.png` → starfields/nebulae (subtle parallax/motion reads as drifting stars).
- Distant skyline: `stages/stage_01/stage_elements/buildings/cityscape_00.png` → distant spaceport silhouette/traffic lanes.

**Spaceport Street A/B (FightRoom1–2)**
- Pavement + sidewalk: keep tiling, swap materials to metal decking / port walkway + warning stripes.
- Storefront/building plates: convert to terminals, hangar walls, customs booths, signage.
- “Street poles / lamps / vending machines / posters”: convert to docking pylons, security lights, kiosks, holo-posters.

**Dock Approach (FightRoom3 + checkpoint landmark)**
- Fences/rails: convert to safety rails/cargo fencing.
- Gate landmark: `stages/stage_01/stage_elements/gates/tori_gate/*` → security scanner arch (keep collisions).
- Dock railing read: reskin the chainlink fence set to a **clean metal safety rail** so it can be reused as the “open to space” edge:
  - `stages/stage_01/stage_elements/fence/chainlink_fence_revised__00.png`
  - `stages/stage_01/stage_elements/fence/chainlink_fence_revised__01.png`
  - `stages/stage_01/stage_elements/fence/chainlink_fence_revised__02.png`
  - `stages/stage_01/stage_elements/fence/chainlink_fence_middle_pole.png`

**Boarding moment (gangplank)**
- Ship entrance object: `stages/stage_01/stage_elements/tax_man_area/brick_gate/*` → gangplank + hatch. Keep animation timing/structure; replace imagery.

**Ship throne room (FightRoom4–5 + tax-man area assets)**
- Background wall: `stages/stage_01/stage_elements/tax_man_area/tax_man_back_brick_wall_dirty.png` → ship hull interior/back wall.
- Windows layer: `stages/stage_01/stage_elements/tax_man_area/tax_man_windows.png` → portholes / panoramic windows to space.
- Floor: `stages/stage_01/stage_elements/tax_man_area/tax_man_black_marble.png` + `tax_man_floor_chess.png` → deck plating / carpeted command walkway (pick one “primary floor” read).
- Pillars/trees: convert to ship supports, cables, engine glow columns, banners.
- Throne prop: `stages/stage_01/stage_elements/tax_man_area/tax_man_throne_revised.png` → pirate captain throne.

### Implementation checklist (minimal-change path)
- Keep the stage structure as-is: `stages/stage_01/stage_01.tscn` + `FightRoom1..5`.
- Re-theme by **replacing textures in-place** (same filenames/paths) using your existing background task docs.
- Convert the “door” moment by reskinning the gate object assets:
  - `stages/stage_01/stage_elements/tax_man_area/brick_gate/brick_gate_back.png`
  - `stages/stage_01/stage_elements/tax_man_area/brick_gate/brick_gate_front.png`
  - `stages/stage_01/stage_elements/tax_man_area/brick_gate/tax_man_doors_1.png`
  - `stages/stage_01/stage_elements/tax_man_area/brick_gate/tax_man_doors_2.png`
- Convert the mid-stage landmark by reskinning:
  - `stages/stage_01/stage_elements/gates/tori_gate/tori_gate_back.png`
  - `stages/stage_01/stage_elements/gates/tori_gate/tori_gate_front.png`

### Open questions (only if you want to refine the narrative beats)
- Any “signature landmark” you want visible from Street A all the way to Dock (planet, ring station, giant crane)?
