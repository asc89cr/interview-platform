import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: "https://e2f2485b49fe49cd01b85a2b38dd5755@o4511859048972288.ingest.us.sentry.io/4511859059326976",
  tracesSampleRate: 0.2,
});
