from dataclasses import dataclass

from build123d import (
    Box,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Plane,
    RectangleRounded,
    Text,
    add,
    extrude,
    mirror,
)

from cad_workspace.model import CadModel


@dataclass(frozen=True)
class TabA9GolfCaseSpec:
    """All dimensions are millimeters."""

    tablet_length: float = 211.0
    tablet_width: float = 124.7
    tablet_thickness: float = 8.0
    fit_clearance: float = 0.7
    back_thickness: float = 4.4
    corner_wall_thickness: float = 2.4
    corner_wall_height: float = 9.8
    side_rail_open_gap: float = 22.0
    front_lip_depth: float = 2.0
    front_lip_height: float = 1.2
    front_lip_clearance: float = 0.4
    snap_latch_width: float = 20.0
    snap_latch_thickness: float = 1.2
    snap_latch_depth: float = 1.6
    snap_latch_inset_from_side: float = 18.0
    top_mic_cutout_width: float = 14.0
    top_mic_cutout_depth: float = 5.4
    top_mic_cutout_height: float = 10.8
    side_button_cutout_length: float = 58.0
    side_button_cutout_depth: float = 5.6
    side_button_cutout_height: float = 10.8
    side_button_cutout_center_from_top: float = 55.0
    magnet_length: float = 60.0
    magnet_width: float = 10.0
    magnet_thickness: float = 3.0
    magnet_clearance: float = 0.35
    magnet_pocket_depth: float = 3.25
    magnet_pocket_overcut: float = 0.4
    magnet_rows: int = 3
    magnet_columns: int = 2
    magnet_gap: float = 8.0
    outside_corner_radius: float = 7.5
    rail_end_radius: float = 0.9
    snap_tab_radius: float = 0.45
    include_text: bool = True
    top_text: str = "Silly"
    bottom_text: str = "(814) 574-6139"
    top_text_font: str = "Snell Roundhand"
    bottom_text_font: str = "Avenir Next"
    top_text_font_size: float = 16.0
    bottom_text_font_size: float = 7.5
    top_text_y: float = 40.0
    bottom_text_y: float = -40.0
    text_inlay_depth: float = 0.45
    text_pocket_overcut: float = 0.15


def build(spec: TabA9GolfCaseSpec):
    validate_spec(spec)

    inner_length = spec.tablet_length + 2 * spec.fit_clearance
    inner_width = spec.tablet_width + 2 * spec.fit_clearance
    outer_length = inner_length + 2 * spec.corner_wall_thickness
    outer_width = inner_width + 2 * spec.corner_wall_thickness

    pocket_length = spec.magnet_length + spec.magnet_clearance
    pocket_width = spec.magnet_width + spec.magnet_clearance

    back_top_z = spec.back_thickness / 2
    corner_z = back_top_z + spec.corner_wall_height / 2
    lip_z = (
        back_top_z
        + spec.tablet_thickness
        + spec.front_lip_clearance
        + spec.front_lip_height / 2
    )
    back_bottom_z = -spec.back_thickness / 2
    pocket_cut_depth = spec.magnet_pocket_depth + spec.magnet_pocket_overcut
    pocket_z = back_bottom_z + spec.magnet_pocket_depth - pocket_cut_depth / 2

    with BuildPart() as case:
        add(
            rounded_box_xy(
                outer_length,
                outer_width,
                spec.back_thickness,
                center=(0, 0, 0),
                radius=spec.outside_corner_radius,
            )
        )

        add_slide_in_retention(spec, inner_length, inner_width, corner_z, lip_z)
        cut_device_controls(spec, inner_length, inner_width, back_top_z)
        cut_magnet_pockets(spec, pocket_length, pocket_width, pocket_cut_depth, pocket_z)
        if has_text(spec):
            cut_text_inlay_pockets(spec)

    return case.part


def build_text_inlay(spec: TabA9GolfCaseSpec):
    validate_spec(spec)

    if not has_text(spec):
        return disabled_text_placeholder()

    return text_features_part(spec, spec.text_inlay_depth, bottom_z_offset=0)


