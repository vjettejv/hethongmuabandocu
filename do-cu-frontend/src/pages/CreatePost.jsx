import { useState } from 'react';

function CreatePost() {
    const [formData, setFormData] = useState({ title: '', price: '', description: '', categoryId: '', condition: 'Má»›i' });
    const [images, setImages] = useState([]);
    const [imagePreviews, setImagePreviews] = useState([]);

    const handleImageChange = (e) => {
        const files = Array.from(e.target.files);
        setImages(files);
        const previews = files.map(file => URL.createObjectURL(file));
        setImagePreviews(previews);
    };

    return (
        <div className="container">
            <h2>ÄÄƒng tin</h2>
            <input type="file" multiple accept="image/*" onChange={handleImageChange} />
        </div>
    );
}
export default CreatePost;