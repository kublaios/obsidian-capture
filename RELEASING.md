# Release Process

This document describes the automated release process for obsidian-capture.

## Automated Releases

The project uses GitHub Actions to automatically build and release:

1. **Python packages** (wheel and source distribution)
2. **Binary executables** for multiple platforms

### Triggering a Release

#### Method 1: Git Tags (Recommended)
Create and push a version tag to trigger an automated release:

```bash
# Create a new version tag
git tag v0.3.0
git push origin v0.3.0
```

#### Method 2: Manual Workflow Dispatch
Trigger a release manually from the GitHub Actions UI:

1. Go to **Actions** tab in the repository
2. Select **Release** workflow
3. Click **Run workflow**
4. Enter the tag name (e.g., `v0.3.0`)

### Release Artifacts

Each release includes:

#### Python Packages
- `obsidian_capture-X.X.X.tar.gz` - Source distribution
- `obsidian_capture-X.X.X-py3-none-any.whl` - Python wheel

Install with: `pip install obsidian-capture`

#### Binary Executables
- `obsidian-capture-linux-x86_64` - Linux 64-bit
- `obsidian-capture-windows-x86_64.exe` - Windows 64-bit  
- `obsidian-capture-macos-x86_64` - macOS Intel 64-bit
- `obsidian-capture-macos-arm64` - macOS Apple Silicon

Binary executables are standalone and don't require Python installation.

### Version Management

Update the version in `pyproject.toml` before creating a release:

```toml
[project]
name = "obsidian-capture"
version = "0.3.0"  # Update this
```

### Platform Support

| Platform | Architecture | Status |
|----------|-------------|---------|
| Linux | x86_64 | ✅ Supported |
| Windows | x86_64 | ✅ Supported |
| macOS | x86_64 (Intel) | ✅ Supported |
| macOS | arm64 (Apple Silicon) | ✅ Supported |

### Development Workflow

1. Make changes and commit to main branch
2. Update version in `pyproject.toml`
3. Create and push a git tag
4. GitHub Actions automatically builds and releases
5. Release appears in GitHub Releases with all artifacts

### Testing Releases

The release workflow can be tested by:

1. Creating a pre-release tag (e.g., `v0.3.0-rc1`)
2. Using workflow dispatch to build specific tags
3. Checking the build logs in GitHub Actions

### Manual Local Builds

For development and testing:

```bash
# Build Python packages
pip install build
python -m build

# Build binaries (requires PyInstaller)
pip install pyinstaller
pyinstaller pyinstaller.spec
```