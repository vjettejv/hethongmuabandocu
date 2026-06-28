const express = require('express');
const commandController = require('../controllers/commandController');

const router = express.Router();

router.post('/email', commandController.sendEmail);

module.exports = router;