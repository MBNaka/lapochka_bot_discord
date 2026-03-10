#!/usr/bin/env sh
set -eu

if [ "${ENABLE_ZAPRET:-0}" = "1" ] && [ "$(uname -s)" = "Linux" ]; then
  if [ -x "/opt/zapret/start.sh" ]; then
    echo "[entrypoint] ENABLE_ZAPRET=1, running /opt/zapret/start.sh"
    /opt/zapret/start.sh || echo "[entrypoint] zapret script finished with non-zero status"
  else
    echo "[entrypoint] ENABLE_ZAPRET=1, but /opt/zapret/start.sh was not found/executable"
  fi
fi

exec "$@"
