# macOS Setup

## Prerequisites

1. **macFUSE** — install once:
   ```bash
   brew install --cask macfuse
   ```
   Then reboot and approve the kernel extension in System Settings → Privacy & Security.

2. **pkg-config** — needed to build pyfuse3:
   ```bash
   # If Homebrew permissions are broken, first fix them:
   sudo chown -R $(whoami) /opt/homebrew
   brew install pkg-config
   ```

## Installing pyfuse3 on macOS

pyfuse3 does not officially support macOS — it includes Linux-specific code (`syncfs` syscall, `struct stat` vs macFUSE's `fuse_darwin_attr`). The build requires two small patches to the generated C source.

A patched build process is included as `scripts/build-pyfuse3-macos.sh`. Run it once after cloning:

```bash
bash scripts/build-pyfuse3-macos.sh
```

This script:
1. Downloads pyfuse3 3.4.0
2. Applies the two macOS patches
3. Builds and installs the wheel into the project's venv

After that, `poetry install` handles the rest (skipping pyfuse3 since it's already installed).

## What the patches do

**Patch 1 — `syncfs` stub:**
```c
#ifdef __APPLE__
static inline int syncfs(int fd) { (void)fd; return 0; }
#endif
```
`syncfs(2)` is a Linux-only syscall; macFUSE doesn't expose it.

**Patch 2 — `setattr` function pointer cast:**
macFUSE uses `fuse_darwin_attr` instead of `struct stat` in several FUSE callbacks. The cast suppresses the clang error for the `setattr` assignment; the pointer layout is compatible in practice.

## Normal install (after pyfuse3 is built)

```bash
poetry install
```
