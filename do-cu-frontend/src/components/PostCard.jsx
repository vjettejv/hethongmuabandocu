import { Link } from 'react-router-dom';
import { serverOrigin } from '../services/api';
import { formatPrice, imageSource } from '../services/contracts';

export default function PostCard({ post, children }) {
    const image = imageSource(post.Images?.[0]?.imageUrl, serverOrigin);
    return <article className="product">
        <Link to={`/post/${post.id}`}>
            {image ? <img className="product-img" src={image} alt={post.title} loading="lazy" /> : <div className="product-img product-placeholder">Chưa có ảnh</div>}
            <div className="product-body">
                <h2 className="product-title">{post.title}</h2>
                <div className="product-price">{formatPrice(post.price)}</div>
                <span className="hint">{post.Category?.name}</span>
            </div>
        </Link>
        {children && <div className="product-body">{children}</div>}
    </article>;
}
