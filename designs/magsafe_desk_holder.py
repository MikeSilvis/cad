from dataclasses import dataclass
from math import atan2, cos, degrees, radians, sin

from build123d import Box, BuildPart, CounterSinkHole, Cylinder, Locations, Mode

from cad_workspace.model import CadModel


@dataclass(frozen=True)
class MagSafeDeskHolderSpec:
    """All dimensions are millimeters."""

    desk_plate_length: float = 110
    desk_plate_width: float = 52
    desk_plate_thickness: float = 6
    screw_diameter: float = 4.5
    screw_head_diameter: float = 8.5
    screw_spacing: float = 78
    cup_outer_diameter: float = 78
    magsafe_puck_diameter: float = 56.5
    puck_clearance: float = 0.7
    puck_pocket_depth: float = 6.8
    cup_thickness: float = 13
    face_angle_degrees: float = 22
    face_forward_offset: float = 76
    face_drop: float = 42
    rail_width: float = 8
    rail_thickness: float = 10
    rail_spacing: float = 34
    cable_slot_width: float = 9


def build(spec: MagSafeDeskHolderSpec):
    validate_spec(spec)

    face_center = (spec.face_forward_offset, 0, -spec.face_drop)
    face_rotation = (0, 90 - spec.face_angle_degrees, 0)
    face_angle = radians(spec.face_angle_degrees)
    normal = (cos(face_angle), 0, sin(face_angle))
    face_down = (sin(face_angle), 0, -cos(face_angle))

    cup_radius = spec.cup_outer_diameter / 2
    puck_radius = (spec.magsafe_puck_diameter + spec.puck_clearance) / 2
    pocket_center = offset_point(
        face_center,
        normal,
        spec.cup_thickness / 2 - spec.puck_pocket_depth / 2,
    )

    with BuildPart() as holder:
        Box(spec.desk_plate_length, spec.desk_plate_width, spec.desk_plate_thickness)

        with Locations(
            (-spec.screw_spacing / 2, 0, 0),
            (spec.screw_spacing / 2, 0, 0),
        ):
            CounterSinkHole(
                radius=spec.screw_diameter / 2,
                counter_sink_radius=spec.screw_head_diameter / 2,
            )

        for y in (-spec.rail_spacing / 2, spec.rail_spacing / 2):
            add_rail(
                start=(8, y, -spec.desk_plate_thickness / 2),
                end=offset_point(face_center, normal, -spec.cup_thickness / 2),
                width=spec.rail_width,
                thickness=spec.rail_thickness,
            )

        with Locations(face_center):
            Cylinder(
                radius=cup_radius,
                height=spec.cup_thickness,
                rotation=face_rotation,
            )

        with Locations(pocket_center):
            Cylinder(
                radius=puck_radius,
                height=spec.puck_pocket_depth + 0.4,
                rotation=face_rotation,
                mode=Mode.SUBTRACT,
            )

        cable_slot_length = cup_radius - puck_radius + 10
        slot_center = offset_point(
            pocket_center,
            face_down,
            puck_radius + cable_slot_length / 2 - 4,
        )
        with Locations(slot_center):
            Box(
                cable_slot_length,
                spec.cable_slot_width,
                spec.puck_pocket_depth + 1.4,
                rotation=face_rotation,
                mode=Mode.SUBTRACT,
            )

    return holder.part


def add_rail(
    *,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    width: float,
    thickness: float,
) -> None:
    center = (
        (start[0] + end[0]) / 2,
        (start[1] + end[1]) / 2,
        (start[2] + end[2]) / 2,
    )
    delta_x = end[0] - start[0]
    delta_z = end[2] - start[2]
    length = (delta_x**2 + delta_z**2) ** 0.5
    rotation_y = degrees(atan2(-delta_z, delta_x))

    with Locations(center):
        Box(length, width, thickness, rotation=(0, rotation_y, 0))


def offset_point(
    point: tuple[float, float, float],
    direction: tuple[float, float, float],
    distance: float,
) -> tuple[float, float, float]:
    return (
        point[0] + direction[0] * distance,
        point[1] + direction[1] * distance,
        point[2] + direction[2] * distance,
    )


def validate_spec(spec: MagSafeDeskHolderSpec) -> None:
    pocket_diameter = spec.magsafe_puck_diameter + spec.puck_clearance

    if pocket_diameter >= spec.cup_outer_diameter - 4:
        raise ValueError("MagSafe pocket must leave at least a 2 mm wall around the cup")
    if spec.puck_pocket_depth >= spec.cup_thickness:
        raise ValueError("MagSafe pocket depth must be shallower than the cup thickness")
    if spec.screw_spacing >= spec.desk_plate_length - spec.screw_head_diameter:
        raise ValueError("Screw spacing is too wide for the desk plate")
    if spec.rail_spacing + spec.rail_width >= spec.desk_plate_width:
        raise ValueError("Rails must fit within the desk plate width")


MODEL = CadModel(
    name="magsafe_desk_holder",
    description=(
        "Under-desk angled MagSafe puck holder with screw flange, twin rails, "
        "charger pocket, and cable slot."
    ),
    spec_type=MagSafeDeskHolderSpec,
    build=build,
)
