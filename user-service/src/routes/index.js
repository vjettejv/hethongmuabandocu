const express = require('express');
const queryController = require('../controllers/queryController');
const commandController = require('../controllers/commandController');
const verifyToken = require('../middlewares/auth');

const router = express.Router();

router.get('/me', verifyToken, queryController.getMyProfile);
router.get('/:authId', queryController.getProfileByAuthId);
router.put('/me', verifyToken, commandController.updateMyProfile);
router.put('/:authId', commandController.updateProfileByAuthId);

module.exports = router;