# CAD Workspace Instructions

This repo is a Python-first CAD workspace for AI-assisted 3D modeling.

## Default Approach

- Use `build123d` for new CAD models unless the user explicitly asks for OpenSCAD.
- Keep all dimensions in millimeters.
- Prefer parametric models with a frozen dataclass spec at the top of each design.
- Export STL for slicers, STEP for CAD interchange, and PNG for quick visual review.
- Keep generated exports out of git; they belong under `exports/`.

## Project Commands

Run commands from the repo root:

```sh
mise run setup
mise run list
mise run build
mise run validate
```

Useful direct CLI commands:

```sh
.venv/bin/cad list
.venv/bin/cad build all
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

## Validation

After changing CAD code, run:

```sh
mise run validate
```

This runs tests and exports every registered model. Inspect the generated PNGs under
`exports/<model-name>/` when shape or orientation matters.

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

