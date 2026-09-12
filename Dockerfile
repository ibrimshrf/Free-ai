FROM node:22-bookworm-slim AS node-runtime

RUN npm install -g @openai/codex@0.153.4 \
    && node --version \
    && codex --version

FROM python:3.14-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    FCC_OPEN_BROWSER=false \
    FCC_REMOTE_ADMIN=1 \
    MESSAGING_PLATFORM=none

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git ripgrep libatomic1 libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=node-runtime /usr/local/bin/node /usr/local/bin/node
COPY --from=node-runtime /usr/local/lib/node_modules/@openai/codex /usr/local/lib/node_modules/@openai/codex
RUN ln -s /usr/local/lib/node_modules/@openai/codex/bin/codex.js /usr/local/bin/codex \
    && node --version \
    && codex --version

WORKDIR /app
COPY . /app
RUN python -m pip install --no-cache-dir . \
    && mkdir -p /workspace

WORKDIR /workspace

# Railway injects PORT at runtime; fcc-server reads it from the environment.
CMD ["fcc-server"]
