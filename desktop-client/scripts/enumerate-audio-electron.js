'use strict';
const { app } = require('electron');

app.whenReady().then(() => {
  const pa = require('naudiodon');

  console.log('=== Host APIs ===');
  try {
    const apis = pa.getHostAPIs();
    console.log(JSON.stringify(apis, null, 2));
  } catch (e) {
    console.log('getHostAPIs not available:', e.message);
  }

  console.log('\n=== All Devices ===');
  const devices = pa.getDevices();
  devices.forEach(d => {
    console.log(`[${d.id}] "${d.name}" | host=${d.hostAPIName} | in=${d.maxInputChannels} out=${d.maxOutputChannels} rate=${d.defaultSampleRate}`);
  });

  app.quit();
});
