import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Swal from 'sweetalert2';

function CreatePost() {
    const navigate = useNavigate();
    const [categories, setCategories] = useState([]);
    
    // State lưu chữ
    const [formData, setFormData] = useState({ title: '', price: '', description: '', categoryId: '', condition: 'Mới' });
    
    // State lưu ảnh
    const [images, setImages] = useState([]);
    const [imagePreviews, setImagePreviews] = useState([]);

    useEffect(() => {
        // Lấy danh mục để đưa vào thẻ <select>
        api.get('/categories').then(res => setCategories(res.data.data || res.data));
    }, []);

    // Hàm xử lý khi người dùng chọn ảnh
    const handleImageChange = (e) => {
        const files = Array.from(e.target.files);
        
        // Kiểm tra giới hạn 5 ảnh như Backend đã cài đặt
        if (files.length > 5) {
            Swal.fire('CẢNH BÁO', 'Bạn chỉ được tải lên tối đa 5 ảnh!', 'warning');
            return;
        }

        setImages(files);

        // Tạo link URL tạm thời để hiển thị trước ảnh (Preview)
        const previews = files.map(file => URL.createObjectURL(file));
        setImagePreviews(previews);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // NẾU CÓ FILE, BẮT BUỘC PHẢI DÙNG FormData (Không dùng JSON thông thường)
        const submitData = new FormData();
        submitData.append('userId', localStorage.getItem('userId'));
        submitData.append('title', formData.title);
        submitData.append('price', formData.price);
        submitData.append('description', formData.description);
        submitData.append('categoryId', formData.categoryId);
        submitData.append('condition', formData.condition);

        // Nạp từng ảnh vào FormData với key là 'images' (Khớp với upload.array('images') ở Backend)
        images.forEach((image) => {
            submitData.append('images', image);
        });

        try {
            // Khi gửi FormData, Axios sẽ tự động set Headers là 'multipart/form-data'
            await api.post('/posts', submitData);
            Swal.fire('THÀNH CÔNG', 'Bài đăng của bạn đã được gửi và đang chờ duyệt!', 'success').then(() => navigate('/'));
        } catch (err) {
            console.error("Lỗi đăng bài:", err);
            Swal.fire('LỖI', 'Không thể đăng bài. Vui lòng điền đủ thông tin và chọn ảnh hợp lệ.', 'error');
        }
    };

    return (
        <div className="container">
            <div className="card card-pad" style={{ maxWidth: 760, margin: '0 auto' }}>
                <div className="toolbar">
                    <div className="toolbar-grow">
                        <h2 className="toolbar-title" style={{ margin: 0 }}>Đăng tin</h2>
                        <div className="hint">Điền thông tin rõ ràng và ảnh thật để tăng tỷ lệ bán.</div>
                    </div>
                    <button className="btn btn-ghost" type="button" onClick={() => navigate(-1)}>
                        Quay lại
                    </button>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 10 }}>
                    <div className="field">
                        <div className="label">Tiêu đề</div>
                        <input
                            className="input"
                            type="text"
                            placeholder="VD: Cần bán iPhone 12 64GB, còn bảo hành..."
                            required
                            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                        />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 12 }}>
                        <div className="field">
                            <div className="label">Danh mục</div>
                            <select
                                className="select"
                                required
                                onChange={(e) => setFormData({ ...formData, categoryId: e.target.value })}
                                defaultValue=""
                            >
                                <option value="" disabled>
                                    Chọn danh mục
                                </option>
                                {categories.map((c) => (
                                    <option key={c.id} value={c.id}>
                                        {c.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="field">
                            <div className="label">Tình trạng</div>
                            <select className="select" onChange={(e) => setFormData({ ...formData, condition: e.target.value })} defaultValue="Mới">
                                <option value="Mới">Đồ mới</option>
                                <option value="Đã sử dụng">Đồ cũ (đã sử dụng)</option>
                            </select>
                        </div>
                    </div>

                    <div className="field">
                        <div className="label">Giá (VNĐ)</div>
                        <input
                            className="input"
                            type="number"
                            placeholder="VD: 1500000"
                            required
                            onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                        />
                        <div className="hint">Bạn có thể để giá hợp lý để bán nhanh.</div>
                    </div>

                    <div className="field">
                        <div className="label">Mô tả</div>
                        <textarea
                            className="textarea"
                            placeholder="Mô tả chi tiết: tình trạng, phụ kiện đi kèm, lý do bán..."
                            required
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        />
                    </div>

                    <div className="card card-pad" style={{ background: 'rgba(238,77,45,0.05)', borderColor: 'rgba(238,77,45,0.18)' }}>
                        <div className="label">Hình ảnh (tối đa 5 ảnh)</div>
                        <div className="hint" style={{ marginTop: 4 }}>Ảnh rõ nét giúp tăng tỷ lệ được duyệt và chốt đơn.</div>
                        <input type="file" multiple accept="image/*" onChange={handleImageChange} style={{ marginTop: 10 }} />

                        {imagePreviews.length > 0 && (
                            <div style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap' }}>
                                {imagePreviews.map((url, index) => (
                                    <img
                                        key={index}
                                        src={url}
                                        alt={`Preview ${index}`}
                                        style={{ width: 88, height: 88, objectFit: 'cover', borderRadius: 12, border: '1px solid rgba(15,23,42,0.12)' }}
                                    />
                                ))}
                            </div>
                        )}
                    </div>

                    <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 6 }}>
                        <button className="btn btn-ghost" type="button" onClick={() => navigate(-1)}>
                            Hủy
                        </button>
                        <button className="btn btn-primary" type="submit">
                            Gửi đăng tin
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default CreatePost;