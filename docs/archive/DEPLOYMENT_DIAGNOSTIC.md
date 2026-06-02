# AlphaScope Deployment Diagnostic

Date: 2026-06-02

## Objective

Determine why the AlphaScope website is not updating even though automation
completes successfully and `origin/web-launch` receives new commits.

## Executive Finding

The repository expects Cloudflare Pages to deploy from the `web-launch` branch.
The latest generated-data commit is present on `origin/web-launch`, but the
repository default remote head still points at `origin/main`.

Based on the repository evidence, the most likely root cause is a Cloudflare
Pages configuration mismatch: the Pages project is probably not configured to
build/deploy production from `web-launch`, or it is connected to a different
repository/project/branch than the automation pushes.

This cannot be fully proven from the repository alone because Cloudflare Pages
project settings and deployment history are external to Git.

## Repository Evidence

### No Cloudflare Pages config file is checked in

Searches for Cloudflare Pages configuration found no checked-in deployment
configuration such as:

- `wrangler.toml`
- Cloudflare-specific config files
- Pages `_headers`
- Pages `_redirects`
- `.pages*`

There is no repository-side config that defines the Cloudflare Pages production
branch, build command, or output directory.

### Deployment automation targets `web-launch`

The automation script is `scripts/alphascope_refresh.sh`.

Important settings:

```bash
REMOTE="origin"
DEPLOY_BRANCH="web-launch"
SOURCE_BRANCH="feature/investor-dashboard-v2"
DEPLOY_WORKTREE="$REPO_DIR/.deploy/web-launch"
```

The script:

1. Runs the pipeline with `.venv/bin/python -m app.main full`.
2. Validates generated JSON files.
3. Copies only generated web data files into the `web-launch` worktree.
4. Commits changed generated data.
5. Pushes `origin web-launch`.

Generated files pushed by automation:

```text
web/data/latest-report.json
web/data/full-report.json
web/data/investor-rankings.json
web/data/data-health.json
```

The script logs the expected model explicitly:

```text
event=deployment_model source_branch=<current> target=origin/web-launch mode=data_files_only
```

### README documents Cloudflare deployment from `web-launch`

`README.md` documents the production refresh path as:

```text
alphascope.timer
  -> alphascope.service
  -> scripts/alphascope_refresh.sh
  -> python -m app.main full
  -> web/data/*.json validation
  -> git commit when generated web data changed
  -> git push origin web-launch
  -> Cloudflare Pages deployment from web-launch
```

The troubleshooting section also says:

```text
Confirm the commit reached GitHub, then check that Cloudflare Pages is connected
to the `web-launch` branch.
```

### Git branch state

Current local working branch:

```text
feature/investor-dashboard-v2
```

Remote head:

```text
origin/HEAD -> origin/main
```

Latest relevant branch tips:

```text
origin/web-launch 65b4573 refresh AlphaScope web data 2026-06-02 19:35 UTC
origin/main       44d79e6 Update README to reflect resilient AlphaScope platform architecture
```

This means `web-launch` is receiving the generated-data commits, while `main`
is not.

### `main` does not contain the static website

`origin/main` only contains:

```text
.gitignore
README.md
app
config
requirements.txt
```

`origin/web-launch` contains the static website under `web/`, including:

```text
web/index.html
web/intelligence.html
web/opportunity.html
web/data/latest-report.json
web/data/full-report.json
web/data/investor-rankings.json
web/data/data-health.json
```

If Cloudflare Pages production is configured to deploy from `main`, then pushes
to `web-launch` will not update the production site.

## Expected Deployment Model

The expected model is Git-driven Cloudflare Pages deployment.

Expected source:

```text
GitHub repository: dunga101/alphascope
Branch: web-launch
Static asset root/output: web
```

Expected automation:

```text
systemd timer/service
  -> local Python pipeline
  -> generated JSON files under web/data
  -> commit to web-launch
  -> push to GitHub
  -> Cloudflare Pages notices the Git commit
  -> Cloudflare deploys the static web directory
```

There is no evidence in this repository that deployment is direct-upload based.
No script invokes `wrangler pages deploy`, no Cloudflare API upload is present,
and no direct-upload credentials or deployment commands are referenced.

## Branch Determination

Cloudflare is supposed to deploy from:

```text
web-launch
```

Cloudflare is not expected to deploy from:

```text
main
```

Cloudflare is not expected to deploy from:

```text
feature/investor-dashboard-v2
```

The feature branch is only an allowed branch for running the automation. It is
not the publication branch.

## Probable Root Cause

Most likely:

```text
Cloudflare Pages production branch is set to main instead of web-launch.
```

Why this fits the evidence:

- `origin/web-launch` receives new commits.
- The script exits successfully after `git_push`.
- `origin/main` remains unchanged.
- `origin/main` does not contain the static `web/` site.
- The repo default remote head is `origin/main`, which is a common default
  branch selection when creating a Pages project.
- The repository has no checked-in Cloudflare config that would override this.

Other plausible Cloudflare-side causes:

- Pages project is connected to the wrong GitHub repository.
- Pages project is connected to the right repository but production branch is
  not `web-launch`.
