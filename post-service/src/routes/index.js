const express = require('express');
const queryController = require('../controllers/queryController');
const commandController = require('../controllers/commandController');
const verifyToken = require('../middlewares/auth');
const upload = require('../middlewares/upload');

const router = express.Router();

router.get('/', queryController.getPosts);
router.get('/my-posts', verifyToken, queryController.getMyPosts);
router.get('/admin/posts', verifyToken, queryController.getAdminPosts);
router.get('/:id', queryController.getPostById);

router.post('/', verifyToken, upload.array('images', 5), commandController.createPost);
router.delete('/:id', verifyToken, commandController.deleteMyPost);

router.put('/admin/posts/:id', verifyToken, commandController.updatePostStatus);
router.delete('/admin/posts/:id', verifyToken, commandController.deleteAdminPost);

module.exports = router;