# CAD Workspace Instructions

Codex agents should follow the same CAD workflow described in `CLAUDE.md`.

## Required Project Layout

For any user-facing printable object, create or update:

```text
projects/<project-id>/
  project.toml
  README.md
  artifacts/<artifact-slug>/
    <artifact-slug>.stl
    <artifact-slug>.step
    <artifact-slug>.png
    cost_estimate.json
    cost_estimate.txt
  renders/<project-id>_final.png
```

- Keep source models in `designs/` with snake_case model names.
- Use kebab-case for `projects/<project-id>` and artifact slugs.
- Treat `exports/` as scratch output; committed generated CAD files belong only
  under `projects/<project-id>/artifacts/`.
- Run `mise run package -- <project-id>` after changing a project so artifacts,
  costs, and the standard final render are refreshed together.
- Run `mise run render -- <project-id>` when only the final PNG needs to be
  rebuilt from existing artifact previews.

## Standard Commands

```sh
mise run setup
mise run list
mise run projects
mise run build
mise run package -- <project-id>
mise run render -- <project-id>
mise run validate
```

Before handing work back, inspect the final render at
`projects/<project-id>/renders/<project-id>_final.png` when the task affects
geometry, fit, artifact packaging, or presentation.
