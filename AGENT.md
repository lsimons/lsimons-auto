# Agent Instructions

## Response Style
- Be concise in responses - avoid over-explaining changes
- Focus on the specific task requested rather than extensive commentary

## Development Workflow
- Follow spec-based development: document new features in `docs/spec/` before implementation (see [001-spec-based-development.md](docs/spec/001-spec-based-development.md))
- Document design decisions in code for future reference
- Always run unit tests after making changes using `uv run pytest`
- Reference spec numbers in commit messages during feature implementation

## Diagnostic Handling
For diagnostic warnings, use specific Pyright ignore comments with error codes:
- `# pyright: ignore[reportAny]` for "Type is Any" warnings
- `# pyright: ignore[reportImplicitOverride]` for unittest method override warnings
- Use `_ = function_call()` assignment for unused return value warnings
