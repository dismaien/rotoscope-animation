# Painterly Rotoscope Animation

High-end painterly rotoscope pipeline for transforming interview footage into a hand-painted animated look inspired by *Waking Life* and *A Scanner Darkly*.

## Goals

- Maximize visual quality first.
- Preserve identity, expression, and mouth shapes.
- Build a reusable pipeline, not just a one-off render.
- Maintain controlled temporal consistency with some intentional paint boil.

## Current Strategy

The project is centered on a hybrid workflow:

1. Curate paired source and styled reference frames.
2. Expand the reference set with rare mouth and expression states.
3. Train a project-specific edit adapter on `FLUX.2 klein`.
4. Generate high-quality anchor frames at `2-4 fps`.
5. Propagate between anchors with an artist-friendly temporal pass.
6. Add localized repair anchors for face, lips, eyes, or hands when needed.

## Initial Repo Layout

- `docs/project-brief.md`: working brief and design targets
- `docs/roadmap.md`: staged plan from `v0` to reusable `v1`
- `tools/mine_mouth_shapes.py`: candidate miner for rare speaking shapes
- `configs/`: reserved for training and inference configs

## Notes

- Source footage and generated frames should live outside git.
- This repo is for code, configs, manifests, prompt templates, and evaluation assets.
- The first model target is project-specific quality; generalization comes later.
