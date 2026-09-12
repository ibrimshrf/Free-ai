FROM node:22-bookworm-slim AS node-runtime

FROM python:3.14-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    FCC_OPEN_BROWSER=false \
    FCC_REMOTE_ADMIN=1 \
    MESSAGING_PLATFORM=none

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git ripgrep \
    && rm -rf /var/lib/apt/lists/*

COPY --from=node-runtime /usr/local/bin/node /usr/local/bin/node
COPY --from=node-runtime /usr/local/bin/npm /usr/local/bin/npm
COPY --from=node-runtime /usr/local/bin/npx /usr/local/bin/npx
COPY --from=node-runtime /usr/local/lib/node_modules /usr/local/lib/node_modules

RUN npm install -g @openai/codex@0.153.4 \
    && codex --version

WORKDIR /app
COPY . /app
RUN python -m pip install --no-cache-dir . \
    && mkdir -p /workspace

WORKDIR /workspace

# Railway injects PORT at runtime; fcc-server reads it from the environment.
CMD ["fcc-server"]
