# UniFi Network API - Home Assistant Integration

A custom [Home Assistant](https://www.home-assistant.io/) integration that monitors your UniFi network devices using the **official UniFi Local Network API** (v10.1.68) with API key authentication.

## Features

- **Per-device sensors** — CPU, memory, uptime, load averages, firmware status, uplink rates, and more for every adopted UniFi device
- **Site-level sensors** — total, wired, wireless, and VPN client counts plus device count
- **Automatic device discovery** — new devices are picked up dynamically without restarting
- **Multi-site support** — choose which site to monitor during setup
- **Async-native** — built on `aiohttp` with parallel data fetching for fast updates
- **30-second polling** via Home Assistant's `DataUpdateCoordinator`

## Requirements

- UniFi Network Application **v10.1.68+** (self-hosted or UDM/UDR/UCG)
- An **API key** generated from the UniFi controller settings
- Home Assistant **2024.1+**

## Installation

### Manual

1. Copy the `custom_components/unifi_network_api/` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

### HACS (Manual Repository)

1. In HACS, go to **Integrations** and click the three-dot menu.
2. Select **Custom repositories**.
3. Add `https://github.com/xguitoux/HA-UnifiStatus` with category **Integration**.
4. Search for "UniFi Network API" and install it.
5. Restart Home Assistant.

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**.
2. Search for **UniFi Network API**.
3. Enter:
   - **Host** — hostname or IP address of your UniFi controller (e.g. `192.168.1.1`)
   - **API Key** — generated from your UniFi controller (see [Generating an API Key](#generating-an-api-key))
   - **Verify SSL** — enable if your controller uses a trusted SSL certificate (default: off)
4. If your controller has multiple sites, select which one to monitor.

### Generating an API Key

1. Log in to your UniFi controller web UI.
2. Navigate to **Settings > Control Plane > API**.
3. Click **Create API Key**.
4. Give it a name and copy the generated key.

For details, see the [official API documentation](https://developer.ui.com/network/v10.1.68/gettingstarted).

## Sensors

### Per-Device Sensors

Each adopted UniFi device (access points, switches, gateways, etc.) appears as its own device in Home Assistant with the following sensors:

| Sensor | Description | Unit |
|--------|-------------|------|
| State | Device state (ONLINE, OFFLINE, etc.) | — |
| CPU Utilization | Current CPU usage | % |
| Memory Utilization | Current memory usage | % |
| Uptime | Time since last boot | seconds |
| Load Average (1m) | 1-minute load average | — |
| Load Average (5m) | 5-minute load average | — |
| Load Average (15m) | 15-minute load average | — |
| Firmware Version | Currently installed firmware | — |
| Firmware Updatable | Whether a firmware update is available | — |
| Uplink TX Rate | Uplink transmit rate | B/s |
| Uplink RX Rate | Uplink receive rate | B/s |
| Last Heartbeat | Timestamp of last heartbeat | — |

### Site-Level Sensors

Grouped under a "UniFi Controller" device:

| Sensor | Description |
|--------|-------------|
| Total Clients | Total number of connected clients |
| Wired Clients | Number of wired clients |
| Wireless Clients | Number of wireless clients |
| VPN Clients | Number of VPN clients |
| Device Count | Total number of adopted devices |

## API Endpoints Used

This integration communicates with the following UniFi Local Network API endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/info` | Connection test during setup |
| `GET /v1/sites` | List available sites |
| `GET /v1/sites/{id}/devices` | List adopted devices (paginated) |
| `GET /v1/sites/{id}/devices/{id}` | Device details |
| `GET /v1/sites/{id}/devices/{id}/statistics/latest` | Device statistics |
| `GET /v1/sites/{id}/clients` | Connected clients (paginated) |
| `GET /v1/sites/{id}/wans` | WAN interfaces |

All endpoints are accessed via `https://<host>/proxy/network/integration/` with the `X-API-Key` header.

## Troubleshooting

**Cannot connect to controller**
- Verify the host is reachable from your Home Assistant instance
- Ensure the UniFi Network Application is running and accessible on port 443
- If using a hostname, verify DNS resolution works

**Invalid API key**
- Regenerate the API key from your UniFi controller settings
- Ensure the key has not been revoked

**No sites found**
- Verify the API key has permissions to access sites on the controller

**SSL errors**
- Try disabling "Verify SSL" during setup if your controller uses a self-signed certificate

## License

MIT
