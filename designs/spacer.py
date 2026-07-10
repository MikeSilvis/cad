from dataclasses import dataclass

from build123d import BuildPart, Cylinder, Hole

from cad_workspace.model import CadModel


@dataclass(frozen=True)
class SpacerSpec:
    """All dimensions are millimeters."""

    outer_diameter: float = 18
    inner_diameter: float = 5.2
    height: float = 10


def build(spec: SpacerSpec):
    with BuildPart() as spacer:
        Cylinder(radius=spec.outer_diameter / 2, height=spec.height)
        Hole(radius=spec.inner_diameter / 2)

    return spacer.part


MODEL = CadModel(
    name="spacer",
    description="Round spacer or bushing with a centered through-hole.",
    spec_type=SpacerSpec,
    build=build,
)

