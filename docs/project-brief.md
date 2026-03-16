# Project Brief

## Target Look

- Bold dark outlines
- Painterly color blocking
- Visible brushstroke feel
- Hand-painted animation quality
- Flattering but identity-faithful likeness
- Preserved expressions and performance

## Output Priorities

1. Highest possible visual quality
2. Identity and expression preservation
3. Reusable workflow design
4. Temporal consistency
5. Cost efficiency
6. Speed

## Known Assets

- Main interview video at `1920x1080`, about `34 minutes`, `24 fps`
- Source keyframes covering the full video
- Nano Banana styled reference frames
- Additional manual favorites and experiments
- Local ComfyUI environment
- Google Cloud access for training and inference

## Working Assumptions

- The Nano Banana frames are the main paired supervision set.
- Favorites are optional references, not the primary gold set.
- Anchor generation should run at `2 fps` minimum and `4 fps` where speech motion is harder.
- Controlled paint boil is desirable and should not be fully removed.

## Open Questions

- Final paired dataset split and caption schema
- Best cloud execution path for `FLUX.2 klein`
- Propagation stack and final repair strategy
