const { createPostHandler, deleteMyPostHandler, updatePostStatusHandler, deleteAdminPostHandler } = require('../commands/postCommands');

const createPost = async (req, res) => {
    try {
        const post = await createPostHandler(req.user.id, req.body, req.files);
        res.status(201).json({ message: 'Post created successfully', post });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

const deleteMyPost = async (req, res) => {
    try {
        const result = await deleteMyPostHandler(req.user.id, req.params.id);
        res.json(result);
    } catch (error) {
        if (error.message.includes('not found')) return res.status(404).json({ error: error.message });
        res.status(500).json({ error: error.message });
    }
};

const updatePostStatus = async (req, res) => {
    try {
        const post = await updatePostStatusHandler(req.params.id, req.body.status);
        res.json({ data: post });
    } catch (error) {
        if (error.message === 'Not found') return res.status(404).json({ error: error.message });
        res.status(500).json({ error: error.message });
    }
};

const deleteAdminPost = async (req, res) => {
    try {
        const result = await deleteAdminPostHandler(req.params.id);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

module.exports = { createPost, deleteMyPost, updatePostStatus, deleteAdminPost };