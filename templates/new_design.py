from dataclasses import dataclass

from build123d import Box, BuildPart

from cad_workspace.model import CadModel


@dataclass(frozen=True)
class NewDesignSpec:
    """All dimensions are millimeters."""

    length: float = 40
    width: float = 20
    height: float = 8


def build(spec: NewDesignSpec):
    with BuildPart() as part:
        Box(spec.length, spec.width, spec.height)

    return part.part


MODEL = CadModel(
    name="new_design",
    description="Short human description of what this part is for.",
    spec_type=NewDesignSpec,
    build=build,
)

