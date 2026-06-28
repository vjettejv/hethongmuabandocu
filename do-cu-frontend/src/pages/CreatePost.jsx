import { useState } from 'react';

function CreatePost() {
    const [formData, setFormData] = useState({ title: '', price: '', description: '', categoryId: '', condition: 'Má»›i' });
    return (
        <div className="container">
            <h2>ÄÄƒng tin</h2>
            <form style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <input type="text" placeholder="TiÃªu Ä‘á»" onChange={e => setFormData({...formData, title: e.target.value})} />
            </form>
        </div>
    );
}
export default CreatePost;