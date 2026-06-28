const { Sequelize, DataTypes } = require('sequelize');

const sequelize = new Sequelize(
    process.env.DB_NAME || 'post_db',
    process.env.DB_USER || 'root',
    process.env.DB_PASSWORD || 'root',
    {
        host: process.env.DB_HOST || 'post-db',
        dialect: 'mysql',
        logging: false
    }
);

const Post = sequelize.define('Post', {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    title: { type: DataTypes.STRING, allowNull: false },
    description: { type: DataTypes.TEXT },
    price: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
    categoryId: { type: DataTypes.INTEGER, allowNull: false },
    userId: { type: DataTypes.INTEGER, allowNull: false },
    status: { type: DataTypes.STRING, defaultValue: 'pending' },
    condition: { type: DataTypes.STRING }
});

const Image = sequelize.define('Image', {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    postId: { type: DataTypes.INTEGER, allowNull: false },
    imageUrl: { type: DataTypes.STRING, allowNull: false }
});

Post.hasMany(Image, { foreignKey: 'postId' });
Image.belongsTo(Post, { foreignKey: 'postId' });

const fetchCategoriesMap = async () => {
    try {
        const res = await fetch('http://category-service:3004');
        if (!res.ok) return {};
        const json = await res.json();
        const list = json.data || json || [];
        const map = {};
        list.forEach(c => map[c.id] = c);
        return map;
    } catch (e) { return {}; }
};

const syncToSearch = async (post, catMap) => {
    try {
        const p = post.toJSON ? post.toJSON() : post;
        const category = catMap[p.categoryId] || { name: 'Đang cập nhật' };
        let imageUrl = null;
        if (p.Images && p.Images.length > 0) imageUrl = p.Images[0].imageUrl;

        await fetch('http://search-service:3008/sync', {
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

async function run() {
    try {
        const posts = await Post.findAll({ where: { status: 'approved' }, include: Image });
        const catMap = await fetchCategoriesMap();
        for (let post of posts) {
            await syncToSearch(post, catMap);
        }
        console.log(`Synced ${posts.length} approved posts to search-service`);
        process.exit(0);
    } catch (e) {
        console.error(e);
        process.exit(1);
    }
}

run();
