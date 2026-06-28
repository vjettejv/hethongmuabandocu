const fetchCategoriesMap = async () => {
    try {
        const res = await fetch(process.env.CATEGORY_SERVICE_URL || 'http://category-service:3004');
        if (!res.ok) return {};
        const json = await res.json();
        const list = json.data || json || [];
        const map = {};
        list.forEach(c => map[c.id] = c);
        return map;
    } catch(e) { return {}; }
};

const syncToSearch = async (post, catMap) => {
    try {
        const p = post.toJSON ? post.toJSON() : post;
        const category = catMap[p.categoryId] || { name: 'Đang cập nhật' };
        let imageUrl = null;
        if (p.Images && p.Images.length > 0) imageUrl = p.Images[0].imageUrl;
        else if (post.Images && post.Images.length > 0) imageUrl = post.Images[0].imageUrl;
        
        await fetch((process.env.SEARCH_SERVICE_URL || 'http://search-service:3008') + '/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                postId: p.id,
                title: p.title,
                description: p.description,
                price: p.price,
                categoryId: p.categoryId,
                imageUrl: imageUrl,
                categoryName: category.name,
                status: p.status
            })
        });
    } catch (e) { console.error('Search sync failed', e.message); }
};

const formatPost = (post, catMap) => {
    const p = post.toJSON ? post.toJSON() : post;
    p.price = parseFloat(p.price) || 0;
    p.Category = catMap[p.categoryId] || { id: p.categoryId, name: 'Đang cập nhật' };
    return p;
};

module.exports = { fetchCategoriesMap, syncToSearch, formatPost };