- Pages project has automatic deployments disabled.
- Pages project build settings use the wrong output directory.
- Cloudflare is deploying successfully, but from a directory other than `web`.
- A custom domain is pointed at a different Pages project than the one connected
  to this repository.
- Deployment is stuck or failing in Cloudflare even though Git push succeeds.
- A stale CDN/browser cache is hiding the update, though this is less likely if
  Cloudflare shows no new deployment for commit `65b4573`.

## Cloudflare Dashboard Validation Steps

Perform these checks in the Cloudflare dashboard.

### 1. Confirm the Pages project

Open:

```text
Cloudflare Dashboard -> Workers & Pages -> Pages
```

Select the AlphaScope Pages project.

Validate:

- The project is connected to GitHub.
- The connected repository is `dunga101/alphascope`.
- The production/custom domain you are checking is attached to this same Pages
  project.

If the domain is attached to a different Pages project, that is the root cause.

### 2. Check the latest deployment commit

Open:

```text
Pages project -> Deployments
```

Look for a deployment corresponding to:

```text
commit: 65b4573
branch: web-launch
message: refresh AlphaScope web data 2026-06-02 19:35 UTC
```

Interpretation:

- If no deployment exists for `65b4573`, Cloudflare did not trigger from
  `web-launch`.
- If a deployment exists and failed, inspect the build logs.
- If a deployment exists and succeeded, compare its deployment URL directly
  against the custom domain.

### 3. Check production branch

Open:

```text
Pages project -> Settings -> Builds & deployments
```

Validate:

```text
Production branch: web-launch
```

If it says `main`, change it to `web-launch` or configure previews/production
according to the desired model.

### 4. Check build configuration

In the same settings area, validate the build settings for a static site.

Expected for this repository:

```text
Build command: empty or no-op
Build output directory: web
Root directory: repository root, unless Cloudflare uses web as the root
```

If Cloudflare requires a build command, use a no-op command appropriate for the
Pages UI, but the important output directory is `web`.

Incorrect examples:

```text
Build output directory: /
Build output directory: public
Build output directory: dist
Root directory: app
```

Any of those would prevent the expected static dashboard from being published.

### 5. Check automatic deployment triggers

Validate that automatic deployments are enabled for Git pushes.

Look for settings related to:

- Automatic deployments
- Git integration
- Production branch deploys
- Branch include/exclude rules

Expected:

```text
Push to web-launch triggers a production deployment.
```

If branch filters exclude `web-launch`, Cloudflare will ignore the push.

### 6. Check deployment build logs

For the latest `web-launch` deployment, inspect logs for:

- Git branch checked out by Cloudflare.
- Commit SHA.
- Build command.
- Output directory.
- Published files.
- Any warnings about missing output directory.

The build log should show:

```text
branch: web-launch
commit: 65b4573
output directory: web
```

### 7. Validate the direct deployment URL

From the deployment record, open the unique `*.pages.dev` deployment URL.

Then validate:

```text
/data/latest-report.json
/data/investor-rankings.json
/data/data-health.json
```

Confirm that `latest-report.json` contains:

```text
Generated: 2026-06-02 19:35
```

or that the JSON timestamp matches the latest automation run.

If the unique deployment URL is current but the custom domain is stale, the
problem is domain routing, caching, or the custom domain is attached elsewhere.

### 8. Validate the custom domain

Open the production custom domain and hard-refresh.

Then fetch the data endpoint directly:

```text
https://<custom-domain>/data/latest-report.json
```

Compare it with the unique Pages deployment URL:

```text
https://<deployment-id>.<project>.pages.dev/data/latest-report.json
```

Interpretation:

- Pages deployment URL current, custom domain stale: domain/cache/routing issue.
- Both stale: Cloudflare did not deploy the latest `web-launch` commit or is
  publishing the wrong directory.

## Local Validation Commands

These commands validate the Git side before looking at Cloudflare:

```bash
cd /home/dmudalige/projects/alphascope
git log origin/web-launch --oneline -5
git log origin/main --oneline -5
git ls-tree --name-only origin/web-launch web
git ls-tree --name-only origin/main web
git show --name-only --oneline origin/web-launch -1
```

Expected:

- `origin/web-launch` includes the latest refresh commit.
- `origin/main` does not include that refresh commit.
- `origin/web-launch` contains `web/`.
- `origin/main` does not contain `web/`.

## Conclusion

The local automation and Git push path are working. The repository is designed
for Git-driven Cloudflare Pages deployment from `web-launch`, with `web` as the
static output directory. Because the new commits are reaching `origin/web-launch`
but the website does not update, the failure point is almost certainly in
Cloudflare Pages configuration or domain routing, not the systemd automation.

The first setting to verify is:

```text
Cloudflare Pages production branch = web-launch
```
###Final Root Cause

Initial deployment issue was caused by GitHub deploy-key authentication failure,
preventing automation from pushing updates to web-launch.

After deploy-key remediation:

- Automation completed successfully.
- GitHub received web-launch updates.
- Cloudflare Pages automatically deployed commit 65b4573.
- Production deployment succeeded.

Remaining apparent issue was browser-side caching.
A hard refresh immediately displayed the latest deployed content.

Resolution:
GitHub deploy key configured correctly and browser cache cleared.

Status:
Resolved.