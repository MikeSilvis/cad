# CAD Workspace

A tiny Python-first CAD workspace for AI-assisted 3D modeling.

## Setup

Install OpenSCAD for PNG previews:

```sh
mise install
brew install --cask openscad@snapshot
mise run setup
```

## Everyday Workflow

List the designs this workspace knows about:

```sh
mise run list
```

Build every design:

```sh
mise run build
```

Build one design with dimension overrides:

```sh
.venv/bin/cad build mounting_plate --set length=120 --set hole_spacing=90
```

Exports go into `exports/<model-name>/`:

- `.stl` for slicers and 3D printing
- `.step` for CAD tools
- `.png` for quick previews

## Add A New Design

Create a new design from the template:

```sh
.venv/bin/cad new my_part --description "What this part is for."
```

Then edit:

- `NewDesignSpec` for dimensions and parameters
- `build()` for geometry
- `MODEL.name` and `MODEL.description` for discovery

Run `mise run list` to confirm the new model is discovered.

## Useful Prompts

Ask Codex things like:

```text
Create a new build123d design called phone_stand with parameters for width,
height, phone thickness, lean angle, and charging cable slot. Export STL, STEP,
and PNG, then run mise run validate.
```

```text
Modify designs/mounting_plate.py so the plate has rounded corners, countersunk
M4 screw holes, and a 2mm raised rim. Keep all dimensions parameterized.
```

## Validate

```sh
mise run validate
```

## AI Instructions

Repo-level instructions for Claude/Codex-style agents live in:

[CLAUDE.md](CLAUDE.md)

## OpenSCAD Reference

The repo also includes a tiny OpenSCAD example:

[examples/basic_mounting_plate.scad](examples/basic_mounting_plate.scad)

Open it with:

```sh
open -a OpenSCAD examples/basic_mounting_plate.scad
```
