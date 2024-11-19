#!/bin/bash
set -euo pipefail

source "/app/.venv/bin/activate"

fastapi run ./src/tag_sensor/server/application.py
