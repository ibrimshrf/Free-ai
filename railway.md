# Railway deployment

Railway can build this repository directly from the root `Dockerfile`.

After connecting `ibrimshrf/Free-ai` to Railway:

1. Generate a public domain for the service.
2. Add Railway Variables `FCC_WEB_USER` and `FCC_WEB_PASSWORD`. These protect `/admin`, `/admin/code`, and the Admin APIs with HTTP Basic Auth.
3. Mount a Railway Volume at `/workspace` if you want Codex workspaces and sessions to persist across redeploys.
4. Keep provider credentials in Railway Variables, not in the repository.

The Railway image runs with `FCC_REMOTE_ADMIN=basic`, binds to `0.0.0.0`, and lets Railway supply `PORT` at runtime. Cloudflare keeps its separate trusted-proxy mode in `Dockerfile.cloudflare`.
