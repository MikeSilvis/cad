# CAD Workspace Instructions

This repo is a Python-first CAD workspace for AI-assisted 3D modeling.

## Default Approach

- Use `build123d` for new CAD models unless the user explicitly asks for OpenSCAD.
- Keep all dimensions in millimeters.
- Prefer parametric models with a frozen dataclass spec at the top of each design.
- Export STL for slicers, STEP for CAD interchange, and PNG for quick visual review.
- Treat `exports/` as scratch space. Commit generated files only through the
  project layout under `projects/<project-id>/`.
- For any user-facing printable object, keep project-specific source inside the
  project folder with a manifest, README, committed artifacts, and a standard
  final render.

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
.venv/bin/cad package my-project
.venv/bin/cad render my-project
.venv/bin/cad build mounting_plate --set length=120 --set hole_spacing=90
.venv/bin/cad new phone_stand --description "Angled phone stand with charging slot."
.venv/bin/cad inspect downloaded_part.step
.venv/bin/cad import downloaded_part.step my-project --as-design my_part
```

## Adding A Shared Design

Generic reusable designs go in `designs/`. User-facing project-specific designs
go in `projects/<project-id>/designs/`.

Each design should:

- Define a frozen dataclass named `<PartName>Spec`.
- Define a `build(spec)` function that returns a build123d part.
- Define `MODEL = CadModel(...)` with a stable snake_case name, or `MODELS = (...)`
  when one source file exposes multiple related outputs.
- Keep dimensions as spec fields instead of hard-coded values.
- Be discoverable by `.venv/bin/cad list`.

Use this when starting from scratch:

```sh
.venv/bin/cad new my_part --description "Short description."
```

Then edit `designs/my_part.py`, or move the source under a project folder if the
part belongs to a specific printable project.

## Adding A Project

Use a project whenever the work represents a real thing the user may print,
inspect, or share. Keep this layout:

```text
projects/<project-id>/
  project.toml
  README.md
  designs/<model-name>.py
  reference/<downloaded-file>.step   # optional: downloaded source files
  outputs/<artifact-slug>/
    <artifact-slug>.stl
    <artifact-slug>.step
    <artifact-slug>.png
    cost_estimate.json
    cost_estimate.txt
  outputs/overview.png
```

Project IDs use kebab-case. Project-specific CAD source lives in
`projects/<project-id>/designs/`. CAD model names and design filenames stay
snake_case. Artifact slugs use kebab-case and should describe the printable part,
such as `case`, `text-inlay`, `mounting-plate`, or `spacer-set`.

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

Use artifact overrides to generate variants from the same model, such as
`include_text=false`, instead of copying or forking source files.

Run `mise run package -- <project-id>` after changing a printable project. This
refreshes committed STL/STEP/PNG files, cost estimates, and the standard final
render. Use `mise run render -- <project-id>` when only the summary PNG needs to
be regenerated from existing artifact PNGs.

## Working With Downloaded Files

Users sometimes bring a file already downloaded from the internet (Thingiverse,
Printables, GrabCAD, a manufacturer's site) instead of describing a part from
scratch. There is no tool that turns an arbitrary file into clean parametric
code; what's possible depends on the format:

- **STEP (`.step`/`.stp`)** is a real BREP solid. It can be imported and
  modified with boolean ops, fillets, and holes.
- **STL** is a mesh with no feature history. Treat it as either a final
  printable artifact to use as-is, or a dimensional reference for hand-building
  a fresh parametric design.

Inspect any downloaded file before deciding how to use it:

```sh
.venv/bin/cad inspect downloaded_part.step
.venv/bin/cad inspect downloaded_part.stl --preview preview.png
```

Bring the file into a project as a committed reference, alongside the project's
manifest and README, under `projects/<project-id>/reference/`:

```sh
.venv/bin/cad import downloaded_part.step my-project --as-design my_part
```

`--as-design` (STEP only) scaffolds `projects/<project-id>/designs/<name>.py`
with a `build()` that calls `import_step()` on the reference file. Add spec
fields and boolean ops on top of the imported solid for whatever the user wants
changed. `cad import` always writes a quick PNG preview next to the reference
file (skip with `--no-preview`).

For an STL-only reference, there is no automatic conversion path. Use
`cad inspect` (and the preview PNG, or a viewer) to read off real dimensions,
then hand-build a normal parametric design under `projects/<project-id>/designs/`
that reproduces those dimensions as spec fields, per the usual "Adding A Shared
Design" workflow.

If the user just wants the downloaded file printed as-is with no modification,
skip designs entirely and place it directly as a committed artifact under
`projects/<project-id>/outputs/<artifact-slug>/`.

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

Then inspect `projects/<project-id>/outputs/overview.png` and the artifact PNGs
before handing work back.

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
