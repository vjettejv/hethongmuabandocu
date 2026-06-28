const { Sequelize } = require('sequelize');
const { Message } = require('../models');

const getContactsHandler = async (userId) => {
    return [];
};

const getHistoryHandler = async (userId, contactId) => {
    return [];
};

module.exports = { getContactsHandler, getHistoryHandler };