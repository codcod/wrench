# Semantic Release Setup

This project uses [Python Semantic Release](https://python-semantic-release.readthedocs.io/) for automated version management and releasing.

## How it works

Semantic Release analyzes commit messages to automatically:
- Determine the next version number (following [Semantic Versioning](https://semver.org/))
- Generate and update the CHANGELOG.md
- Create a git tag
- Create a GitHub release
- Publish to PyPI (when configured)

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Supported types:
- `feat`: A new feature (minor version bump)
- `fix`: A bug fix (patch version bump)
- `perf`: A performance improvement (patch version bump)
- `docs`: Documentation changes (no version bump)
- `style`: Code style changes (no version bump)
- `refactor`: Code refactoring (no version bump)
- `test`: Adding or updating tests (no version bump)
- `chore`: Maintenance tasks (no version bump)
- `ci`: CI/CD changes (no version bump)
- `build`: Build system changes (no version bump)

### Examples:

```bash
# Patch release (0.1.0 → 0.1.1)
git commit -m "fix: resolve connection timeout issue"

# Minor release (0.1.0 → 0.2.0)
git commit -m "feat: add new API endpoint for user management"

# Major release (0.1.0 → 1.0.0) - with breaking change
git commit -m "feat: redesign authentication system

BREAKING CHANGE: The authentication API has changed completely"
```

## Manual Release Process

To manually trigger a release:

```bash
# Install dependencies
uv sync --dev

# Print next version (without making changes)
uv run semantic-release version --print

# Create release locally (no push)
uv run semantic-release version --no-push

# Create and push release
uv run semantic-release version
```

## Automated Release

Releases are automatically triggered when commits are pushed to the `main` branch via GitHub Actions. The workflow:

1. Analyzes commit messages since the last release
2. Determines the next version number
3. Updates version in `pyproject.toml` and `src/wrench/__init__.py`
4. Updates `CHANGELOG.md`
5. Creates a git tag and GitHub release
6. Publishes to PyPI (if configured)

## Configuration

The semantic release configuration is in `pyproject.toml` under `[tool.semantic_release]`.

Key settings:
- Version files: `pyproject.toml` and `src/wrench/__init__.py`
- Changelog template: `templates/CHANGELOG.md.j2`
- Commit parser: Conventional Commits
- Branch: `main`
- Remote: `origin` (GitHub)

## Setup Requirements

1. **GitHub Repository**: Must have appropriate permissions for the workflow
2. **PyPI Setup** (optional): Configure PyPI publishing in GitHub secrets
3. **Conventional Commits**: All contributors should follow the commit message format

## First Release

For the initial release, make sure:
1. Version is set to `0.1.0` in relevant files
2. Basic CHANGELOG.md exists
3. All semantic release configuration is in place
4. GitHub workflow has proper permissions

Then commit with:
```bash
git add .
git commit -m "feat: add semantic release configuration"
git push origin main
```

This will trigger the first automated release! 🚀
