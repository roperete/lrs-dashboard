# Branching Strategy

## Branch Overview

```
dev  ──push──>  staging  ──merge──>  main
 |                 |                   |
 |                 |                   +-- Production (live)
 |                 |                       https://roperete.github.io/lrs-dashboard/
 |                 |
 |                 +-- Preview / QA
 |                     https://roperete.github.io/lrs-dashboard/staging/
 |
 +-- Active development (no deployment)
```

## Branches

| Branch    | Purpose                        | Deploys to         | Merges into |
|-----------|--------------------------------|--------------------|-------------|
| `dev`     | Daily development work         | Nothing            | `staging`   |
| `staging` | Preview and QA before release  | `/staging/`        | `main`      |
| `main`    | Production — stable, live site | `/` (root)         | Never       |

## Workflow

### Daily development
Work on `dev`. Commit freely. Nothing deploys.

```bash
git checkout dev
# ... make changes ...
git add -A && git commit -m "feat: whatever"
```

### Push to staging for preview
When ready to preview changes, merge dev into staging and push.

```bash
git checkout staging
git merge dev
git push origin staging
```

This triggers the GitHub Actions workflow, which builds both `main` (production) and `staging` (preview) and deploys them together to GitHub Pages. Preview at: `https://roperete.github.io/lrs-dashboard/staging/`

### Promote to production
After QA on staging, merge staging into main.

```bash
git checkout main
git merge staging
git push origin main
```

This triggers the same workflow, rebuilding both sites. Production updates at: `https://roperete.github.io/lrs-dashboard/`

### Hotfix flow
For urgent production fixes, branch from main, fix, merge back to main, then backport to staging and dev.

```bash
git checkout main
git checkout -b hotfix/fix-name
# ... fix ...
git checkout main && git merge hotfix/fix-name && git push origin main
git checkout staging && git merge main && git push origin staging
git checkout dev && git merge staging
git branch -d hotfix/fix-name
```

## Deployment Details

- **CI/CD**: `.github/workflows/deploy.yml`
- **Triggers**: Push to `main` or `staging`
- **Build tool**: Vite with `--base /lrs-dashboard/` (production) and `--base /lrs-dashboard/staging/` (staging)
- **Hosting**: GitHub Pages via `actions/deploy-pages@v4`
- Both branches are built in a single workflow run and deployed as one artifact

## For AI Agents

When working on this project:
- Always work on `dev` branch unless explicitly told otherwise
- Never push directly to `main` or `staging` without user approval
- After completing work on `dev`, ask the user if they want to push to staging
- The version displayed in the sidebar (Sidebar.tsx) should match the current release
- NEXT.md tracks backlog and changelog; update it when completing features
