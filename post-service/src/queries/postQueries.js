const { Sequelize } = require('sequelize');
const { Post, Image } = require('../models');
const { fetchCategoriesMap, formatPost } = require('../utils/helpers');

const getPostsHandler = async ({ categoryId, keyword, status }) => {
    const whereClause = {};
    if (categoryId) whereClause.categoryId = categoryId;
    if (status) whereClause.status = status;
    if (keyword) whereClause.title = { [Sequelize.Op.like]: `%${keyword}%` };

    const posts = await Post.findAll({ 
        where: whereClause, 
        include: Image,
        order: [['createdAt', 'DESC']] 
    });
    const catMap = await fetchCategoriesMap();
    return posts.map(p => formatPost(p, catMap));
};

const getMyPostsHandler = async (userId) => {
    const posts = await Post.findAll({ 
        where: { userId }, 
        include: Image,
        order: [['createdAt', 'DESC']]
    });
    const catMap = await fetchCategoriesMap();
    return posts.map(p => formatPost(p, catMap));
};

const getPostByIdHandler = async (id) => {
    const post = await Post.findByPk(id, { include: Image });
    if (!post) throw new Error('Post not found');
    const catMap = await fetchCategoriesMap();
    return formatPost(post, catMap);
};

const getAdminPostsHandler = async () => {
    const posts = await Post.findAll({ include: Image, order: [['createdAt', 'DESC']] });
    const catMap = await fetchCategoriesMap();
    return posts.map(p => formatPost(p, catMap));
};

module.exports = { getPostsHandler, getMyPostsHandler, getPostByIdHandler, getAdminPostsHandler };