def add_slide_in_retention(
    spec: TabA9GolfCaseSpec,
    inner_length: float,
    inner_width: float,
    corner_z: float,
    lip_z: float,
) -> None:
    wall = spec.corner_wall_thickness
    rail_length = inner_length - spec.side_rail_open_gap
    rail_center_x = -inner_length / 2 + rail_length / 2

    for y_sign in (-1, 1):
        y_wall = y_sign * (inner_width / 2 + wall / 2)
        y_lip = y_sign * (inner_width / 2 - spec.front_lip_depth / 2)

        add(
            rounded_box_xy(
                rail_length,
                wall,
                spec.corner_wall_height,
                center=(rail_center_x, y_wall, corner_z),
                radius=spec.rail_end_radius,
            )
        )

        add(
            rounded_box_xy(
                rail_length,
                spec.front_lip_depth,
                spec.front_lip_height,
                center=(rail_center_x, y_lip, lip_z),
                radius=spec.rail_end_radius,
            )
        )

    closed_x = -inner_length / 2 - wall / 2
    add(
        rounded_box_xy(
            wall,
            inner_width + 2 * wall,
            spec.corner_wall_height,
            center=(closed_x, 0, corner_z),
            radius=spec.rail_end_radius,
        )
    )

    closed_lip_x = -inner_length / 2 + spec.front_lip_depth / 2
    add(
        rounded_box_xy(
            spec.front_lip_depth,
            inner_width,
            spec.front_lip_height,
            center=(closed_lip_x, 0, lip_z),
            radius=spec.rail_end_radius,
        )
    )

    # Screwless snap catches: thin upright tabs at the open end block slide-out.
    for y_sign in (-1, 1):
        y_latch = y_sign * (
            inner_width / 2 - spec.snap_latch_inset_from_side - spec.snap_latch_width / 2
        )
        latch_wall_x = inner_length / 2 + spec.snap_latch_thickness / 2
        latch_lip_x = inner_length / 2 - spec.snap_latch_depth / 2

        add(
            rounded_box_xy(
                spec.snap_latch_thickness,
                spec.snap_latch_width,
                spec.corner_wall_height,
                center=(latch_wall_x, y_latch, corner_z),
                radius=spec.snap_tab_radius,
            )
        )

        add(
            rounded_box_xy(
                spec.snap_latch_depth,
                spec.snap_latch_width,
                spec.front_lip_height,
                center=(latch_lip_x, y_latch, lip_z),
                radius=spec.snap_tab_radius,
            )
        )


def cut_device_controls(
    spec: TabA9GolfCaseSpec,
    inner_length: float,
    inner_width: float,
    back_top_z: float,
) -> None:
    wall = spec.corner_wall_thickness
    control_z = back_top_z + spec.side_button_cutout_height / 2

    top_mic_x = -inner_length / 2 - wall / 2
    add(
        rounded_box_xy(
            spec.top_mic_cutout_depth,
            spec.top_mic_cutout_width,
            spec.top_mic_cutout_height,
            center=(top_mic_x, 0, control_z),
            radius=spec.rail_end_radius,
        ),
        mode=Mode.SUBTRACT,
    )

    button_x = -inner_length / 2 + spec.side_button_cutout_center_from_top
    button_y = inner_width / 2 + wall / 2
    add(
        rounded_box_xy(
            spec.side_button_cutout_length,
            spec.side_button_cutout_depth,
            spec.side_button_cutout_height,
            center=(button_x, button_y, control_z),
            radius=spec.rail_end_radius,
        ),
        mode=Mode.SUBTRACT,
    )


def cut_magnet_pockets(
    spec: TabA9GolfCaseSpec,
    pocket_length: float,
    pocket_width: float,
    pocket_cut_depth: float,
    pocket_z: float,
) -> None:
    for x in centered_positions(spec.magnet_rows, pocket_length, spec.magnet_gap):
        for y in centered_positions(spec.magnet_columns, pocket_width, spec.magnet_gap):
            with Locations((x, y, pocket_z)):
                Box(pocket_length, pocket_width, pocket_cut_depth, mode=Mode.SUBTRACT)


def cut_text_inlay_pockets(spec: TabA9GolfCaseSpec) -> None:
    cut_depth = spec.text_inlay_depth + spec.text_pocket_overcut
    add(
        text_features_part(spec, cut_depth, bottom_z_offset=-spec.text_pocket_overcut),
        mode=Mode.SUBTRACT,
    )


