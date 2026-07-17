from dataclasses import dataclass

from build123d import (
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Locations,
    Mode,
    Plane,
    RectangleRounded,
    add,
    extrude,
)

from cad_workspace.model import CadModel


@dataclass(frozen=True)
class XboxEliteIndexCardHolderSpec:
    """All dimensions are millimeters."""

    card_width: float = 127.0
    card_height: float = 76.2
    card_side_clearance: float = 0.6
    card_slot_depth: float = 1.2
    backplate_height: float = 68.0
    backplate_thickness: float = 2.4
    backplate_corner_radius: float = 6.0
    edge_wall_thickness: float = 2.4
    front_lip_thickness: float = 1.8
    front_lip_height: float = 14.0
    side_rail_height: float = 32.0
    thumb_notch_radius: float = 10.0
    controller_top_depth: float = 38.0
    controller_top_height: float = 22.0
    fit_clearance: float = 0.6
    clip_wall_thickness: float = 2.4
    clip_corner_radius: float = 8.0
    clip_hook_engagement: float = 1.3
    clip_opening_rise: float = 2.0
    clip_band_width: float = 10.0
    clip_band_spacing: float = 44.0
    mount_post_depth: float = 7.0
    port_clearance_height: float = 18.0
    crossbar_height: float = 4.0
    connector_flange_width: float = 36.0
    connector_flange_depth: float = 8.0
    connector_flange_height: float = 3.0
    connector_tongue_width: float = 28.0
    connector_tongue_depth: float = 4.8
    connector_tongue_height: float = 17.0
    connector_taper: float = 0.8
    connector_clearance: float = 0.3
    connector_socket_wall: float = 2.2
    connector_socket_height: float = 19.0
    fit_test_band_width: float = 8.0
    fit_test_tab_width: float = 18.0
    fit_test_tab_depth: float = 7.0
    fit_test_tab_height: float = 3.0


def build_card_holder(spec: XboxEliteIndexCardHolderSpec):
    validate_spec(spec)

    inner_width = spec.card_width + spec.card_side_clearance
    backplate_width = inner_width + 2 * spec.edge_wall_thickness
    bottom_z = -spec.backplate_height / 2
    front_face_y = -spec.backplate_thickness / 2
    pocket_front_y = front_face_y - spec.card_slot_depth - spec.front_lip_thickness
    pocket_back_y = spec.backplate_thickness / 2
    pocket_depth = pocket_back_y - pocket_front_y
    pocket_center_y = (pocket_front_y + pocket_back_y) / 2
    front_lip_y = front_face_y - spec.card_slot_depth - spec.front_lip_thickness / 2

    socket_width = spec.connector_tongue_width + 2 * (
        spec.connector_clearance + spec.connector_socket_wall
    )
    socket_depth = spec.connector_tongue_depth + 2 * (
        spec.connector_clearance + spec.connector_socket_wall
    )
    socket_front_y = spec.backplate_thickness / 2 - 0.2
    socket_center_y = socket_front_y + socket_depth / 2
    cavity_depth = spec.connector_tongue_depth + 2 * spec.connector_clearance
    cavity_front_y = socket_front_y + spec.connector_socket_wall
    cavity_center_y = cavity_front_y + cavity_depth / 2
    cavity_height = spec.connector_tongue_height + 1.0
    cavity_bottom_z = bottom_z - 0.5

    with BuildPart() as holder:
        add(
            rounded_plate_xz(
                backplate_width,
                spec.backplate_height,
                spec.backplate_thickness,
                spec.backplate_corner_radius,
            )
        )

        with Locations(
            (
                0,
                pocket_center_y,
                bottom_z + spec.edge_wall_thickness / 2,
            )
        ):
            Box(backplate_width, pocket_depth, spec.edge_wall_thickness)

        with Locations(
            (
                0,
                front_lip_y,
                bottom_z + spec.front_lip_height / 2,
            )
        ):
            Box(
                inner_width + 0.4,
                spec.front_lip_thickness,
                spec.front_lip_height,
            )

        side_rail_x = inner_width / 2 + spec.edge_wall_thickness / 2
        with Locations(
            (
                -side_rail_x,
                pocket_center_y,
                bottom_z + spec.side_rail_height / 2,
            ),
            (
                side_rail_x,
                pocket_center_y,
                bottom_z + spec.side_rail_height / 2,
            ),
        ):
            Box(spec.edge_wall_thickness, pocket_depth, spec.side_rail_height)

        with Locations(
            (
                0,
                socket_center_y,
                bottom_z + spec.connector_socket_height / 2,
            )
        ):
            Box(socket_width, socket_depth, spec.connector_socket_height)

        with Locations(
            (
                0,
                cavity_center_y,
                cavity_bottom_z + cavity_height / 2,
            )
        ):
            Box(
                spec.connector_tongue_width + 2 * spec.connector_clearance,
                cavity_depth,
                cavity_height,
                mode=Mode.SUBTRACT,
            )

        with Locations((0, 0, spec.backplate_height / 2)):
            Cylinder(
                radius=spec.thumb_notch_radius,
                height=spec.backplate_thickness + 2,
                rotation=(90, 0, 0),
                mode=Mode.SUBTRACT,
            )

    return holder.part


