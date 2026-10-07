'use strict';
require('./legacy-schema-guard.cjs');
// Dependency injection for isolated reference tests only; business handlers stay original.
const fetch = global.fetch;
global.fetch = (url, options) => {
  const prefix = 'http://user-service:3002';
  if (String(url).startsWith(prefix + '/')) {
    url = process.env.USER_SERVICE_URL + String(url).slice(prefix.length);
  }
  return fetch(url, options);
};
