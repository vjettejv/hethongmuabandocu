const express = require('express');
const queryController = require('../controllers/queryController');
const commandController = require('../controllers/commandController');
const upload = require('../middlewares/upload');

const router = express.Router();

router.get('/user/:userId', queryController.getReviews);
router.post('/', upload.single('image'), commandController.createReview);
router.put('/:id', upload.single('image'), commandController.updateReview);
router.delete('/:id', commandController.deleteReview);

module.exports = router;