def build_controller_mount(spec: XboxEliteIndexCardHolderSpec):
    validate_spec(spec)

    outer_height = clip_outer_height(spec)
    outer_top_z = outer_height / 2
    post_bottom_z = outer_top_z - 1.0
    post_top_z = outer_top_z + spec.port_clearance_height
    post_height = post_top_z - post_bottom_z
    crossbar_bottom_z = post_top_z - 1.0
    crossbar_top_z = crossbar_bottom_z + spec.crossbar_height
    flange_bottom_z = crossbar_top_z - 0.5
    flange_top_z = flange_bottom_z + spec.connector_flange_height
    tongue_bottom_z = flange_top_z - 0.5
    overall_band_width = spec.clip_band_spacing + spec.clip_band_width

    with BuildPart() as mount:
        band = snap_band(spec, spec.clip_band_width)
        for x in (-spec.clip_band_spacing / 2, spec.clip_band_spacing / 2):
            add(band.translate((x, 0, 0)))

        with Locations(
            (
                -spec.clip_band_spacing / 2,
                0,
                post_bottom_z + post_height / 2,
            ),
            (
                spec.clip_band_spacing / 2,
                0,
                post_bottom_z + post_height / 2,
            ),
        ):
            Box(spec.clip_band_width, spec.mount_post_depth, post_height)

        with Locations(
            (
                0,
                0,
                crossbar_bottom_z + spec.crossbar_height / 2,
            )
        ):
            Box(overall_band_width, spec.mount_post_depth, spec.crossbar_height)

        with Locations(
            (
                0,
                0,
                flange_bottom_z + spec.connector_flange_height / 2,
            )
        ):
            Box(
                spec.connector_flange_width,
                spec.connector_flange_depth,
                spec.connector_flange_height,
            )

        add(tapered_connector_tongue(spec, tongue_bottom_z))

    return mount.part


def build_clip_fit_test(spec: XboxEliteIndexCardHolderSpec):
    validate_spec(spec)

    outer_top_z = clip_outer_height(spec) / 2

    with BuildPart() as fit_test:
        add(snap_band(spec, spec.fit_test_band_width))
        with Locations(
            (
                0,
                0,
                outer_top_z + spec.fit_test_tab_height / 2 - 0.4,
            )
        ):
            Box(
                spec.fit_test_tab_width,
                spec.fit_test_tab_depth,
                spec.fit_test_tab_height,
            )

    return fit_test.part


def snap_band(spec: XboxEliteIndexCardHolderSpec, band_width: float):
    inner_depth = spec.controller_top_depth + 2 * spec.fit_clearance
    inner_height = spec.controller_top_height + 2 * spec.fit_clearance
    outer_depth = inner_depth + 2 * spec.clip_wall_thickness
    outer_height = inner_height + 2 * spec.clip_wall_thickness
    outer_radius = min(
        spec.clip_corner_radius,
        outer_depth / 2 - 0.05,
        outer_height / 2 - 0.05,
    )
    inner_radius = min(
        outer_radius - spec.clip_wall_thickness,
        inner_depth / 2 - 0.05,
        inner_height / 2 - 0.05,
    )
    opening_width = inner_depth - 2 * spec.clip_hook_engagement
    opening_bottom_z = -outer_height / 2 - 0.5
    opening_top_z = -inner_height / 2 + spec.clip_opening_rise
    opening_height = opening_top_z - opening_bottom_z

    with BuildPart() as band:
        with BuildSketch(Plane.YZ):
            RectangleRounded(outer_depth, outer_height, outer_radius)
            RectangleRounded(
                inner_depth,
                inner_height,
                inner_radius,
                mode=Mode.SUBTRACT,
            )
        extrude(amount=band_width / 2, both=True)

        with Locations((0, 0, opening_bottom_z + opening_height / 2)):
            Box(
                band_width + 2,
                opening_width,
                opening_height,
                mode=Mode.SUBTRACT,
            )

    return band.part


