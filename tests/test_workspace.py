from cad_workspace.cost import CostSettings, estimate_cost
from cad_workspace.cli import parse_overrides, to_pascal_case
from cad_workspace.exporter import export_model
from cad_workspace.model import coerce_value
from cad_workspace.projects import discover_projects
from cad_workspace.render import compose_labeled_grid, title_from_slug
from cad_workspace.registry import discover_models
from designs.tab_a9_golf_case import TabA9GolfCaseSpec
from PIL import Image


def test_discovers_multiple_models():
    models = discover_models()

    assert "magsafe_desk_holder" in models
    assert "mounting_plate" in models
    assert "spacer" in models
    assert "tab_a9_golf_case" in models
    assert "tab_a9_golf_case_text" in models


def test_models_build_solid_parts():
    for model in discover_models().values():
        part = model.build(model.default_spec())

        assert part.volume > 0


def test_tab_a9_golf_case_defaults_match_magnet_layout():
    model = discover_models()["tab_a9_golf_case"]
    spec = model.default_spec()
    part = model.build(spec)

    assert isinstance(spec, TabA9GolfCaseSpec)
    assert spec.magnet_rows * spec.magnet_columns == 6
    assert spec.front_lip_clearance > 0
    assert spec.side_rail_open_gap > spec.snap_latch_thickness
    assert spec.include_text is True
    assert spec.top_text == "Silly"
    assert spec.bottom_text == "(814) 574-6139"
    assert spec.bottom_text_font == "Avenir Next"
    assert part.bounding_box().size.X > spec.tablet_length
    assert part.bounding_box().size.Y > spec.tablet_width


def test_tab_a9_golf_case_text_can_be_disabled():
    case_model = discover_models()["tab_a9_golf_case"]
    text_model = discover_models()["tab_a9_golf_case_text"]
    spec = case_model.spec_with_overrides({"include_text": "false"})

    assert spec.include_text is False
    assert case_model.build(spec).volume > 0
    assert text_model.build(spec).volume > 0


def test_cost_estimate_uses_density_price_and_multiplier():
    estimate = estimate_cost(
        "sample",
        1000,
        CostSettings(
            filament_density_g_cm3=1.25,
            filament_cost_per_kg=20,
            material_multiplier=1.1,
        ),
    )

    assert estimate.volume_cm3 == 1
    assert estimate.solid_mass_g == 1.25
    assert round(estimate.estimated_material_g, 4) == 1.375
    assert round(estimate.estimated_cost_usd, 4) == 0.0275


def test_discovers_configured_projects():
    projects = discover_projects()
    project = projects["tab-a9-golf-case"]

    assert project.title == "Samsung Galaxy Tab A9 Golf Case"
    assert [artifact.slug for artifact in project.artifacts] == ["case", "text-inlay"]
    assert [artifact.model for artifact in project.artifacts] == [
        "tab_a9_golf_case",
        "tab_a9_golf_case_text",
    ]


def test_export_model_can_use_project_artifact_names(tmp_path):
    model = discover_models()["spacer"]
    spec = model.default_spec()

    written = export_model(
        model,
        spec,
        tmp_path,
        ["stl"],
        directory_name="printable-spacer",
        file_stem="spacer-v1",
    )

    assert written == [tmp_path / "printable-spacer" / "spacer-v1.stl"]
    assert written[0].exists()


def test_render_helpers_make_standard_project_preview():
    image = compose_labeled_grid(
        [
            ("Case", Image.new("RGB", (100, 60), (20, 80, 140))),
            ("Text Inlay", Image.new("RGB", (80, 80), (140, 120, 80))),
        ]
    )

    assert image.size == (1864, 710)
    assert title_from_slug("text-inlay") == "Text Inlay"


def test_parameter_overrides_are_applied():
    model = discover_models()["mounting_plate"]
    spec = model.spec_with_overrides({"length": "120", "hole_diameter": "4.2"})

    assert spec.length == 120
    assert spec.hole_diameter == 4.2


def test_magsafe_holder_parameters_are_applied():
    model = discover_models()["magsafe_desk_holder"]
    spec = model.spec_with_overrides(
        {
            "face_angle_degrees": "28",
            "puck_clearance": "1.0",
            "face_drop": "48",
        }
    )

    assert spec.face_angle_degrees == 28
    assert spec.puck_clearance == 1.0
    assert spec.face_drop == 48


def test_cli_override_parser():
    assert parse_overrides(["length=120", "hole_diameter=4.2"]) == {
        "length": "120",
        "hole_diameter": "4.2",
    }


def test_boolean_coercion():
    assert coerce_value("true", bool) is True
    assert coerce_value("no", bool) is False


def test_pascal_case_design_name():
    assert to_pascal_case("phone_stand") == "PhoneStand"
