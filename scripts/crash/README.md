# Crash suite

Scenario files for `scripts/ui_scenario.mjs`: each clicks through part of the app and fails if
the page raises an error or goes blank. Run them all against a build:

    npm run build && npx vite preview --port 4173 &
    chrome --headless=new --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --remote-debugging-port=9333 --user-data-dir=/tmp/lrs-chrome &
    for f in scripts/crash/*.json; do node scripts/ui_scenario.mjs 9333 http://localhost:4173/lrs-dashboard/ "$f" /tmp || echo "FAILED $f"; done

Also run `views.json` with a Chrome started without WebGL (`--disable-gpu`): the globe must fail
into its message, not blank the page. And open a malformed shared link, e.g.
`?view=nonsense&sim=NOPE&cmp=,,&f=type:;bulk_density:a..b`.
