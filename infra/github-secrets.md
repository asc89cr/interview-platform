# GitHub Actions — Required Secrets

Set these in: GitHub repo → Settings → Secrets and variables → Actions

## Backend / Railway

| Secret | Description |
|--------|-------------|
| `RAILWAY_TOKEN` | Railway API token (railway.app → Account → Tokens) |
| `DATABASE_URL` | Production Postgres URL (Neon/Supabase connection string) |

## Web Dashboard / Vercel

| Secret | Description |
|--------|-------------|
| `VERCEL_TOKEN` | Vercel API token (vercel.com → Settings → Tokens) |
| `VERCEL_ORG_ID` | Found in `.vercel/project.json` after `vercel link` |
| `VERCEL_PROJECT_ID` | Found in `.vercel/project.json` after `vercel link` |

## Desktop Client — Code Signing

| Secret | Description |
|--------|-------------|
| `VITE_API_BASE_URL` | Your Railway backend URL, e.g. `https://your-app.up.railway.app` |
| `WINDOWS_CERT_P12_BASE64` | Windows code signing cert (base64-encoded .p12) |
| `WINDOWS_CERT_PASSWORD` | Password for the Windows .p12 cert |
| `APPLE_CERT_P12_BASE64` | Apple Developer cert (base64-encoded .p12) |
| `APPLE_CERT_PASSWORD` | Password for the Apple .p12 cert |
| `APPLE_ID` | Apple ID email used for notarization |
| `APPLE_APP_SPECIFIC_PASSWORD` | App-specific password from appleid.apple.com |
| `APPLE_TEAM_ID` | Apple Developer Team ID |

## Notes

- `DATABASE_URL` in the `migrate` job must be the **production** DB URL with
  a direct (non-pooled) connection string for Alembic to run DDL migrations.
  Neon provides both pooled and direct URLs — use the direct one here.

- To get `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID`, run once locally:
  ```
  cd web-dashboard
  npx vercel link
  cat .vercel/project.json
  ```
