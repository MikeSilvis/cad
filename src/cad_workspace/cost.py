from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class CostSettings:
    """Material cost assumptions for a rough CAD-volume estimate."""

    filament_density_g_cm3: float = 1.27
    filament_cost_per_kg: float = 24.0
    material_multiplier: float = 1.12


@dataclass(frozen=True)
class CostEstimate:
    model_name: str
    volume_mm3: float
    volume_cm3: float
    solid_mass_g: float
    estimated_material_g: float
    estimated_cost_usd: float
    settings: CostSettings


def estimate_cost(model_name: str, volume_mm3: float, settings: CostSettings) -> CostEstimate:
    volume_cm3 = volume_mm3 / 1000
    solid_mass_g = volume_cm3 * settings.filament_density_g_cm3
    estimated_material_g = solid_mass_g * settings.material_multiplier
    estimated_cost_usd = estimated_material_g / 1000 * settings.filament_cost_per_kg

    return CostEstimate(
        model_name=model_name,
        volume_mm3=volume_mm3,
        volume_cm3=volume_cm3,
        solid_mass_g=solid_mass_g,
        estimated_material_g=estimated_material_g,
        estimated_cost_usd=estimated_cost_usd,
        settings=settings,
    )


def write_cost_estimate(model_dir: Path, estimate: CostEstimate) -> list[Path]:
    json_path = model_dir / "cost_estimate.json"
    txt_path = model_dir / "cost_estimate.txt"

    json_path.write_text(json.dumps(asdict(estimate), indent=2) + "\n")
    txt_path.write_text(format_cost_estimate(estimate))

    return [json_path, txt_path]


def format_cost_estimate(estimate: CostEstimate) -> str:
    return "\n".join(
        [
            f"Model: {estimate.model_name}",
            "",
            "Rough material estimate from CAD solid volume.",
            "Slicer settings such as infill, walls, supports, purge, and brim will change the final cost.",
            "",
            f"Volume: {estimate.volume_cm3:.2f} cm^3 ({estimate.volume_mm3:.0f} mm^3)",
            f"Solid material mass: {estimate.solid_mass_g:.1f} g",
            f"Estimated print material: {estimate.estimated_material_g:.1f} g",
            f"Estimated material cost: ${estimate.estimated_cost_usd:.2f}",
            "",
            "Assumptions:",
            f"- Filament density: {estimate.settings.filament_density_g_cm3:.2f} g/cm^3",
            f"- Filament cost: ${estimate.settings.filament_cost_per_kg:.2f}/kg",
            f"- Material multiplier: {estimate.settings.material_multiplier:.2f}x",
            "",
        ]
    )
