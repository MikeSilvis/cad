from dataclasses import dataclass
from pathlib import Path

from build123d import import_step

from cad_workspace.model import CadModel


REFERENCE_STEP = Path(__file__).resolve().parent.parent / "reference" / "REFERENCE_FILENAME"


@dataclass(frozen=True)
class NewDesignSpec:
    """All dimensions are millimeters.

    Add fields here for the modifications you make to the imported part
    (extra holes, trims, added features). The imported geometry itself is
    not parametric.
    """


def build(spec: NewDesignSpec):
    imported = import_step(REFERENCE_STEP)

    # Apply modifications on top of `imported` (boolean ops, fillets, holes)
    # using spec fields above, then return the result.
    return imported


MODEL = CadModel(
    name="new_design",
    description="Imported from REFERENCE_FILENAME. Replace this description once modified.",
    spec_type=NewDesignSpec,
    build=build,
)
