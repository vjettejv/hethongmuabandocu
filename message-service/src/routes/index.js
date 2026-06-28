const express = require('express');
const queryController = require('../controllers/queryController');
const commandController = require('../controllers/commandController');
const verifyToken = require('../middlewares/auth');

const router = express.Router();

router.get('/health', (req, res) => res.status(200).send('Message Service OK'));

// Message routes
router.get('/contacts', verifyToken, queryController.getContacts);
router.get('/:contactId', verifyToken, queryController.getHistory);
router.post('/', verifyToken, commandController.sendMessage);

// Notification routes
router.post('/notifications', commandController.createNotification);
router.get('/notifications', verifyToken, queryController.getNotifications);
router.put('/notifications/read-all', verifyToken, commandController.markAllRead);

module.exports = router;