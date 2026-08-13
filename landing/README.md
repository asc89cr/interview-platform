# Landing Site (standalone)

The public marketing landing page. **Standalone and additive** — it does **not**
touch or depend on the `web-dashboard`, `desktop-client`, or `backend`. It's a
single static `index.html` (styles inlined, no build step).

Owned by the **Marketing Agent (10)**. Brand name ("InterviewAce"), hero copy,
and positioning are placeholders to be finalized from
`docs/marketing/marketing-plan.md`.

## Preview locally
```powershell
# From the repo root
cd landing
python -m http.server 8080
# open http://localhost:8080
```

## Deploy (any static host — separate from the dashboard)
- **Vercel:** `vercel deploy` from this folder (new, separate project).
- **Netlify:** drag-and-drop the `landing/` folder, or connect the repo with
  publish directory `landing`.
- **Cloudflare Pages / GitHub Pages / S3+CloudFront:** upload `index.html`.

Keep it on the marketing apex/root domain (e.g. `interviewace.com`) and point the
app at a subdomain (e.g. `app.interviewace.com`). This keeps the landing site
fully decoupled from the product.

## Before going live
- [ ] Replace CTA `href="#"` links with real signup / Stripe / contact URLs.
- [ ] Finalize brand name + hero copy from the marketing plan.
- [ ] Add real `/terms` and `/privacy` pages (Legal Advisor 09).
- [ ] Wire analytics (conversion tracking) — Marketing.
- [ ] Legal review of all public claims (Agent 09).
