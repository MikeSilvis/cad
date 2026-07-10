from cad_workspace.cost import CostSettings, estimate_cost
from cad_workspace.cli import parse_overrides, to_pascal_case
from cad_workspace.exporter import export_model
from cad_workspace.model import coerce_value
from cad_workspace.projects import Project, ProjectArtifact, discover_projects
from cad_workspace.render import compose_labeled_grid, render_project, title_from_slug
from cad_workspace.registry import discover_models
from PIL import Image


def test_discovers_multiple_models():
    models = discover_models()

    assert "magsafe_desk_holder" in models
    assert "mounting_plate" in models
    assert "spacer" in models


def test_models_build_solid_parts():
    for model in discover_models().values():
        part = model.build(model.default_spec())

        assert part.volume > 0


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


def test_discovers_configured_projects(tmp_path):
    project_dir = tmp_path / "example-project"
    project_dir.mkdir()
    (project_dir / "project.toml").write_text(
        """
id = "example-project"
title = "Example Project"
description = "A test project."

[[artifact]]
slug = "printable-part"
model = "spacer"
formats = ["stl", "step", "png"]

[[artifact]]
slug = "printable-part-no-label"
model = "spacer"
formats = ["stl"]

[artifact.overrides]
height = 8
""".strip()
        + "\n"
    )

    projects = discover_projects(tmp_path)
    project = projects["example-project"]

    assert project.title == "Example Project"
    assert [artifact.slug for artifact in project.artifacts] == [
        "printable-part",
        "printable-part-no-label",
    ]
    assert [artifact.model for artifact in project.artifacts] == ["spacer", "spacer"]
    assert project.artifacts[1].overrides == {"height": "8"}


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


def test_render_project_writes_overview_to_outputs(tmp_path):
    project_path = tmp_path / "example"
    preview_path = project_path / "outputs" / "case" / "case.png"
    preview_path.parent.mkdir(parents=True)
    Image.new("RGB", (100, 60), (20, 80, 140)).save(preview_path)

    render_path = render_project(
        Project(
            project_id="example",
            title="Example",
            description="",
            path=project_path,
            artifacts=(
                ProjectArtifact(
                    slug="case",
                    model="example_case",
                    formats=("png",),
                    overrides={},
                ),
            ),
        )
    )

    assert render_path == project_path / "outputs" / "overview.png"
    assert render_path.exists()


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
