# Known Limitations

- **No delete support** — `unlink`/`rmdir` are not implemented; attempts return `ENOSYS`.
- **No cache invalidation** — changes made outside SolidFUSE won't be reflected until remount.
- **Eager file download on `readdir`** — opening a directory downloads all file contents (needed for `st_size`). Large directories will be slow.
- **Hardcoded timestamps** — all files report the same mtime/atime. Time-based tools like `make` will not work correctly.
- **No POSIX permission mapping** — always reports `0o755` for dirs and `0o644` for files regardless of Solid ACL.
- **OIDC token not refreshed** — long-running mounts will fail after the token expires (upstream `solid-oidc-client` limitation).
- **CSS client credentials token not refreshed** — same issue; remount to re-authenticate.
- **macOS only tested with macFUSE** — requires macFUSE or `libfuse3` on Linux.