def text_features_part(
    spec: TabA9GolfCaseSpec,
    depth: float,
    *,
    bottom_z_offset: float,
):
    back_bottom_z = -spec.back_thickness / 2

    with BuildPart() as text:
        with BuildSketch(Plane.XY.offset(back_bottom_z + bottom_z_offset)):
            if spec.top_text:
                with Locations((0, spec.top_text_y)):
                    Text(spec.top_text, font_size=spec.top_text_font_size, font=spec.top_text_font)
            if spec.bottom_text:
                with Locations((0, spec.bottom_text_y)):
                    Text(
                        spec.bottom_text,
                        font_size=spec.bottom_text_font_size,
                        font=spec.bottom_text_font,
                    )
        extrude(amount=depth)

    return mirror(text.part, about=Plane.XZ)


def has_text(spec: TabA9GolfCaseSpec) -> bool:
    return spec.include_text and bool(spec.top_text or spec.bottom_text)


def disabled_text_placeholder():
    with BuildPart() as placeholder:
        Box(0.1, 0.1, 0.1)

    return placeholder.part


def centered_positions(count: int, item_size: float, gap: float) -> list[float]:
    total = span(count, item_size, gap)
    first = -total / 2 + item_size / 2
    return [first + index * (item_size + gap) for index in range(count)]


def span(count: int, item_size: float, gap: float) -> float:
    return count * item_size + (count - 1) * gap


def rounded_box_xy(
    length: float,
    width: float,
    height: float,
    *,
    center: tuple[float, float, float],
    radius: float,
):
    clamped_radius = min(radius, length / 2 - 0.05, width / 2 - 0.05)
    x, y, z = center

    with BuildPart() as rounded:
        with BuildSketch(Plane.XY.offset(z - height / 2)):
            RectangleRounded(length, width, max(0.01, clamped_radius))
        extrude(amount=height)

    return rounded.part.translate((x, y, 0))


def validate_spec(spec: TabA9GolfCaseSpec) -> None:
    if spec.magnet_rows < 1 or spec.magnet_columns < 1:
        raise ValueError("magnet_rows and magnet_columns must be at least 1")
    if spec.magnet_pocket_depth < spec.magnet_thickness:
        raise ValueError("magnet_pocket_depth must be at least magnet_thickness")
    if spec.back_thickness <= spec.magnet_pocket_depth:
        raise ValueError("back_thickness must leave material behind the magnet pockets")
    required_wall_height = (
        spec.tablet_thickness + spec.front_lip_clearance + spec.front_lip_height
    )
    if spec.corner_wall_height < required_wall_height:
        raise ValueError("corner_wall_height must reach the top of the front lip")
    if spec.side_rail_open_gap <= spec.snap_latch_thickness:
        raise ValueError("side_rail_open_gap must leave room for the snap latches to flex")
    if spec.top_mic_cutout_width <= 0 or spec.top_mic_cutout_depth <= 0:
        raise ValueError("top mic cutout dimensions must be positive")
    if spec.side_button_cutout_length <= 0 or spec.side_button_cutout_depth <= 0:
        raise ValueError("side button cutout dimensions must be positive")
    if spec.side_button_cutout_center_from_top <= spec.side_button_cutout_length / 2:
        raise ValueError("side button cutout must stay inside the side rail")
    if (
        spec.side_button_cutout_center_from_top + spec.side_button_cutout_length / 2
        >= spec.tablet_length - spec.side_rail_open_gap
    ):
        raise ValueError("side button cutout must not run into the open-end latch area")
    if spec.text_inlay_depth <= 0:
        raise ValueError("text_inlay_depth must be positive")
    if spec.text_inlay_depth + spec.text_pocket_overcut >= spec.back_thickness:
        raise ValueError("text inlay pocket cannot cut through the back plate")


MODEL = CadModel(
    name="tab_a9_golf_case",
    description="Galaxy Tab A9 golf-cart case with recessed bar-magnet pockets.",
    spec_type=TabA9GolfCaseSpec,
    build=build,
)
