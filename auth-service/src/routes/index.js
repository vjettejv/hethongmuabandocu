const express = require('express');
const commandController = require('../controllers/commandController');
const queryController = require('../controllers/queryController');

const router = express.Router();

// Commands (Write operations & Authentication operations generating state/tokens)
router.post('/register', commandController.register);
router.post('/login', commandController.login);
router.post('/verify-otp', commandController.verifyOtp);

// Queries (Read operations)
router.get('/:id', queryController.getUserById);
router.post('/verify', queryController.verifyToken); // Validating is conceptually read-only

module.exports = router;
