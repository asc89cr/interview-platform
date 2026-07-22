'use strict';

/**
 * Mac notarization script (called by electron-builder afterSign hook).
 * Requires env vars: APPLE_ID, APPLE_ID_PASSWORD, APPLE_TEAM_ID
 */

const { notarize } = require('@electron/notarize');

exports.default = async function notarizing(context) {
  const { electronPlatformName, appOutDir } = context;
  if (electronPlatformName !== 'darwin') return;

  const appName = context.packager.appInfo.productFilename;
  const appBundleId = 'com.interviewplatform.client';

  if (!process.env.APPLE_ID) {
    console.log('[notarize] APPLE_ID not set — skipping notarization');
    return;
  }

  console.log(`[notarize] Notarizing ${appBundleId}…`);
  await notarize({
    tool: 'notarytool',
    appBundleId,
    appPath: `${appOutDir}/${appName}.app`,
    appleId: process.env.APPLE_ID,
    appleIdPassword: process.env.APPLE_ID_PASSWORD,
    teamId: process.env.APPLE_TEAM_ID,
  });
  console.log('[notarize] Done.');
};
