from cad_workspace.model import CadModel
from cad_project_tab_a9_golf_case_tab_a9_golf_case import (
    TabA9GolfCaseSpec,
    build_text_inlay,
)


MODEL = CadModel(
    name="tab_a9_golf_case_text",
    description="Flush colored text inlays for the Galaxy Tab A9 golf-cart case.",
    spec_type=TabA9GolfCaseSpec,
    build=build_text_inlay,
)
