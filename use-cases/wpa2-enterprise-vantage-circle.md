# WPA2-Enterprise RADIUS Configuration Guide

How we configured FreeRADIUS for Vantage Circle's office WiFi — WPA2-Enterprise with EAP-TLS/PEAP/TTLS, Let's Encrypt certificates, and web-based user management.

---

## 1. Container Setup (Docker Compose)

```yaml
services:
  postgres:
    image: postgres:latest
    container_name: postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: <db-password>
    volumes:
      - ./postgres/data:/var/lib/postgresql

  freeradius:
    image: freeradius/freeradius-server:latest
    container_name: freeradius
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./freeradius/raddb:/etc/raddb
```

---

## 2. TLS Certificates (Let's Encrypt)

WPA2-Enterprise requires a valid TLS certificate so client devices trust the RADIUS server during the EAP handshake.

### Obtain via Certbot
```bash
certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials ~/.secrets/cloudflare.ini \
  -d vc.xynocast.com
```

### Copy into RADIUS config
Certs are at `/etc/letsencrypt/live/vc.xynocast.com/`. Copy them to the FreeRADIUS certs directory (mounted volume):
```bash
cp /etc/letsencrypt/live/vc.xynocast.com/fullchain.pem ./freeradius/raddb/certs/
cp /etc/letsencrypt/live/vc.xynocast.com/privkey.pem  ./freeradius/raddb/certs/
```

### Auto-renewal
Launchd job runs `certbot renew` weekly (Mondays 4 AM). Deploy hook copies fresh certs and restarts the container:
```bash
# /etc/letsencrypt/renewal-hooks/deploy/freeradius.sh
cp .../fullchain.pem ./freeradius/raddb/certs/
cp .../privkey.pem  ./freeradius/raddb/certs/
docker restart freeradius
```

---

## 3. EAP Configuration (mods-available/eap)

### Choose EAP methods
WPA2-Enterprise supports multiple inner methods. Common setup:

- **PEAP** (widest device support — Windows, Android, iOS)
- **TTLS** (good for Linux, some BYOD policies)
- **TLS** (certificate-based, no password — strongest, harder to deploy)

### TLS common block
```bash
tls-config tls-common {
    private_key_file = ${certdir}/privkey.pem
    certificate_file = ${certdir}/fullchain.pem
    tls_min_version = "1.2"
    tls_max_version = "1.2"
}
```
`ca_file` is commented out — client verifies the server cert, but the server doesn't require client certs (PEAP/TTLS use password inside the tunnel).

### PEAP section
```bash
peap {
    tls = tls-common
    default_eap_type = mschapv2    # MSCHAPv2 inside the TLS tunnel
}
```

### TTLS section
```bash
ttls {
    tls = tls-common
    default_eap_type = md5        # or mschapv2
}
```

### No changes needed elsewhere
The `inner-tunnel` virtual server (port 18120 on localhost) handles decrypted inner authentication automatically. EAP module proxies the inner identity to it internally.

---

## 4. PostgreSQL Integration

Same as ISP setup — see `isp-radius-config.md` sections 3 for connection config and schema bootstrap.

Key difference: WPA2-Enterprise with PEAP/MSCHAPv2 requires `NT-Password` in `radcheck`, not `Cleartext-Password`:

```sql
INSERT INTO radcheck (username, attribute, op, value)
VALUES ('office-user', 'NT-Password', ':=', '<ntlm-hash>');
```

The FastAPI backend handles hashing — store the plaintext password, backend converts to NTLM hash before inserting.

---

## 5. NAS (Access Point) Configuration

### Open NAS policy (office WiFi)
For an office with multiple APs on the same subnet, the wildcard approach is practical:

```
# clients.conf
client docker-net {
    ipaddr = 0.0.0.0/0
    secret = <shared-secret>
}
```

All UniFi/Cisco/MikroTik APs share the same secret. The RADIUS server trusts any AP on the office network.

