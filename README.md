# Škoda Order Status for Home Assistant

Home Assistant integration to track the status of a **pending Škoda vehicle order** via the unofficial MyŠkoda API.

This fills the gap left by the official Škoda integration: order tracking in the MyŠkoda app ("Track & Explore") works **before** a VIN exists.

## Features

- Native Home Assistant sensor (no REST API workaround)
- Automatic discovery of open orders in your MyŠkoda account
- German status labels and checkpoint dates
- Configurable polling interval (default: 1 hour)
- Refresh token stored securely in the config entry

## Installation

### HACS (recommended)

1. Open **HACS → Integrations**
2. Click the menu (⋮) → **Custom repositories**
3. Add `https://github.com/SentiQ/homeassistant-skoda-order-status`
4. Category: **Integration**
5. Install **Škoda Order Status** and restart Home Assistant

### Manual

Copy `custom_components/skoda_order_status` into your Home Assistant `custom_components` directory and restart.

## Configuration

1. Go to **Settings → Devices & services → Add integration**
2. Search for **Škoda Order Status**
3. Sign in with your MyŠkoda email and password
4. Select your order if multiple are available

### Options

- **Update interval**: polling interval in seconds (900–86400, default 3600)

## Entities

| Entity | Description |
|--------|-------------|
| `sensor.<device>_bestellstatus` | Current order status |

Attributes include model, trim, colours, commission ID, checkpoint dates, and pending steps.

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

## Legacy script

The original cron-based poller is still available in `scripts/poll_order_status.py` for reference.

## Disclaimer

This integration uses an **unofficial, reverse-engineered** MyŠkoda API. It is not affiliated with Škoda Auto. Use at your own risk.

## Development

Repository validation (HACS + hassfest) runs via GitHub Actions. See [HACS publisher documentation](https://www.hacs.xyz/docs/publish/).

```bash
# Local syntax check
python3 -m compileall custom_components/skoda_order_status
```

## License

MIT
