const express = require('express');
const queryController = require('../controllers/queryController');
const commandController = require('../controllers/commandController');

const router = express.Router();

router.get('/', queryController.search);
router.post('/sync', commandController.syncIndex);

module.exports = router;