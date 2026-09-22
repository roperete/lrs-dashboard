#!/bin/zsh
# Apply one finished provenance unit end to end: collect the workflow journal, write the
# agreed claims, refresh composition statuses, export, verify, score, render-check.
# Usage: scripts/apply_unit.sh <workflow transcript dir> <label>
# Commits nothing; prints the summary the commit message needs.
set -e -o pipefail
R="${0:A:h:h}"
W="$1"; LABEL="$2"
python3 "$R/scripts/collect_findings.py" "$W" --label "$LABEL"
echo "--- apply ---"
python3 "$R/scripts/apply_provenance.py" --findings "$R/documentation/provenance-findings-$LABEL.json" --write --log-out "$R/documentation/provenance-apply-log-$LABEL.json" | grep -v "^log ->"
echo "--- status ---"
python3 "$R/scripts/refresh_composition_status.py"
python3 "$R/scripts/export_json.py" | grep "^Suppressed"
python3 "$R/scripts/verify_data.py" | tail -1
python3 "$R/scripts/provenance_report.py" | grep "^| [123]\."
"$R/node_modules/.bin/tsx" --tsconfig "$R/tsconfig.json" "$R/scripts/render_smoke.tsx" | tail -1
sqlite3 "$R/lrs.sqlite" "select 'verified '||count(*) from simulants where composition_status='verified'; select 'sourced scalars '||count(*) from property_sources;" | paste -sd' ' -
