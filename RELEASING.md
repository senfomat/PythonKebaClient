# Releasing

This project publishes to PyPI as [`keba-modbus-client`](https://pypi.org/project/keba-modbus-client/) via GitHub Actions using [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) — no API tokens are stored as secrets.

## One-time setup

### 1. GitHub environments

In the repository settings (`Settings > Environments`), create two environments:

- `pypi`
- `testpypi`

No secrets are needed in either — trusted publishing uses GitHub's OIDC token instead. You can optionally add required reviewers to the `pypi` environment as a manual approval gate before a real release goes out.

### 2. Register the trusted publisher on PyPI

Since `keba-modbus-client` does not exist on PyPI yet, register a **pending** trusted publisher (this reserves the name for the first publish):

1. Go to <https://pypi.org/manage/account/publishing/>.
2. Under "Add a pending publisher", fill in:
   - PyPI project name: `keba-modbus-client`
   - Owner: `senfomat`
   - Repository name: `PythonKebaClient`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
3. Repeat on <https://test.pypi.org/manage/account/publishing/> with environment name `testpypi`, for test releases.

After the first successful publish, PyPI converts the pending publisher into a regular one automatically — nothing further to do.

## Making a release

1. Bump `version` in [`pyproject.toml`](pyproject.toml) (follow [SemVer](https://semver.org/)).
2. Run the full check suite locally:

   ```bash
   uv sync --all-extras --all-groups
   uv run pytest
   uvx ruff format --check .
   uvx ruff check .
   uvx ty check .
   ```

3. Commit the version bump and push to `main`.
4. Create a GitHub Release for the new version (`Releases > Draft a new release`, tag it e.g. `v0.2.0`).
5. Publishing the release triggers [`.github/workflows/publish.yml`](.github/workflows/publish.yml), which builds the sdist/wheel with `uv build` and uploads them to PyPI via `uv publish --trusted-publishing always`.

### Dry run on TestPyPI

Before a real release (or to test the workflow itself), trigger it manually without cutting a GitHub Release:

`Actions > Publish to PyPI > Run workflow`, target = `testpypi`.

This builds and publishes the current `main` branch to <https://test.pypi.org/project/keba-modbus-client/>. Install it from there to sanity-check:

```bash
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ keba-modbus-client
```

(The `--extra-index-url` is needed because TestPyPI does not mirror dependencies like `pymodbus` or `pydantic`.)

## Manual publish (fallback, no CI)

If you ever need to publish from your own machine instead of CI, use a PyPI API token instead of trusted publishing (which only works from the registered GitHub Actions workflow):

```bash
uv build
uv publish --token <your-pypi-api-token>
```

Generate a scoped token at <https://pypi.org/manage/account/token/>.
