# Visual Benchmark Shortlist

This replaces the looser transcript-first clip selection with a more useful picture-first shortlist.

## Why This Exists

The earlier dense Gemini tests were not surgically chosen enough for the cost. Some of the benchmark windows were strong conceptually, but they were not always the best on-camera speaking stretches for testing:

- mouth-shape preservation
- expression fidelity
- flattering face rendering while speaking
- final clip usefulness

The corrected rule is:

- choose windows from picture first
- require the subject to be clearly on camera
- prefer active mouth movement over passive listening
- then intersect that with the strongest content ranges

## Output Packets

### On-camera speaking shortlist

Generated from the first `13:12` of current styled coverage by scoring the source `1 fps` keyframes for:

- face presence and size
- face centering
- mouth openness
- second-to-second mouth change as a proxy for active speech

Packet:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/oncamera_speaking_benchmarks_v1`

Most useful files:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/oncamera_speaking_benchmarks_v1/README.md`
- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/oncamera_speaking_benchmarks_v1/contact_sheet.jpg`
- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/oncamera_speaking_benchmarks_v1/speaking_windows.csv`
- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/oncamera_speaking_benchmarks_v1/all_speaking_windows.csv`

### Content-friendly corrected benchmarks

These are the first corrected windows that combine:

- strong content sections
- clear on-camera speaking
- existing styled coverage

Target windows:

1. `02:46-02:58`
2. `10:31-10:43`
3. `12:54-13:06`

Packet:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/content_speaking_benchmarks_v1/clips`

Most useful files:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/content_speaking_benchmarks_v1/clips/transmission_visual_source_vs_styled.mp4`
- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/content_speaking_benchmarks_v1/clips/stop_muting_visual_source_vs_styled.mp4`
- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/content_speaking_benchmarks_v1/clips/easeful_productivity_visual_source_vs_styled.mp4`

## Recommendation

If we do any more paid dense-anchor testing, it should use one of these corrected windows, not a loosely chosen transcript section.

My preferred order now is:

1. `10:31-10:43`
2. `12:54-13:06`
3. `02:46-02:58`

That order favors:

- visible speech
- concept strength
- likely usefulness as polished final content
