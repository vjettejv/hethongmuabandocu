import { useState } from 'react';
import api from '../services/api';

function CreatePost() {
    const [formData, setFormData] = useState({ title: '', price: '', description: '', categoryId: '', condition: 'Má»›i' });
    const [images, setImages] = useState([]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        const submitData = new FormData();
        submitData.append('title', formData.title);
        await api.post('/posts', submitData);
    };

    return (
        <div className="container">
            <form onSubmit={handleSubmit}></form>
        </div>
    );
}
export default CreatePost;