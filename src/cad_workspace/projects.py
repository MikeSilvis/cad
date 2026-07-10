from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cad_workspace.cost import CostSettings
from cad_workspace.exporter import SUPPORTED_FORMATS, export_model, normalize_formats
from cad_workspace.model import SpecError
from cad_workspace.registry import discover_models
from cad_workspace.render import render_project


DEFAULT_PROJECTS_ROOT = Path("projects")
PROJECT_OUTPUTS_DIR = "outputs"


@dataclass(frozen=True)
class ProjectArtifact:
    slug: str
    model: str
    formats: tuple[str, ...]
    overrides: dict[str, str]


@dataclass(frozen=True)
class Project:
    project_id: str
    title: str
    description: str
    path: Path
    artifacts: tuple[ProjectArtifact, ...]


def discover_projects(projects_root: Path = DEFAULT_PROJECTS_ROOT) -> dict[str, Project]:
    if not projects_root.exists():
        return {}

    projects: dict[str, Project] = {}
    for manifest_path in sorted(projects_root.glob("*/project.toml")):
        project = load_project_manifest(manifest_path)
        if project.project_id in projects:
            raise ValueError(f"Duplicate project id: {project.project_id}")
        projects[project.project_id] = project

    return projects


def load_project(project_id: str, projects_root: Path = DEFAULT_PROJECTS_ROOT) -> Project:
    manifest_path = projects_root / project_id / "project.toml"
    if not manifest_path.exists():
        available = ", ".join(discover_projects(projects_root)) or "none"
        raise ValueError(f"Unknown project {project_id!r}. Available projects: {available}")

    return load_project_manifest(manifest_path)


def load_project_manifest(manifest_path: Path) -> Project:
    data = tomllib.loads(manifest_path.read_text())
    project_id = read_required_string(data, "id", manifest_path)
    artifacts = tuple(parse_artifact(item, manifest_path) for item in data.get("artifact", []))

    if manifest_path.parent.name != project_id:
        raise ValueError(
            f"{manifest_path} id must match its directory name: {manifest_path.parent.name}"
        )
    if not artifacts:
        raise ValueError(f"{manifest_path} must define at least one [[artifact]]")
    if len({artifact.slug for artifact in artifacts}) != len(artifacts):
        raise ValueError(f"{manifest_path} has duplicate artifact slugs")

    return Project(
        project_id=project_id,
        title=read_required_string(data, "title", manifest_path),
        description=str(data.get("description", "")),
        path=manifest_path.parent,
        artifacts=artifacts,
    )


def parse_artifact(data: dict[str, Any], manifest_path: Path) -> ProjectArtifact:
    slug = read_required_string(data, "slug", manifest_path)
    model = read_required_string(data, "model", manifest_path)
    formats = tuple(data.get("formats", SUPPORTED_FORMATS))
    overrides = {str(key): str(value) for key, value in data.get("overrides", {}).items()}

    if not slug.replace("-", "_").isidentifier():
        raise ValueError(f"{manifest_path} artifact slug must be identifier-like: {slug!r}")

    return ProjectArtifact(
        slug=slug,
        model=model,
        formats=normalize_formats(formats),
        overrides=overrides,
    )


def package_project(
    project: Project,
    *,
    cost_settings: CostSettings | None,
) -> list[Path]:
    models = discover_models()
    outputs_root = project.path / PROJECT_OUTPUTS_DIR
    written: list[Path] = []

    for artifact in project.artifacts:
        if artifact.model not in models:
            available = ", ".join(models)
            raise ValueError(
                f"{project.project_id} references unknown model {artifact.model!r}. "
                f"Available models: {available}"
            )

        model = models[artifact.model]
        try:
            spec = model.spec_with_overrides(artifact.overrides)
        except SpecError as error:
            raise ValueError(f"{project.project_id}/{artifact.slug}: {error}") from error

        written.extend(
            export_model(
                model,
                spec,
                outputs_root,
                artifact.formats,
                cost_settings,
                directory_name=artifact.slug,
                file_stem=artifact.slug,
            )
        )

    render_path = render_project(project)
    if render_path is not None:
        written.append(render_path)

    return written


def read_required_string(data: dict[str, Any], key: str, manifest_path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{manifest_path} must define a non-empty {key!r}")
    return value
