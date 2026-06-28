// File: src/services/api.js
import axios from 'axios';

const apiBaseUrl = import.meta.env?.VITE_API_URL || '';

const api = axios.create({
    baseURL: apiBaseUrl
});

export const serverOrigin = apiBaseUrl || '';

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default api;