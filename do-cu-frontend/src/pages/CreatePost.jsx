import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { errorMessage, listData } from '../services/contracts';
import Page, { ErrorNotice } from '../components/Page';

export default function CreatePost() {
    const [form, setForm] = useState({ title: '', price: '', description: '', categoryId: '', condition: 'Đã sử dụng' });
    const [images, setImages] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [retry, setRetry] = useState(0);
    const navigate = useNavigate();
    useEffect(() => {
        const controller = new AbortController();
        setLoading(true); setError('');
        api.get('/categories', { signal: controller.signal }).then(response => {
            if (!controller.signal.aborted) setCategories(listData(response));
        }).catch(failure => { if (!controller.signal.aborted) setError(errorMessage(failure)); })
            .finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [retry]);
    const submit = async event => {
        event.preventDefault();
        if (busy) return;
        setError('');
        if (images.length > 5) { setError('Chọn tối đa 5 ảnh.'); return; }
        if (!form.title.trim() || !form.categoryId || !Number.isFinite(Number(form.price))) { setError('Vui lòng nhập đầy đủ thông tin hợp lệ.'); return; }
        setBusy(true);
        const data = new FormData();
        Object.entries({ ...form, title: form.title.trim() }).forEach(([key, value]) => data.append(key, value));
        images.forEach(image => data.append('images', image));
        try { await api.post('/posts', data); navigate('/my-posts', { replace: true }); }
        catch (failure) { setError(errorMessage(failure, 'Không thể đăng tin.')); }
        finally { setBusy(false); }
    };
    return <Page title="Đăng tin"><section className="card card-pad form-card">
        <ErrorNotice error={error} />
        {loading ? <p role="status">Đang tải danh mục…</p> : categories.length === 0 ?
            <button className="btn btn-ghost" onClick={() => setRetry(value => value + 1)}>Tải lại danh mục</button> :
            <form className="form-stack" onSubmit={submit}>
                <label className="field"><span className="label">Tiêu đề</span><input className="input" required maxLength={255} value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} /></label>
                <label className="field"><span className="label">Giá (VND)</span><input className="input" required type="number" min="0" step="0.01" value={form.price} onChange={event => setForm({ ...form, price: event.target.value })} /></label>
                <label className="field"><span className="label">Danh mục</span><select className="select" required value={form.categoryId} onChange={event => setForm({ ...form, categoryId: event.target.value })}>
                    <option value="">Chọn danh mục</option>{categories.map(category => <option key={category.id} value={category.id}>{category.name}</option>)}
                </select></label>
                <label className="field"><span className="label">Tình trạng</span><select className="select" value={form.condition} onChange={event => setForm({ ...form, condition: event.target.value })}>
                    <option>Đã sử dụng</option><option>Mới</option>
                </select></label>
                <label className="field"><span className="label">Mô tả</span><textarea className="textarea" value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} /></label>
                <label className="field"><span className="label">Ảnh sản phẩm (tối đa 5)</span><input type="file" accept="image/*" multiple onChange={event => setImages(Array.from(event.target.files || []))} /></label>
                <p className="hint">Tin sẽ hiển thị công khai sau khi được duyệt.</p>
                <button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Đang đăng tin…' : 'Đăng tin'}</button>
            </form>}
    </section></Page>;
}
