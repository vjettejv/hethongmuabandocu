'use strict';

// Runtime-only migration guard: preserve Node source and all existing table schemas.
if (process.env.LEGACY_SCHEMA_SYNC !== 'disabled') {
  throw new Error('Legacy schema guard requires LEGACY_SCHEMA_SYNC=disabled');
}
const Sequelize = require('sequelize');
Sequelize.prototype.sync = async function () {
  return this;
};
const query = Sequelize.prototype.query;
Sequelize.prototype.query = function (sql, ...args) {
  const statement = typeof sql === 'string' ? sql : sql.query;
  if (/^\s*(ALTER|CREATE|DROP|TRUNCATE|RENAME)\b/i.test(statement)) {
    throw new Error('Legacy schema DDL blocked during migration');
  }
  return query.call(this, sql, ...args);
};
