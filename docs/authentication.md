# Authentication

SolidFUSE supports three authentication modes, selected via the `auth` key in `config.toml` (or inferred from whether credentials are present).

## CSS Client Credentials (recommended for CSS servers)

Community Solid Server uses OAuth2 client credentials with DPoP tokens. To use this:

1. Log into your CSS server's web UI.
2. Go to Account → Tokens (or similar) and create a new token. You will receive a **client ID** and **client secret**.
3. Set them in `config.toml`:

```toml
pod = "https://your-css-server.example.org/your-username/"
idp = "https://your-css-server.example.org"
username = "your-client-id"
password = "your-client-secret"
```

SolidFUSE will discover the token endpoint via `{idp}/.well-known/openid-configuration`, obtain a DPoP-bound access token, and attach `Authorization: DPoP` + `DPoP:` headers to every request.

## OIDC Browser Flow (fallback / alternative)

Leave `username` and `password` commented out. SolidFUSE starts a local Flask server on port 8080 and prints a login URL:

```
Please visit this URL to log-in: https://...
```

Open that URL in a browser, complete the login, and the mount will proceed automatically. Works with both CSS and NSS.

## NSS Password Auth (legacy, no longer maintained)

The old `Auth` class that posted credentials to NSS's `/login/password` endpoint has been replaced by `CssAuth`. If you still need NSS support, use the OIDC browser flow instead.
