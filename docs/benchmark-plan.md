# Benchmark Plan

## Goal

Benchmark a small number of serious candidates on a fixed still-frame panel before
committing to large-scale anchor generation.

## Candidate Models

1. `FLUX.2 klein Base 9B` plus paired edit LoRA
2. `FLUX.1 Kontext Max` zero-shot or reference-guided editing baseline
3. `FLUX.2 dev` zero-shot or lightly adapted baseline
4. Existing `SDXL + ControlNet/IP-Adapter` stack as control

## Benchmark Panel

Use a `12-frame` panel that spans the interview's hardest expression states.

- neutral front-facing talking
- mouth closed between words
- small mouth opening
- wide mouth opening
- teeth-visible speech
- warm smile
- asymmetrical smile
- blink or half-closed eyes
- slight head turn left
- slight head turn right
- hands or jewelry visible near the torso
- shadow or lighting variation

## Evaluation Questions

For each output, ask:

- Does this still feel like the same person?
- Does the mouth shape match the source frame?
- Does the output flatter without changing identity?
- Does the linework feel expressive instead of filter-like?
- Does the paint feel deliberate instead of plastic?
- Would this frame belong in the final film?

## Scoring

Score each frame from `1` to `5` on:

- likeness
- expression fidelity
- painterly quality
- flattery
- structure preservation
- final-film usefulness

## Stop Criteria

Do not scale a model to full anchor generation if it fails either of these:

- average likeness below `4.0`
- more than `2` of the `12` benchmark frames feel production-breaking

## Preferred Run Order

1. strong zero-shot baseline
2. first paired `FLUX.2 klein` run
3. improved paired `FLUX.2 klein` run with backfilled expressions
4. only then full anchor rendering
