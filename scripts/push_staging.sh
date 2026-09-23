#!/bin/zsh
# Push the staging branch, refusing to do so unless the version the sidebar shows has
# changed since the last push. The number in the sidebar is how a reader tells whether the
# page in front of them contains a given change, so it must never repeat across pushes.
#
# Usage: scripts/push_staging.sh        (bump first with scripts/bump_version.py)
set -e -o pipefail
R="${0:A:h:h}"
SIDEBAR="src/components/sidebar/Sidebar.tsx"

if [ -n "$(git -C "$R" status --porcelain)" ]; then
  echo "refusing: working tree is dirty; commit first" >&2
  git -C "$R" status --short >&2
  exit 1
fi

git -C "$R" fetch -q origin staging
local_v=$(grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' "$R/$SIDEBAR" | head -1)
remote_v=$(git -C "$R" show origin/staging:$SIDEBAR 2>/dev/null | grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)

if [ "$local_v" = "$remote_v" ]; then
  echo "refusing: the sidebar still shows $local_v, the version already on origin/staging." >&2
  echo "run:  python3 scripts/bump_version.py --body \"what changed\"   then commit and retry" >&2
  exit 1
fi
if ! grep -q "^## $local_v " "$R/CHANGELOG.md"; then
  echo "refusing: $local_v has no CHANGELOG section" >&2
  exit 1
fi

echo "$remote_v -> $local_v"
gh auth switch --user roperete >/dev/null
git -C "$R" push origin staging
status=$?
gh auth switch --user alvaroENPICOM >/dev/null
exit $status
