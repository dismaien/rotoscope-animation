# Evaluation Rubric

## Still-Frame Evaluation

Score each dimension from `1` to `5`.

- `likeness`: face shape, lips, eyes, nose, brow, and overall identity stay true
- `expression`: mouth shape, gaze, and emotional read match the source frame
- `flattery`: the result is attractive and polished without becoming a different person
- `style`: bold contours, paint handling, and brush texture match the target aesthetic
- `structure`: pose, clothing, jewelry, and background composition stay aligned
- `artifact_risk`: low score means distracting failures, high score means clean

## Production Gate

A frame is production-worthy when:

- likeness is at least `4`
- expression is at least `4`
- style is at least `4`
- there are no obvious structural errors

## Temporal Evaluation

Judge propagated segments on:

- face stability across adjacent frames
- mouth readability while speaking
- eye stability during blinks
- line flicker quality
- paint boil quality
- background wobble or drift

Good temporal behavior means:

- the face stays the same person
- the speaking performance remains readable
- the paint moves with life rather than jittering randomly

## Notes Template

When logging review notes, keep them specific.

- `good lip fullness, background stable`
- `too much nasolabial emphasis`
- `mouth shape off on open vowel`
- `great brush texture, slight eye drift`