### Why not strict per-AP?
Office APs change, get replaced, DHCP reassigns IPs. Managing individual NAS entries per AP adds friction without security benefit — all APs are on the same trusted LAN segment.

### Per-AP enforcement (optional)
For higher security, use the DB-backed NAS list (see ISP guide section 4). Useful if APs span untrusted network segments.

---

## 6. User Management

### Database tables used
- `radcheck` — user credentials (`NT-Password` for PEAP/MSCHAPv2)
- `radreply` — per-user attributes (rare for office WiFi, but possible)
- `radusergroup` + `radgroupreply` — group-based policies (VLAN assignment, bandwidth)
- `radacct` — session accounting (who connected, when, from which AP)

### Web backend
FastAPI backend on port 8001 provides:
- `/auth/login` — admin authentication
- `/auth/seed` — first-time admin setup
- CRUD for users, groups, NAS entries
- Password hashing (bcrypt for admins, NTLM for RADIUS users)

### Adding a user (via API)
```json
POST /users
{
  "username": "employee.name",
  "password": "secure-wifi-pass",
  "full_name": "Employee Name",
  "group": "staff"
}
```

Backend creates both `radcheck` (NT-Password) and `user_meta` (name, email, phone) entries.

---

## 7. WPA2-Enterprise Flow

```
Client device
    │
    │  "Connect to CorpWiFi"
    ▼
Access Point (UniFi)
    │
    │  EAPoL-Start
    │  ← EAP-Identity request
    │  → EAP-Identity response ("anonymous@vc.xynocast.com")
    ▼
FreeRADIUS (:1812)
    │
    │  TLS tunnel established (server cert validated by client)
    │  Inner method: MSCHAPv2 (PEAP) or PAP/MD5 (TTLS)
    │  RADIUS queries PostgreSQL for NT-Password
    ▼
Access-Accept
    │
    │  Optional: VLAN assignment, bandwidth limits
    ▼
Client connected ✅
```

---

## 8. Testing

### From server
```bash
# radtest doesn't support EAP. Use eapol_test instead:
eapol_test -c peap-mschapv2.conf -s <radius-secret> -a 127.0.0.1 -p 1812
```

### From a real device
Connect a laptop/phone to the WPA2-Enterprise SSID and check RADIUS logs:
```bash
docker logs freeradius
```
Look for `Login OK` or `Login incorrect` in `/var/log/freeradius/radius.log`.

### From a remote machine with radtest
Only works for non-EAP methods. For EAP, use `eapol_test` or a real client device.

---

## 9. Certificate Renewal Notes

Keep an eye on expiry:
```bash
openssl x509 -in certs/fullchain.pem -noout -enddate
```

Certbot renews automatically, but the deploy hook must be verified after each macOS update (launchd plists can get disabled).

---

## Summary of Config Files Touched

| File | Change |
|---|---|
| `docker-compose.yml` | PostgreSQL + FreeRADIUS with `network_mode: host` |
| `mods-available/eap` | Set TLS certs, enable PEAP + TTLS, set TLS version |
| `mods-enabled/sql` | PostgreSQL connection params |
| `clients.conf` | Open wildcard for office AP subnet |
| `certs/` | Let's Encrypt fullchain + privkey copied in |
| `/etc/letsencrypt/` | Certbot deploy hook for auto-renewal |

Users, groups, and passwords are managed entirely via the FastAPI backend — no config file edits needed for day-to-day operations.



---

## Mandatory DB Extension — `nasidentifier`

Every project using this codebase **must** add the `nasidentifier` column to `radacct`:

```sql
ALTER TABLE radacct ADD COLUMN nasidentifier TEXT;
```

Even if your NAS is not MikroTik, an extra nullable text column hurts nothing.
The API handles both schemas gracefully — but having the column unlocks NAS identity
tracking for every session without relying on IP-based lookups.
