from dataclasses import dataclass

from build123d import Box, BuildPart, Hole, Locations

from cad_workspace.model import CadModel


@dataclass(frozen=True)
class MountingPlateSpec:
    """All dimensions are millimeters."""

    length: float = 80
    width: float = 36
    thickness: float = 4
    hole_diameter: float = 5
    hole_spacing: float = 54


def build(spec: MountingPlateSpec):
    with BuildPart() as plate:
        Box(spec.length, spec.width, spec.thickness)

        with Locations(
            (-spec.hole_spacing / 2, 0, 0),
            (spec.hole_spacing / 2, 0, 0),
        ):
            Hole(radius=spec.hole_diameter / 2)

    return plate.part


MODEL = CadModel(
    name="mounting_plate",
    description="Flat rectangular plate with two screw holes.",
    spec_type=MountingPlateSpec,
    build=build,
)

