'use strict';
const keytar = require('keytar');
const SVC = 'InterviewPlatformClient';

Promise.all([
  keytar.deletePassword(SVC, 'jwt'),
  keytar.deletePassword(SVC, 'refresh_token'),
  keytar.deletePassword(SVC, 'session_id'),
]).then(() => {
  console.log('Credentials cleared. Run npm start again — login window will appear.');
}).catch(err => {
  console.error('Error:', err.message);
});
