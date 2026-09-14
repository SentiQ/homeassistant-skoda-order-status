# Škoda Order Status for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration to track the status of a **pending Škoda vehicle order** via the unofficial MyŠkoda API.

This fills the gap left by the official Škoda integration: order tracking in the MyŠkoda app ("Track & Explore") works **before** a VIN exists.

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=SentiQ&repository=homeassistant-skoda-order-status&category=integration)

[![Open your Home Assistant instance and start setting up this integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=skoda_order_status)

## Features

- Native Home Assistant sensor (no REST API workaround)
- Automatic discovery of open orders in your MyŠkoda account
- German status labels and checkpoint dates
- Configurable polling interval (default: 1 hour)
- Refresh token stored securely in the config entry
- Lovelace card (`custom:skoda-order-card`) with configurator image and production timeline

## Installation

### HACS (recommended)

This integration is a **custom HACS repository** (not in the default HACS store).

1. Open **HACS → Integrations**
2. Click the menu (⋮) → **Custom repositories**
3. Add `https://github.com/SentiQ/homeassistant-skoda-order-status`
4. Click **Download** (pick a [release](https://github.com/SentiQ/homeassistant-skoda-order-status/releases) version if available)
5. **Restart Home Assistant**

### Manual

Copy `custom_components/skoda_order_status` into your Home Assistant `custom_components` directory and restart.

## Configuration

After installation and restart, use the **Add integration** button above or:

1. Go to **Settings → Devices & services → Add integration**
2. Search for **Škoda Order Status**
3. Sign in with your MyŠkoda email and password
4. Select your order if multiple are available

### Options

- **Update interval**: polling interval in seconds (900–86400, default 3600)

## Entities

| Entity                          | Description          |
| ------------------------------- | -------------------- |
| `sensor.<device>_bestellstatus` | Current order status |

Attributes include model, trim, colours, commission ID, checkpoint dates, and pending steps.

## Lovelace card

After installing the integration and restarting Home Assistant, the card **Škoda Order Status** is available in the dashboard card picker. No extra HACS frontend plugin is required.

```yaml
type: custom:skoda-order-card
entity: sensor.skoda_elroq_bestellstatus
layout: combined   # combined (default) | hero | timeline
```

`combined` shows the vehicle render, specs, and checkpoint timeline. `hero` hides the timeline. `timeline` hides the photo.

## Automations

Example notification when the status changes:

```yaml
automation:
  - alias: Škoda Bestellstatus geändert
    triggers:
      - trigger: state
        entity_id: sensor.skoda_elroq_bestellstatus
    conditions:
      - condition: template
        value_template: "{{ trigger.from_state.state not in ['unknown', 'unavailable'] }}"
    actions:
      - action: notify.mobile_app_iphone
        data:
          title: "Škoda Bestellstatus"
          message: >
            {{ states(trigger.entity_id) }}
            {% if state_attr(trigger.entity_id, 'order_confirmed_date') %}
            ({{ state_attr(trigger.entity_id, 'order_confirmed_date') | as_datetime | as_local | strftime('%d.%m.%Y') }})
            {% endif %}
```

## Disclaimer

This integration uses an **unofficial, reverse-engineered** MyŠkoda API. It is not affiliated with Škoda Auto. Use at your own risk.

## License

MIT
