# Troubleshooting

Use this guide when setup succeeds partially, a container does not become healthy, another device
cannot reach the application, or the browser refuses a capability such as the camera.

## Start With Status and Logs

The project commands automatically use a running Docker engine when available and otherwise use
the validated Podman path:

```powershell
npm run app:status
npm run app:logs
```

Force a provider when both engines are installed:

```powershell
$env:COMPOSE_PROVIDER = "Docker" # or "Podman"
npm run app:up
```

Docker uses its installed Compose plugin directly. The Podman path uses the pinned
`podman-compose` provider through `uv`, because provider availability varies between Podman Desktop
installations. Clear the override with `Remove-Item Env:COMPOSE_PROVIDER`.

## PostgreSQL Cannot Be Reached

### Without Containers

Confirm that PostgreSQL is running, the database exists, the login can create its schema, and
`DATABASE_URL` contains the correct host, port, credentials, and database name.

### With Compose

```powershell
npm run db:status
npm run db:logs
```

The wrapper writes the connection that Windows can actually reach to the ignored
`backend/.env.compose`. A process-level `DATABASE_URL` or `backend/.env` still takes precedence.

If a clean project database is required, `npm run db:reset` removes this project's PostgreSQL
volume. This is destructive and should be used only when its local data can be discarded.

## Python Cannot Import `backend`

For the standard `venv`/`pip` path, run commands from the repository root and set:

```powershell
$env:PYTHONPATH = (Resolve-Path backend/src)
```

The `uv --directory backend run ...` commands set up the installed project environment and do not
require this manual `PYTHONPATH` assignment.

## A Port Is Already in Use

Stop the process using port `5432`, `8000`, or `5173`. Advanced database and host-process overrides
are documented in
[the database workflow](docs/development/database.md).

## Frontend Calls Fail Although FastAPI Logs `200 OK`

A failure normally means the request reached FastAPI but the browser blocked JavaScript from
reading the response because the frontend origin does not match CORS exactly.

For example, when another device opens `http://192.168.15.130:5173`, use the shared root file:

```dotenv
# .env
APP_BIND_ADDRESS=0.0.0.0
PUBLIC_HOST=192.168.15.130
```

Restart both processes after changing the file. The project wrappers derive `FRONTEND_ORIGIN` and
`VITE_API_URL` before FastAPI or Vite starts.

## Open the Application From a Phone

The phone and development computer must be on the same non-isolated network. Find the computer's
Wi-Fi IPv4 address with `ipconfig`, then expose the host processes:

```powershell
# Terminal 1
npm run db:up
npm run dev:backend

# Terminal 2
npm run dev:frontend
```

The scripts read the root `.env`; no nested npm argument separators are required. Permit Node.js
and Python on private networks in Windows Firewall, and open `http://<wifi-ip>:5173` on the phone.

Podman on Windows runs inside a WSL virtual machine. In some installations, container ports are
healthy inside that machine but are not forwarded to the Windows Wi-Fi interface. Setting
`APP_BIND_ADDRESS=0.0.0.0` publishes on all interfaces owned by the Podman engine, while
`PUBLIC_HOST` provides the browser-visible host for direct-process URLs, CORS, and diagnostics. The
containerized frontend now uses its same-origin Nginx gateway. Neither variable can create a
missing Windows-to-WSL network forward. In that situation, keep only PostgreSQL in Podman with
`npm run db:up` and run FastAPI and Vite on the Windows host as shown above.

Plain LAN HTTP is useful for layout testing, but it does not provide a secure context for the phone
camera. For the complete containerized camera path without installing a local certificate, stop
the host Vite and FastAPI processes and run:

```powershell
npm run app:tunnel:up
```

Open the printed `https://...trycloudflare.com` URL rather than a LAN or localhost URL. The tunnel
connects outward, so no router port forwarding or inbound Windows Firewall rule is needed.

## The Quick Tunnel Does Not Print or Open a URL

Inspect its logs:

```powershell
npm run app:tunnel:logs
```

The first start must download the pinned official `cloudflared` image. The computer must resolve
public DNS and allow outbound Cloudflare Tunnel traffic. A restrictive corporate network, VPN,
proxy, or unavailable Cloudflare service can prevent creation of the URL.

If the configured local ports are already occupied by host-process Vite, FastAPI, or PostgreSQL,
stop those processes or select unused ports in the root `.env`, then retry. A Quick Tunnel URL is
random and changes after the container is recreated; use `npm run app:tunnel:url` to print the
currently active URL.

The URL exposes the complete evaluation application and its documented seeded accounts to the
internet. Do not leave it running, do not use real personal data, and stop it with:

```powershell
npm run app:tunnel:down
```

## The QR Camera Does Not Open

`getUserMedia` is a secure-context browser API. Chrome and Edge allow it on HTTPS and make a local
development exception for `localhost`; they do not expose it to a page opened from another device
over a plain HTTP LAN address such as `http://192.168.x.x:5173`.

Therefore:

- use `localhost` when testing a camera attached to the same computer;
- use the temporary HTTPS URL printed by `npm run app:tunnel:up` when testing from a phone without
  installing a certificate;
- grant camera permission for the exact site;
- close other software that may hold the camera; and
- use manual ticket entry when a secure context or camera is unavailable.

The Gate screen reports an insecure origin before attempting to start ZXing. This restriction is
enforced by the browser before the QR decoder can access a video stream; changing decoder libraries
would not bypass it.

## Signing or External Catalog Failures

- A Ticket or Gate endpoint returning `503` usually means `TICKET_HMAC_SECRET` is missing, unstable,
  or shorter than 32 bytes. Correct it and restart the backend or Compose stack.
- Ticketmaster search requires a valid `TICKETMASTER_API_KEY`, provider network access, and
  available quota. The seeded event and the rest of the local flow do not depend on Ticketmaster.
