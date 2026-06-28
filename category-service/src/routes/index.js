const express = require('express');
const queryController = require('../controllers/queryController');
const commandController = require('../controllers/commandController');

const router = express.Router();

router.get('/', queryController.getAllCategories);
router.post('/', commandController.createCategory);
router.post('/admin/categories', commandController.createAdminCategory);

module.exports = router;