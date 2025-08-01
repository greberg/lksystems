# LK Systems for Home Assistant

A custom integration for Home Assistant to monitor and control LK Systems thermostats from LK webserver.

## Features

- Automatically discovers active thermostats
- Creates both temperature sensors and climate entities
- Supports setting target temperature via Home Assistant UI
- Handles tid mapping and decoding from LK’s `main.json`
- Optimized to work with sections and unused thermostat slots

## Configuration

Install via HACS by adding this repository as a custom source. Then add the integration via Home Assistant UI.
