# SolidFUSE — Developer Notes

## What This Project Does

SolidFUSE mounts a [Solid Pod](https://solidproject.org/) as a local filesystem using FUSE. It lets you read, write, and create files in a Solid Pod using ordinary command-line tools (`ls`, `cat`, `cp`, `echo`, etc.).

## Architecture

See [docs/architecture.md](docs/architecture.md) for a full description of the components and data flow.

## Running

```bash
cp config_example.toml config.toml
$EDITOR config.toml          # fill in pod URL, IDP, and CSS credentials
mkdir -p /tmp/solid
poetry run src/solid-fuse.py config.toml /tmp/solid
```

Add `--debug` for verbose logging or `--debug-fuse` for low-level FUSE tracing.

Unmount: `umount /tmp/solid`

## Authentication

See [docs/authentication.md](docs/authentication.md).

## macOS Setup

See [docs/macos-setup.md](docs/macos-setup.md) — installing pyfuse3 on macOS requires patches and workarounds.

## Known Limitations

See [docs/limitations.md](docs/limitations.md).
