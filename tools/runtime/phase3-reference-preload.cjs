'use strict';
require('./legacy-schema-guard.cjs');
// Isolated test transport injection; original Node handlers remain untouched.
const fetch = global.fetch;
global.fetch = (url, options) => {
  const prefix = 'http://user-service:3002';
  if (String(url).startsWith(prefix + '/')) {
    url = process.env.USER_SERVICE_URL + String(url).slice(prefix.length);
  }
  return fetch(url, options);
};
if (process.env.PHASE3_DISABLE_TEST_SEED === 'true') {
  // Suppress only legacy startup fixtures in the schema-only Category reference.
  // List/create handlers continue using the actual model/database unchanged.
  const Category = require('./src/models/Category');
  Category.count = async () => 1;
}
