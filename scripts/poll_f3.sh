#!/usr/bin/env bash
# F3 poll: wait for the 2026-07-29 US close to exist, then run the decomposition.
# Respects throttle discipline: long intervals, no tightening, single symbol.
cd "$(dirname "$0")/.."
STATE=data/derived/poll/f3_state.txt
echo "armed $(date -u +%FT%TZ) — waiting for 2026-07-29 on both legs" > "$STATE"
while true; do
  HAVE=$(uv run python -c "
from pipeline.ingest._common import latest_raw_file
import pandas as pd
try:
    a=pd.read_csv(latest_raw_file('d1_prices','skhy_adr_daily.csv'))
    print('yes' if (a.date=='2026-07-29').any() else 'no')
except Exception: print('no')" 2>/dev/null | tail -1)
  if [ "$HAVE" = "yes" ]; then echo "HAVE 07-29 already stored $(date -u +%FT%TZ)" >> "$STATE"; break; fi
  NOW=$(date -u +%s); TARGET=$(date -u -j -f "%Y-%m-%dT%H:%M:%S" "2026-07-29T20:05:00" +%s 2>/dev/null || echo 0)
  if [ "$NOW" -ge "$TARGET" ]; then
    echo "attempting pull $(date -u +%FT%TZ)" >> "$STATE"
    uv run python -m pipeline.ingest.d1_prices --only skhy_adr_daily,skhynix_local_daily --new-partition --no-cache >> "$STATE" 2>&1
    GOT=$(uv run python -c "
from pipeline.ingest._common import latest_raw_file
import pandas as pd
a=pd.read_csv(latest_raw_file('d1_prices','skhy_adr_daily.csv'))
print('yes' if (a.date=='2026-07-29').any() else 'no')" 2>/dev/null | tail -1)
    if [ "$GOT" = "yes" ]; then echo "F3 DATA READY $(date -u +%FT%TZ)" >> "$STATE"; break; fi
    echo "  07-29 not yet published; sleeping 30m" >> "$STATE"
    sleep 1800
  else
    sleep 1800
  fi
done
echo "poll complete $(date -u +%FT%TZ)" >> "$STATE"
