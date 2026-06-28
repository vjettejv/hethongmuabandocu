const express = require('express');
const queryController = require('../controllers/queryController');
const commandController = require('../controllers/commandController');
const verifyToken = require('../middlewares/auth');

const router = express.Router();

router.post('/toggle', verifyToken, commandController.toggleFavorite);
router.get('/check/:postId', verifyToken, queryController.checkFavorite);
router.get('/my-favorites', verifyToken, queryController.getMyFavorites);

module.exports = router;