# ISP RADIUS Configuration Guide

How we configured FreeRADIUS for ISP use — PPPoE auth, DB-backed NAS list, per-user bandwidth/IP profiles.
All paths relative to the RADIUS config root (`/etc/raddb/` inside the container).

---

## 1. Container Setup (Docker Compose)

```yaml
services:
  freeradius:
    image: freeradius/freeradius-server:latest
    restart: unless-stopped
    network_mode: host            # ISP needs direct port access
    volumes:
      - ./freeradius/raddb:/etc/raddb
```

`network_mode: host` so NASes reach ports directly. Same Postgres container runs alongside — FreeRADIUS connects via `localhost`.

---

## 2. Running Multiple Instances on One Host

Can't bind two instances to the same port in host mode. Change the **listen ports** in `sites-available/default`:

```
# Instance 1 (default):   auth=1812,  acct=1813,  inner-tunnel=18120
# Instance 2 (custom):    auth=11812, acct=11813, inner-tunnel=11820
```

Search for every `listen { }` block — there are four (auth IPv4, acct IPv4, auth IPv6, acct IPv6) — and change `port = 0` → `port = 11812` etc.

Also in `sites-available/inner-tunnel`: change `port = 18120` → `port = 11820`.

---

## 3. PostgreSQL Integration

### Enable the SQL module
Symlink or ensure present: `mods-enabled/sql` → `mods-available/sql`

### Configure connection (mods-enabled/sql)
```
dialect = "postgresql"
driver = "rlm_sql_${dialect}"

server = "localhost"
port = 5432
login = "radiususer"
password = "<db-password>"

radius_db = "radius"
```

### Bootstrap the schema
Run the bundled schema file against the database:
```
mods-config/sql/main/postgresql/schema.sql
```
This creates all RADIUS tables: `radcheck`, `radreply`, `radgroupcheck`, `radgroupreply`, `radusergroup`, `radacct`, `radpostauth`, `nas`, `nasreload`.

---

## 4. Database-Backed NAS List (Strict Enforcement)

### Why
Default `clients.conf` uses a catch-all wildcard (`0.0.0.0/0`). Any device with the shared secret can authenticate. For ISP, each NAS must be explicitly whitelisted.

### Step 1 — Remove wildcard from clients.conf
Keep only `localhost` for local testing:
```
client localhost {
    ipaddr = 127.0.0.1
    secret = <local-secret>
}
# REMOVE: client docker-net { ipaddr = 0.0.0.0/0 ... }
```

### Step 2 — Enable SQL client loading (mods-enabled/sql)
Uncomment:
```
read_clients = yes
```
This tells FreeRADIUS to load NAS definitions from the `nas` table at startup.

### Step 3 — The query (auto-configured)
The SQL module uses this query (from `mods-config/sql/main/postgresql/queries.conf`):
```sql
SELECT id, nasname, shortname, type, secret, server FROM nas
```

### Step 4 — Adding a NAS (via backend API or direct SQL)
```sql
INSERT INTO nas (nasname, shortname, type, secret, description)
VALUES ('10.10.10.1', 'Downtown-NAS', 'mikrotik', '<nas-secret>', 'Downtown PPPoE');
```

### Step 5 — Reloading NAS list
Bump the `nasreload` table, then restart FreeRADIUS:
```sql
UPDATE nasreload SET reloadtime = NOW();
```
```
docker compose restart freeradius
```

### Result
Requests from unknown IPs are **silently dropped** — no response at all. Only IPs in the `nas` table + matching secret get through.

---

## 5. Per-User Attributes (Bandwidth, Static IP, PPPoE Framing)

All stored in `radreply`. Sent in the `Access-Accept` response alongside auth success.

### Bandwidth (MikroTik)
```sql
INSERT INTO radreply (username, attribute, op, value)
VALUES ('username', 'Mikrotik-Rate-Limit', ':=', '10M/20M');
```
Format: `rx-rate/tx-rate` (MikroTik convention). Other NAS vendors use different attributes.

### Static IP
```sql
INSERT INTO radreply (username, attribute, op, value)
VALUES ('username', 'Framed-IP-Address', ':=', '10.5.50.100');
```
No netmask needed — PPPoE is `/32` by nature.

### PPPoE framing
```sql
INSERT INTO radreply (username, attribute, op, value) VALUES
('username', 'Framed-Protocol', ':=', 'PPP'),
('username', 'Service-Type', ':=', 'Framed-User');
```

### Group-based profiles
For plan-wide settings, use `radgroupreply`:
```sql
INSERT INTO radgroupreply (groupname, attribute, op, value)
VALUES ('10mbps-plan', 'Mikrotik-Rate-Limit', ':=', '10M/20M');

INSERT INTO radusergroup (username, groupname, priority)
VALUES ('username', '10mbps-plan', 1);
```

---

## 6. Testing Auth Remotely

```bash
radtest <username> <password> <server-ip>:11812 0 <nas-secret>
```

Expected output includes all configured attributes:
```
Received Access-Accept
  Mikrotik-Rate-Limit = "10M/20M"
  Framed-IP-Address = 10.5.50.100
  Framed-Protocol = PPP
  Service-Type = Framed-User
```

Unknown NAS IP → no response (packet dropped silently).

---

## 7. FastAPI Backend Integration

Backend manages all tables (`nas`, `radcheck`, `radreply`, `radgroupreply`, `radusergroup`) via REST API. No direct FreeRADIUS communication — everything through the shared PostgreSQL database.

```
Backend (FastAPI) ──writes──→ PostgreSQL ←──reads── FreeRADIUS
```

For multiple RADIUS instances, clone the backend, change `.env` → `DATABASE_URL` to point at a different database, run on a different port.

---

## Summary of Config Files Touched

| File | Change |
|---|---|
| `docker-compose.yml` | `network_mode: host`, volume mount |
| `clients.conf` | Remove wildcard, keep localhost |
| `mods-enabled/sql` | Set dialect, connection params, `read_clients = yes` |
| `sites-available/default` | Change `port = 0` → explicit ports in all 4 listen blocks |
| `sites-available/inner-tunnel` | Change `port = 18120` → custom port |

Everything else — NAS list, users, attributes, groups — is pure database data, no config changes needed.

---

## MikroTik Bandwidth Profiles — Important

When setting `Mikrotik-Rate-Limit`, only set the **rx-rate/tx-rate** (down/up):

```
10M/20M       ✅ Works — 10 Mbps down, 20 Mbps up
```

Do **not** include burst parameters unless explicitly needed:

```
10M/20M 1M/1M 8 4    ❌ MikroTik rejects this
```

The correct full format is:
```
rx-rate/tx-rate rx-burst-rate/tx-burst-rate rx-burst-threshold/tx-burst-threshold rx-burst-time/tx-burst-time priority rx-min-rate/tx-min-rate
```

The API's `/radius/bandwidth/{username}` endpoint accepts only the base rate to keep it simple.
If you need burst, set it manually via the raw `/radius/replies` endpoint.
