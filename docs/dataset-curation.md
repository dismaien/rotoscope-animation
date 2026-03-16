# Dataset Curation

## Purpose

The first model should learn a paired transformation:

- input: original interview frame
- target: high-quality Nano Banana painterly frame

This is not a pure style-only dataset. It is a subject-preserving edit dataset.

## Primary Dataset

Use `nano_output` as the main supervision set. Treat `saved_favorites` as optional
references, not the default gold set.

## First-Pass Workflow

1. Build a pair manifest from the source keyframes and styled references.
2. Review every pair for structural fidelity and art quality.
3. Mark weak or broken pairs as `discard` instead of forcing them into training.
4. Split the usable pairs into `train`, `val`, and `holdout`.
5. Identify missing expression coverage and backfill with new Nano Banana renders.

## Pair Review Rubric

Score each pair from `1` to `5`.

- `style_score`: painterly beauty, line quality, brush feel
- `likeness_score`: same face, same proportions, same person
- `expression_score`: same mouth shape, eyes, emotional read
- `structure_score`: same pose, framing, clothing, jewelry, background

Suggested interpretation:

- `5`: excellent, definitely keep
- `4`: strong, likely keep
- `3`: usable but watch for specific flaws
- `2`: weak, keep only if coverage is rare
- `1`: broken, discard

## Split Strategy

Start from the set of usable pairs only.

- `train`: about `70-80%`
- `val`: about `10-15%`
- `holdout`: about `10-15%`

The split should be coverage-aware, not random. The holdout needs to include:

- neutral talking frames
- narrow mouth speech
- open mouth speech
- teeth-visible speech
- smiles
- blinks or half-closed eyes
- slight head turns left and right
- lighting or shadow variation

## Missing Examples To Backfill

High-value missing examples are the ones most likely to break the final film:

- lips pressed together before or after a word
- small mouth opening
- wide mouth opening
- teeth-visible speech
- asymmetrical smile or smirk
- blink or eyes half closed
- downward glance
- head turned slightly off-center
- hand or necklace interaction
- stronger shadow on the face

## Caption Strategy

Use a stable style clause plus compact structured tags.

Base style clause:

`high-end painterly rotoscope animation, bold dark contour lines, visible brushstrokes, cinematic painted color blocking, hand-painted motion feel`

Useful structured tags:

- `expression=neutral_talking`
- `mouth=closed|small_open|wide_open|teeth_visible|smile`
- `eyes=open|blink|half_closed`
- `head=front|three_quarter_left|three_quarter_right`
- `hands=none|visible`
- `lighting=soft|shadowed`

## What To Avoid

- overloading the dataset with near-identical neutral frames
- training on pairs that clearly change lip fullness or facial proportions
- hiding weak data inside the train set instead of discarding it
- relying on captions alone to fix bad supervision
