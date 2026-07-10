# CAD Workspace Instructions

This repo is a Python-first CAD workspace for AI-assisted 3D modeling.

## Default Approach

- Use `build123d` for new CAD models unless the user explicitly asks for OpenSCAD.
- Keep all dimensions in millimeters.
- Prefer parametric models with a frozen dataclass spec at the top of each design.
- Export STL for slicers, STEP for CAD interchange, and PNG for quick visual review.
- Treat `exports/` as scratch space. Commit generated files only through the
  project layout under `projects/<project-id>/`.
- For any user-facing printable object, create or update a project folder with
  a manifest, README, committed artifacts, and a standard final render.

## Project Commands

Run commands from the repo root:

```sh
mise run setup
mise run list
mise run build
mise run projects
mise run package -- <project-id>
mise run render -- <project-id>
mise run validate
```

Useful direct CLI commands:

```sh
.venv/bin/cad list
.venv/bin/cad build all
.venv/bin/cad projects
.venv/bin/cad package tab-a9-golf-case
.venv/bin/cad render tab-a9-golf-case
.venv/bin/cad build mounting_plate --set length=120 --set hole_spacing=90
.venv/bin/cad new phone_stand --description "Angled phone stand with charging slot."
```

## Adding A Design

New designs go in `designs/`.

Each design should:

- Define a frozen dataclass named `<PartName>Spec`.
- Define a `build(spec)` function that returns a build123d part.
- Define `MODEL = CadModel(...)` with a stable snake_case name.
- Keep dimensions as spec fields instead of hard-coded values.
- Be discoverable by `.venv/bin/cad list`.

Use this when starting from scratch:

```sh
.venv/bin/cad new my_part --description "Short description."
```

Then edit `designs/my_part.py`.

## Adding A Project

Use a project whenever the work represents a real thing the user may print,
inspect, or share. Keep this layout:

```text
projects/<project-id>/
  project.toml
  README.md
  artifacts/<artifact-slug>/
    <artifact-slug>.stl
    <artifact-slug>.step
    <artifact-slug>.png
    cost_estimate.json
    cost_estimate.txt
  renders/<project-id>_final.png
```

Project IDs use kebab-case. CAD model names stay snake_case. Artifact slugs use
kebab-case and should describe the printable part, such as `case`, `text-inlay`,
`mounting-plate`, or `spacer-set`.

Each `project.toml` should define the stable project metadata and the artifacts
that `cad package` must regenerate:

```toml
id = "my-project"
title = "My Project"
description = "Short human description."

[[artifact]]
slug = "printable-part"
model = "my_part"
formats = ["stl", "step", "png"]
```

Run `mise run package -- <project-id>` after changing a printable project. This
refreshes committed STL/STEP/PNG files, cost estimates, and the standard final
render. Use `mise run render -- <project-id>` when only the summary PNG needs to
be regenerated from existing artifact PNGs.

## Validation

After changing CAD code, run:

```sh
mise run validate
```

This runs tests and exports every registered model. Inspect the generated PNGs under
`exports/<model-name>/` when shape or orientation matters.

For project work, also run:

```sh
mise run package -- <project-id>
```

Then inspect `projects/<project-id>/renders/<project-id>_final.png` and the
artifact PNGs before handing work back.

## Modeling Style

- Keep designs readable and direct. Avoid clever geometry abstractions until there is real repetition.
- Name parameters after the physical feature: `wall_thickness`, `hole_diameter`, `slot_width`.
- Add comments only around non-obvious construction steps.
- Favor simple primitives and boolean operations before complex curves.
- For functional parts, include clearance/tolerance parameters where fit matters.
- If a part will be 3D printed, consider print orientation, overhangs, wall thickness, and screw/hole clearances.

## When To Ask Questions

Ask for missing dimensions only when they affect fit, safety, or compatibility with a real object.
Otherwise, choose reasonable starter dimensions, make them parameters, and explain what to change.

For printer-specific output, ask what printer or slicer the user uses. Do not guess final machine G-code.

## Good User Prompts

```text
Create a build123d design called cable_clip with parameters for cable diameter,
screw size, wall thickness, and clip opening. Export STL, STEP, and PNG.
```

```text
Modify designs/mounting_plate.py so it has rounded corners, countersunk M4 holes,
and a raised rim. Keep every important dimension parameterized.
```

```text
Make a printable spacer for an M5 bolt: 18mm outer diameter, 5.4mm inner diameter,
and 12mm tall. Export it and show me the preview.
```
