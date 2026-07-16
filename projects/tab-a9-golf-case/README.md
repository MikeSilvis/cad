# Samsung Galaxy Tab A9 Golf Case

Magnetic case for the Samsung Galaxy Tab A9 8.7-inch tablet. The case body uses
recessed pockets for six adhesive-backed bar magnets and an open top so the tablet
slides down between the side rails. Gravity seats it against the lower retaining
tabs. The default case includes a clean right-side power/volume button relief, a
bottom-right speaker relief, and a continuous bottom-left retainer that stops before
the USB-C area. The rails and lower stop share one continuous rounded corner, with
a short return around the speaker-side corner.

## Artifacts

- `designs/` contains the project-local parametric source models.
- `outputs/case/` contains the main printable case body with rear text pockets.
- `outputs/case-no-text/` contains the same case generated with `include_text=false`.
- `outputs/text-inlay/` contains the separate flush rear lettering for a second filament color.
- `outputs/overview.png` is the standard final project render.

Refresh committed files with:

```sh
mise run package -- tab-a9-golf-case
```

The rear text can be removed for scratch exports with:

```sh
.venv/bin/cad build tab_a9_golf_case --set include_text=false
```
