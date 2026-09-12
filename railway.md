# Railway deployment

Railway can build this repository directly from the root `Dockerfile`.

After connecting `ibrimshrf/Free-ai` to Railway:

1. Generate a public domain for the service.
2. Mount a Railway Volume at `/workspace` if you want Codex workspaces and sessions to persist across redeploys.
3. Keep provider credentials in Railway Variables, not in the repository.

The application binds to `0.0.0.0`, and Railway supplies `PORT` at runtime.
