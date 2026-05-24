# Architecture

## Components

```
solid-fuse.py          CLI entry point — argument parsing, logging, FUSE init, trio event loop
config.py              TOML config loader (pod URL, IDP, optional credentials)
fsimpl.py              All filesystem logic:
  UriWrapper             URI manipulation (parent/child navigation, container detection)
  ResourceLinkHelper     Bidirectional mapping: inode ↔ file-handle ↔ Solid URI
  ResourceInfoCache      Simple dict-backed cache keyed by URI
  ResourceInfoLinkWrapper  Orchestrates auth, API calls, and caching; used by SolidFs
  SolidFs                pyfuse3.Operations subclass — implements FUSE callbacks
```

## Data Flow

- `ResourceInfoLinkWrapper` owns the `SolidAPI` instance from `solid-file-python`.
- `ResourceLinkHelper` maps each URI to an inode (and a file handle, which equals the inode in this implementation).
- Two info caches: `_container_info_cache` (whole folder listings keyed by folder URL) and `_resource_info_cache` (individual item metadata keyed by item URL). File content lives in `_resource_contant_cache` (misspelled in source).
- On `readdir`, the folder listing is fetched on demand. `getattr` is called for each entry during listing, which calls `size_of_resource` → `get_resource`, causing every file's content to be downloaded eagerly (needed for `st_size`). Only the root container is pre-fetched on init; subdirectories are lazy.

## Dependencies

| Package | Purpose |
|---------|---------|
| `pyfuse3` | Python FUSE bindings (requires libfuse3 / macFUSE on macOS) |
| `trio` | Async I/O runtime used by pyfuse3 |
| `solid-file` | Solid API client — custom fork at `renyuneyun/solid-file-python`, branch `pin/for-solid-fuse` (dev: local path `../solid-file-python`) |
| `solid-oidc-client` | OIDC login flow + DPoP token generation for Solid servers |
| `flask` | Required by `solid-oidc-client` for the OIDC redirect callback server |
| `tomlkit` | TOML config parsing |
