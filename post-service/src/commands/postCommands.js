const { Post, Image } = require('../models');
const { fetchCategoriesMap, syncToSearch } = require('../utils/helpers');

const createPostHandler = async (userId, data, files) => {
    const { categoryId, title, description, price, condition } = data;
    const newPost = await Post.create({ userId, categoryId, title, description, price, condition });

    if (files && files.length > 0) {
        const images = files.map(file => ({
            postId: newPost.id,
            imageUrl: `/uploads/${file.filename}`
        }));
        newPost.Images = await Image.bulkCreate(images);
    }

    const catMap = await fetchCategoriesMap();
    syncToSearch(newPost, catMap);
    return newPost;
};

const deleteMyPostHandler = async (userId, id) => {
    const post = await Post.findOne({ where: { id, userId } });
    if (!post) throw new Error('Post not found or unauthorized');
    
    await Image.destroy({ where: { postId: id } });
    await Post.destroy({ where: { id } });
    
    const catMap = await fetchCategoriesMap();
    post.status = 'deleted';
    syncToSearch(post, catMap);
    return { message: 'Deleted successfully' };
};

const updatePostStatusHandler = async (id, status) => {
    const post = await Post.findByPk(id, { include: Image });
    if (!post) throw new Error('Not found');
    
    const oldStatus = post.status;
    post.status = status;
    await post.save();
    
    const catMap = await fetchCategoriesMap();
    syncToSearch(post, catMap);
    
    if (oldStatus !== status && (status === 'approved' || status === 'rejected')) {
        const title = status === 'approved' ? 'Bài viết đã được duyệt' : 'Bài viết bị từ chối';
        const message = status === 'approved' 
            ? `Bài viết "${post.title}" của bạn đã được hiển thị trên chợ.`
            : `Bài viết "${post.title}" của bạn đã bị từ chối duyệt.`;
            
        fetch((process.env.MESSAGE_SERVICE_URL || 'http://message-service:3005') + '/notifications', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ receiverId: post.userId, title, message })
        }).catch(e => console.error('Failed to trigger notification', e.message));
    }
    return post;
};

const deleteAdminPostHandler = async (id) => {
    await Image.destroy({ where: { postId: id } });
    await Post.destroy({ where: { id } });
    return { message: 'Deleted' };
};

module.exports = { createPostHandler, deleteMyPostHandler, updatePostStatusHandler, deleteAdminPostHandler };