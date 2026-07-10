from cad_workspace.cli import parse_overrides, to_pascal_case
from cad_workspace.model import coerce_value
from cad_workspace.registry import discover_models


def test_discovers_multiple_models():
    models = discover_models()

    assert "mounting_plate" in models
    assert "spacer" in models


def test_models_build_solid_parts():
    for model in discover_models().values():
        part = model.build(model.default_spec())

        assert part.volume > 0


def test_parameter_overrides_are_applied():
    model = discover_models()["mounting_plate"]
    spec = model.spec_with_overrides({"length": "120", "hole_diameter": "4.2"})

    assert spec.length == 120
    assert spec.hole_diameter == 4.2


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
