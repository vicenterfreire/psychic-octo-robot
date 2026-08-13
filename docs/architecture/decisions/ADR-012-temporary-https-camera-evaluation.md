# ADR-012: Temporary HTTPS Camera Evaluation

## Status

Accepted

## Context

The challenge requires Gate staff to read a QR code through the browser camera, with manual entry
as an alternative. Modern mobile browsers expose `getUserMedia` only in a secure context. Local
`http://localhost` is treated as trustworthy on the same device, but a phone opening a private LAN
address over HTTP cannot use that exception.

Generating a private certificate inside the frontend container provides encryption but does not
make the certificate trusted by the phone. Installing a project-specific certificate authority on
every evaluator device was rejected as too invasive for a time-constrained challenge. A production
deployment remains optional and requires broader hosting, secret, database, and operations
decisions.

ADR-010 previously kept Nginx from proxying the API because separate local ports and explicit CORS
were already implemented. HTTPS camera evaluation changes that constraint: one trusted public
origin must serve both the SPA and its credentialed API without mixed content.

## Decision

- Keep direct Vite/FastAPI development and normal `app:up` execution available over local HTTP.
- Add an opt-in Compose `tunnel` profile using the pinned official `cloudflared` image and a
  Cloudflare Quick Tunnel.
- Route the tunnel only to the internal Nginx frontend service; do not publish a separate public
  FastAPI origin.
- Build the containerized frontend with relative `/api` requests and make Nginx proxy `/api`,
  `/docs`, and `/openapi.json` to FastAPI inside the Compose network.
- Enable the session cookie's `Secure` attribute only through the `app:tunnel:up` workflow.
- Print the generated HTTPS URL from the project hook and provide explicit URL, log, and shutdown
  commands.
- Treat the URL as temporary public test infrastructure, never as production deployment or the
  challenge's optional hosted-application bonus.

## Alternatives Considered

### Generate a Private Certificate in the Frontend Container

Nginx could terminate TLS locally, but each phone would still need to trust the signing authority.
Generating a new self-signed certificate on every start would preserve browser warnings and may
leave camera access unavailable.

### Require `mkcert` and Install Its Authority on Every Device

This works offline and supports private addresses, but adds host tooling and a security-sensitive
certificate installation to the evaluator's phone and computer.

### Keep Separate Public Frontend and Backend Tunnels

Two random origins would reintroduce credentialed CORS, coordinate two changing URLs, and create
more cookie and mixed-content failure modes than one same-origin proxy.

### Deploy the Application to a Permanent Provider

A real deployment gives trusted HTTPS and evaluator convenience, but requires provider, database,
secret management, migration, monitoring, and lifecycle decisions beyond this diagnostic fix.

### Rely Only on Manual Ticket Entry

Manual entry is a required fallback, not a substitute for demonstrating the required camera path.

## Consequences

- A phone can test the camera through trusted HTTPS without installing a certificate, discovering
  a LAN IP, or opening an inbound firewall port.
- The container topology now uses Nginx as the same-origin browser gateway, amending that part of
  ADR-010; direct host development continues to exercise explicit credentialed CORS.
- Quick Tunnel creation requires outbound internet and Cloudflare availability, has no SLA, and
  produces a different random URL when recreated.
- Anyone who receives or discovers the active URL can reach the application and its documented
  seeded accounts. It must use only disposable evaluation data and be stopped immediately after
  testing.
- The official tunnel image is an additional optional container dependency, fixed to a reviewed
  version for reproducibility.
- Secure opaque sessions work through the HTTPS URL, while normal local HTTP intentionally retains
  a non-`Secure` development cookie.
- Production TLS, access control, rate limiting, secret management, and deployment operations
  remain unsolved and are not implied by this local evaluation aid.

## Revisit When

- The application receives a permanent hosted URL and managed certificate.
- Cloudflare Quick Tunnels become unavailable or their terms no longer fit development testing.
- Evaluators must run fully offline or public temporary exposure is prohibited.
