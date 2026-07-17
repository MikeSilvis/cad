# Xbox Elite Series 2 Index Card Holder

Modular landscape holder for a standard 3 × 5 inch (127 × 76.2 mm) index card.
Two spring bands snap around the top-center shell of an Xbox Elite Wireless
Controller Series 2 (Microsoft model 1797), while a raised bridge leaves a
34 mm-wide center corridor for the USB-C area. The card tray slides onto the
mount's tapered tongue and stops against the shoulder below it.

The controller-shell dimensions are adjustable starter measurements because the
manufacturer does not publish a mechanical interface drawing for the top shell.
Print `clip-fit-test` first. It uses the same profile as both mount bands while
consuming much less material.

## Artifacts

- `outputs/card-holder/` contains the landscape card tray with an open top,
  1.2 mm card slot, front retaining rail, side rails, thumb notch, and rear socket.
- `outputs/controller-mount/` contains the twin snap bands, raised USB-C corridor,
  bridge, stop shoulder, and tapered connector tongue.
- `outputs/clip-fit-test/` contains one short snap band with a pull tab for checking
  shell fit before printing the full mount.
- `outputs/overview.png` is the standard project render.

## Fit and assembly

1. Print `clip-fit-test` in PETG with the band axis vertical, 0.2 mm layers, and at
   least four walls. Flex it over one of the two top-center shell areas beside the
   USB-C port; do not force it over buttons or a shoulder control.
2. If it is too tight, increase `fit_clearance` in
   `designs/xbox_elite_index_card_holder.py` by 0.2 mm. If the shell profile itself
   is larger, adjust `controller_top_depth` or `controller_top_height` from a
   caliper measurement and repackage the project.
3. Print the full controller mount in PETG or another fatigue-resistant filament.
   Avoid brittle silk PLA for the spring bands.
4. Slide the card holder down over the tapered tongue until its socket seats on the
   mount shoulder. Insert the index card from the open top.

The default 1.2 mm slot holds one card loosely or a small stack. Change
`card_slot_depth` for thicker laminated cards. Remove the mount before placing the
controller in its charging case, and inspect the snap bands for cracking before use.

Refresh all committed artifacts with:

```sh
mise run package -- xbox-elite-index-card-holder
```
