'use strict';
const pa = require('naudiodon');

console.log('=== Host APIs ===');
try {
  const apis = pa.getHostAPIs();
  console.log(JSON.stringify(apis, null, 2));
} catch (e) {
  console.log('getHostAPIs not available:', e.message);
}

console.log('\n=== All Devices (full detail) ===');
const devices = pa.getDevices();
devices.forEach(d => {
  console.log(`[${d.id}] "${d.name}"`);
  console.log(`     hostAPIName=${d.hostAPIName} maxIn=${d.maxInputChannels} maxOut=${d.maxOutputChannels} defaultSampleRate=${d.defaultSampleRate}`);
});
