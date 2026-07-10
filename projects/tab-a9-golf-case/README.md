# Samsung Galaxy Tab A9 Golf Case

Magnetic case for the Samsung Galaxy Tab A9 8.7-inch tablet. The case body uses
recessed pockets for six adhesive-backed bar magnets, slide-in side retention,
and screwless snap catches at the open end.

## Artifacts

- `artifacts/case/` contains the main printable case body.
- `artifacts/text-inlay/` contains the separate flush rear lettering for a second filament color.
- `renders/tab-a9-golf-case_final.png` is the standard final project render.

Refresh committed files with:

```sh
mise run package -- tab-a9-golf-case
```

The rear text can be removed for scratch exports with:

```sh
.venv/bin/cad build tab_a9_golf_case --set include_text=false
```
