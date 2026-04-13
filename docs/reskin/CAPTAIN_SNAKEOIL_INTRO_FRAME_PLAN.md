# Captain Snakeoil Intro Frame Plan

## Source videos

### Seated master
- Video: `outputs/reskin/captain_snakeoil/intro/seated_master/videos/20260412_162918/bytedance_seedance_2_0_fast_image_to_video/seated_master.mp4`
- Full contact: `outputs/reskin/captain_snakeoil/intro/seated_master/review/20260412_162918/bytedance_seedance_2_0_fast_image_to_video/contact.png`
- Segment contacts:
  - `outputs/reskin/captain_snakeoil/intro/seated_master/review/20260412_162918/bytedance_seedance_2_0_fast_image_to_video/frames_reveal_settle_contact.png`
  - `outputs/reskin/captain_snakeoil/intro/seated_master/review/20260412_162918/bytedance_seedance_2_0_fast_image_to_video/frames_swirl_loop_contact.png`
  - `outputs/reskin/captain_snakeoil/intro/seated_master/review/20260412_162918/bytedance_seedance_2_0_fast_image_to_video/frames_drink_contact.png`
  - `outputs/reskin/captain_snakeoil/intro/seated_master/review/20260412_162918/bytedance_seedance_2_0_fast_image_to_video/frames_laugh_contact.png`

### Engage master
- Video: `outputs/reskin/captain_snakeoil/intro/engage_master/videos/20260412_161222/bytedance_seedance_2_0_fast_image_to_video/engage_master.mp4`
- Full contact: `outputs/reskin/captain_snakeoil/intro/engage_master/review/20260412_161222/bytedance_seedance_2_0_fast_image_to_video/contact.png`
- Segment contacts:
  - `outputs/reskin/captain_snakeoil/intro/engage_master/review/20260412_161222/bytedance_seedance_2_0_fast_image_to_video/frames_throw_contact.png`
  - `outputs/reskin/captain_snakeoil/intro/engage_master/review/20260412_161222/bytedance_seedance_2_0_fast_image_to_video/frames_reach_sword_contact.png`
  - `outputs/reskin/captain_snakeoil/intro/engage_master/review/20260412_161222/bytedance_seedance_2_0_fast_image_to_video/frames_stand_up_contact.png`
  - `outputs/reskin/captain_snakeoil/intro/engage_master/review/20260412_161222/bytedance_seedance_2_0_fast_image_to_video/frames_ready_pose_contact.png`

## Proposed distinct source frames

These are the distinct frames to extract from the videos. Hold timing should be handled in the animation resources, not by duplicating PNGs excessively.

### Seated master

#### `seated_reveal`
- Use 3 distinct frames
- Tentative picks from `frames_reveal_settle`:
  - `001`
  - `007`
  - `011`
- Reason: enough change for a short reveal/notice beat without wasting frames on near-identical poses.

#### `seated_swirl`
- Use 4 distinct frames
- Tentative picks from `frames_swirl_loop`:
  - `001`
  - `005`
  - `008`
  - `011`
- Reason: this is the only seated loop, so it needs the smoothest cadence of the seated set.

#### `seated_drink`
- Use 3 distinct frames
- Tentative picks from `frames_drink`:
  - `001`
  - `006`
  - `012`
- Reason: lift / sip / settle is enough. The timing should come from animation lengths, not 30 repeated files.

#### `seated_laugh`
- Use 3 distinct frames
- Tentative picks from `frames_laugh`:
  - `001`
  - `007`
  - `013`
- Reason: current laugh motion is subtle. Keep the frame count low and use timing/holds to sell it.

### Engage master

#### `seated_engage` composite
- Use 12 distinct frames total, composed from the engage source video:

##### Throw
- 3 frames
- Tentative picks from `frames_throw`:
  - `003`
  - `008`
  - `013`

##### Reach sword
- 3 frames
- Tentative picks from `frames_reach_sword`:
  - `001`
  - `007`
  - `013`

##### Stand up
- 4 frames
- Tentative picks from `frames_stand_up`:
  - `001`
  - `004`
  - `008`
  - `012`

##### Ready pose
- 2 frames
- Tentative picks from `frames_ready_pose`:
  - `002`
  - `006`

## Chair handoff plan

The seated frames have the throne baked in. The standing gameplay character must not.

### Rule
- Keep the throne baked into all seated video-derived frames.
- At the first fully upright handoff frame, switch to:
  - normal Captain Snakeoil standing character
  - plus a separate static throne sprite left behind in-world

### Empty chair asset
- Chair sprite: `outputs/reskin/captain_snakeoil/intro/assets/throne_only.png`

### Alignment steps
1. Extract seated frames on the exact video canvas they already use.
2. Pick the final seated/stand-up frame where Snakeoil is clearly no longer visually supported by the chair.
3. Place `throne_only.png` in world space so it matches the chair location from the final baked seated frame.
4. Align the gameplay Snakeoil standing sprite to that same frame by pelvis/foot position.
5. Tune chair X/Y and character X/Y in a dedicated preview scene until:
   - the stand-up handoff does not pop
   - the empty chair remains exactly where the seated throne was
   - the gameplay character does not slide when the state changes

## Integration notes

- Replace the current bloated repeated-frame seated sprite usage with fewer distinct frames and explicit timing.
- Do not keep the legacy Tax Man repeated 31-frame `wine_drink` or 37-frame `engage` pattern.
- Use the distinct frame counts above and let the animation resources hold poses for longer where needed.

## Known risk

- `seated_laugh` in the current seated source video is visually weak. If the three selected laugh frames still do not read in preview, regenerate only the seated master with a stronger laugh beat instead of forcing more frames.
