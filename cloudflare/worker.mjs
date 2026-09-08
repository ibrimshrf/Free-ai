import { Container, getContainer } from "@cloudflare/containers";

const TRUSTED_PROXY_HEADER = "x-fcc-trusted-proxy";
const TRUSTED_PROXY_VALUE = "cloudflare";

export class FreeAIContainer extends Container {
  defaultPort = 8082;
  sleepAfter = "10m";
  envVars = {
    HOST: "0.0.0.0",
    PORT: "8082",
    FCC_OPEN_BROWSER: "false",
    FCC_REMOTE_ADMIN: "1",
    MESSAGING_PLATFORM: "none",
  };
}

function constantTimeEqual(left, right) {
  if (typeof left !== "string" || typeof right !== "string") return false;
  const length = Math.max(left.length, right.length);
  let diff = left.length ^ right.length;
  for (let index = 0; index < length; index += 1) {
    diff |= (left.charCodeAt(index) || 0) ^ (right.charCodeAt(index) || 0);
  }
  return diff === 0;
}

function decodeBasicCredentials(header) {
  if (!header || !header.startsWith("Basic ")) return null;
  try {
    const encoded = header.slice(6).trim();
    const bytes = Uint8Array.from(atob(encoded), (character) => character.charCodeAt(0));
    const decoded = new TextDecoder().decode(bytes);
    const separator = decoded.indexOf(":");
    if (separator < 0) return null;
    return [decoded.slice(0, separator), decoded.slice(separator + 1)];
  } catch {
    return null;
  }
}

function isAuthorized(request, env) {
  if (!env.FCC_WEB_USER || !env.FCC_WEB_PASSWORD) return false;
  const credentials = decodeBasicCredentials(request.headers.get("authorization"));
  if (!credentials) return false;
  return (
    constantTimeEqual(credentials[0], env.FCC_WEB_USER) &&
    constantTimeEqual(credentials[1], env.FCC_WEB_PASSWORD)
  );
}

function unauthorized() {
  return new Response("Authentication required", {
    status: 401,
    headers: {
      "cache-control": "no-store",
      "www-authenticate": 'Basic realm="Free AI", charset="UTF-8"',
    },
  });
}

export default {
  async fetch(request, env) {
    if (!env.FCC_WEB_USER || !env.FCC_WEB_PASSWORD) {
      return new Response("FCC_WEB_USER and FCC_WEB_PASSWORD secrets are required.", {
        status: 503,
        headers: { "cache-control": "no-store" },
      });
    }

    if (!isAuthorized(request, env)) return unauthorized();

    const url = new URL(request.url);
    if (url.pathname === "/") {
      url.pathname = "/admin/code";
      return Response.redirect(url.toString(), 302);
    }

    const headers = new Headers(request.headers);
    headers.delete(TRUSTED_PROXY_HEADER);
    headers.delete("authorization");
    headers.set(TRUSTED_PROXY_HEADER, TRUSTED_PROXY_VALUE);

    const forwarded = new Request(request, { headers });
    return getContainer(env.FCC_CONTAINER, "primary").fetch(forwarded);
  },
};
