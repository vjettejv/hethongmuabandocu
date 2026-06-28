const { getPostsHandler, getMyPostsHandler, getPostByIdHandler, getAdminPostsHandler } = require('../queries/postQueries');

const getPosts = async (req, res) => {
    try {
        const posts = await getPostsHandler(req.query);
        res.json(posts);
    } catch (error) { res.status(500).json({ error: error.message }); }
};

const getMyPosts = async (req, res) => {
    try {
        const posts = await getMyPostsHandler(req.user.id);
        res.json(posts);
    } catch (error) { res.status(500).json({ error: error.message }); }
};

const getPostById = async (req, res) => {
    try {
        const post = await getPostByIdHandler(req.params.id);
        res.json(post);
    } catch (error) {
        if (error.message === 'Post not found') return res.status(404).json({ error: error.message });
        res.status(500).json({ error: error.message });
    }
};

const getAdminPosts = async (req, res) => {
    try {
        const posts = await getAdminPostsHandler();
        res.json({ data: posts });
    } catch (error) { res.status(500).json({ error: error.message }); }
};

module.exports = { getPosts, getMyPosts, getPostById, getAdminPosts };