def tapered_connector_tongue(
    spec: XboxEliteIndexCardHolderSpec,
    bottom_z: float,
):
    lower_height = spec.connector_tongue_height - spec.connector_taper

    with BuildPart() as tongue:
        with Locations(
            (
                0,
                0,
                bottom_z + lower_height / 2,
            )
        ):
            Box(
                spec.connector_tongue_width,
                spec.connector_tongue_depth,
                lower_height,
            )

        with Locations(
            (
                0,
                0,
                bottom_z + lower_height + spec.connector_taper / 2,
            )
        ):
            Box(
                spec.connector_tongue_width - 2 * spec.connector_taper,
                spec.connector_tongue_depth,
                spec.connector_taper,
            )

    return tongue.part


def rounded_plate_xz(
    width: float,
    height: float,
    thickness: float,
    radius: float,
):
    clamped_radius = min(radius, width / 2 - 0.05, height / 2 - 0.05)

    with BuildPart() as plate:
        with BuildSketch(Plane.XZ):
            RectangleRounded(width, height, clamped_radius)
        extrude(amount=thickness / 2, both=True)

    return plate.part


def clip_outer_height(spec: XboxEliteIndexCardHolderSpec) -> float:
    return (
        spec.controller_top_height
        + 2 * spec.fit_clearance
        + 2 * spec.clip_wall_thickness
    )


def validate_spec(spec: XboxEliteIndexCardHolderSpec) -> None:
    positive_dimensions = {
        "card_width": spec.card_width,
        "card_height": spec.card_height,
        "card_slot_depth": spec.card_slot_depth,
        "backplate_height": spec.backplate_height,
        "backplate_thickness": spec.backplate_thickness,
        "edge_wall_thickness": spec.edge_wall_thickness,
        "controller_top_depth": spec.controller_top_depth,
        "controller_top_height": spec.controller_top_height,
        "clip_wall_thickness": spec.clip_wall_thickness,
        "clip_band_width": spec.clip_band_width,
        "connector_tongue_width": spec.connector_tongue_width,
        "connector_tongue_depth": spec.connector_tongue_depth,
        "connector_tongue_height": spec.connector_tongue_height,
    }
    non_positive = sorted(name for name, value in positive_dimensions.items() if value <= 0)
    if non_positive:
        raise ValueError(f"dimensions must be positive: {', '.join(non_positive)}")
    if spec.card_side_clearance < 0 or spec.fit_clearance < 0:
        raise ValueError("fit clearances cannot be negative")
    if spec.backplate_height >= spec.card_height:
        raise ValueError("backplate_height must leave the card exposed above the holder")
    if spec.side_rail_height > spec.backplate_height:
        raise ValueError("side rails cannot be taller than the backplate")
    if spec.front_lip_height > spec.side_rail_height:
        raise ValueError("front lip cannot be taller than the side rails")
    if spec.thumb_notch_radius >= spec.backplate_height / 2:
        raise ValueError("thumb notch is too large for the backplate")
    if spec.clip_corner_radius <= spec.clip_wall_thickness:
        raise ValueError("clip corner radius must exceed clip wall thickness")
    inner_depth = spec.controller_top_depth + 2 * spec.fit_clearance
    if 2 * spec.clip_hook_engagement >= inner_depth:
        raise ValueError("clip hooks leave no bottom opening")
    if spec.clip_band_spacing - spec.clip_band_width < 18:
        raise ValueError("clip bands must leave at least 18 mm of center clearance")
    if spec.mount_post_depth > spec.controller_top_depth:
        raise ValueError("mount posts cannot be deeper than the controller profile")
    if spec.connector_taper * 2 >= spec.connector_tongue_width:
        raise ValueError("connector taper is too large for the tongue")
    if spec.connector_tongue_height + 1 > spec.connector_socket_height:
        raise ValueError("connector socket must be taller than the inserted tongue")


CARD_HOLDER_MODEL = CadModel(
    name="xbox_elite_index_card_holder",
    description="Landscape 3x5 index-card tray with a thumb notch and mount socket.",
    spec_type=XboxEliteIndexCardHolderSpec,
    build=build_card_holder,
)

CONTROLLER_MOUNT_MODEL = CadModel(
    name="xbox_elite_controller_mount",
    description="Twin snap-band Xbox Elite Series 2 top mount with a raised connector.",
    spec_type=XboxEliteIndexCardHolderSpec,
    build=build_controller_mount,
)

CLIP_FIT_TEST_MODEL = CadModel(
    name="xbox_elite_clip_fit_test",
    description="Low-material fit gauge for the Xbox Elite Series 2 snap-band profile.",
    spec_type=XboxEliteIndexCardHolderSpec,
    build=build_clip_fit_test,
)

MODELS = (CARD_HOLDER_MODEL, CONTROLLER_MOUNT_MODEL, CLIP_FIT_TEST_MODEL)
