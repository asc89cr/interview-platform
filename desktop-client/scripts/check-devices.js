'use strict';
const pa = require('naudiodon');
const devices = pa.getDevices();
const d = devices.find(x => x.id === 2);
console.log(JSON.stringify(d, null, 2));
