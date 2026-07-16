from build123d import Box, BuildPart, export_step, export_stl

from cad_workspace.cost import CostSettings, estimate_cost
from cad_workspace.cli import parse_overrides, scaffold_imported_design, to_pascal_case
from cad_workspace.exporter import export_model
from cad_workspace.imports import format_inspection, import_reference_file, inspect_file
from cad_workspace.model import coerce_value
from cad_workspace.projects import Project, ProjectArtifact, discover_projects
from cad_workspace.render import compose_labeled_grid, render_project, title_from_slug
from cad_workspace.registry import discover_models, import_module_from_path
from PIL import Image


def test_discovers_multiple_models():
    models = discover_models()

    assert "magsafe_desk_holder" in models
    assert "mounting_plate" in models
    assert "spacer" in models
    assert "tab_a9_golf_case" in models
    assert "tab_a9_golf_case_text" in models


def test_discovers_tab_a9_project_local_models():
    models = discover_models()

    assert models["tab_a9_golf_case"].build.__module__.startswith("cad_project_tab_a9_golf_case")
    assert models["tab_a9_golf_case_text"].build.__module__.startswith(
        "cad_project_tab_a9_golf_case"
    )
    assert (
        models["tab_a9_golf_case"].build.__module__
        == models["tab_a9_golf_case_text"].build.__module__
    )


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


def test_tab_a9_golf_case_defaults_match_printable_layout():
    model = discover_models()["tab_a9_golf_case"]
    spec = model.default_spec()
    part = model.build(spec)

    assert type(spec).__name__ == "TabA9GolfCaseSpec"
    assert spec.magnet_rows * spec.magnet_columns == 6
    assert spec.back_thickness - spec.magnet_pocket_depth >= 1.5
    assert spec.side_rail_open_gap > spec.snap_latch_thickness
    assert spec.include_text is True
    assert spec.top_text == "Silly"
    assert spec.bottom_text == "(814) 574-6139"
    assert spec.side_button_cutout_depth > spec.corner_wall_thickness + spec.front_lip_depth
    assert spec.bottom_left_retainer_height > 0
    assert spec.bottom_left_retainer_height < spec.tablet_width / 2
    assert spec.bottom_speaker_cutout_width > spec.snap_latch_width
    assert part.bounding_box().size.X > spec.tablet_length
    assert part.bounding_box().size.Y > spec.tablet_width

    inner_length = spec.tablet_length + 2 * spec.fit_clearance
    inner_width = spec.tablet_width + 2 * spec.fit_clearance
    wall_center_z = spec.back_thickness / 2 + spec.corner_wall_height / 2
    top_wall_center = (
        -inner_length / 2 - spec.corner_wall_thickness / 2,
        0,
        wall_center_z,
    )
    top_lip_center = (
        -inner_length / 2 + spec.front_lip_depth / 2,
        0,
        spec.back_thickness / 2
        + spec.tablet_thickness
        + spec.front_lip_clearance
        + spec.front_lip_height / 2,
    )
    bottom_stop_center = (
        inner_length / 2 + spec.snap_latch_thickness / 2,
        -(inner_width / 2 - spec.snap_latch_inset_from_side - spec.snap_latch_width / 2),
        wall_center_z,
    )
    joined_stop_center = (
        inner_length / 2 + spec.snap_latch_thickness / 2,
        -inner_width / 2 + spec.bottom_left_retainer_height + 1,
        wall_center_z,
    )

    assert not part.is_inside(top_wall_center)
    assert not part.is_inside(top_lip_center)
    assert part.is_inside(bottom_stop_center)
    assert part.is_inside(joined_stop_center)


def test_tab_a9_text_can_be_disabled_from_same_model():
    case_model = discover_models()["tab_a9_golf_case"]
    text_model = discover_models()["tab_a9_golf_case_text"]
    spec = case_model.spec_with_overrides({"include_text": "false"})

    assert spec.include_text is False
    assert case_model.build(spec).volume > 0
    assert text_model.build(spec).volume > 0


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


def test_tab_a9_project_manifest_outputs():
    projects = discover_projects()
    project = projects["tab-a9-golf-case"]

    assert project.title == "Samsung Galaxy Tab A9 Golf Case"
    assert [artifact.slug for artifact in project.artifacts] == [
        "case",
        "case-no-text",
        "text-inlay",
    ]
    assert [artifact.model for artifact in project.artifacts] == [
        "tab_a9_golf_case",
        "tab_a9_golf_case",
        "tab_a9_golf_case_text",
    ]
    assert project.artifacts[1].overrides == {"include_text": "False"}


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


def _write_sample_box(tmp_path, suffix):
    with BuildPart() as part:
        Box(40, 20, 8)

    path = tmp_path / f"box{suffix}"
    if suffix == ".stl":
        export_stl(part.part, path)
    else:
        export_step(part.part, path)
    return path


def test_inspect_file_reports_step_bounding_box_and_volume(tmp_path):
    step_path = _write_sample_box(tmp_path, ".step")

    inspection = inspect_file(step_path)

    assert inspection.file_format == "step"
    assert inspection.size_x_mm == 40
    assert inspection.size_y_mm == 20
    assert inspection.size_z_mm == 8
    assert inspection.solid_count == 1
    assert round(inspection.volume_mm3) == 6400
    assert "volume:" in format_inspection(inspection)


def test_inspect_file_reports_stl_bounding_box_without_volume(tmp_path):
    stl_path = _write_sample_box(tmp_path, ".stl")

    inspection = inspect_file(stl_path)

    assert inspection.file_format == "stl"
    assert round(inspection.size_x_mm) == 40
    assert inspection.volume_mm3 is None
    assert inspection.solid_count is None
    assert "mesh reference" in format_inspection(inspection)


def test_inspect_file_rejects_unsupported_format(tmp_path):
    bad_path = tmp_path / "model.obj"
    bad_path.write_text("not a real model")

    try:
        inspect_file(bad_path)
        assert False, "expected ValueError"
    except ValueError as error:
        assert "Unsupported file format" in str(error)


def test_import_reference_file_copies_into_project_reference_dir(tmp_path):
    step_path = _write_sample_box(tmp_path, ".step")
    (tmp_path / "widget-project").mkdir()

    destination = import_reference_file(step_path, "widget-project", tmp_path)

    assert destination == tmp_path / "widget-project" / "reference" / "box.step"
    assert destination.exists()


def test_import_reference_file_rejects_unknown_project(tmp_path):
    step_path = _write_sample_box(tmp_path, ".step")

    try:
        import_reference_file(step_path, "missing-project", tmp_path)
        assert False, "expected ValueError"
    except ValueError as error:
        assert "Unknown project" in str(error)


def test_scaffold_imported_design_produces_buildable_model(tmp_path):
    step_path = _write_sample_box(tmp_path, ".step")
    (tmp_path / "widget-project").mkdir()
    reference_path = import_reference_file(step_path, "widget-project", tmp_path)

    design_path = scaffold_imported_design(
        "widget_body", "widget-project", tmp_path, reference_path
    )

    assert "widget_body" in design_path.read_text()
    assert "box.step" in design_path.read_text()
    assert "class WidgetBodySpec" in design_path.read_text()

    module = import_module_from_path("test_widget_body_module", design_path)
    built = module.MODEL.build(module.MODEL.default_spec())

    assert built.volume > 0
