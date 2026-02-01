
import axios from 'axios';

// Detect if we are running locally or on VPS (same host)
// If frontend is served by Nginx on port 80/3000 and backend on 8000
const API_URL = import.meta.env.PROD
    ? '/api' // Nginx proxy behavior
    : 'http://localhost:8000'; // Local dev

console.log('API_URL configured as:', API_URL);

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 second timeout
});

// Interceptor to add Token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('vong_token');
    if (token) {
        config.headers['x-token'] = token;
    }
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
});

// Response interceptor for better error handling
api.interceptors.response.use(
    (response) => {
        console.log('API Response:', response.config.url, response.status);
        return response;
    },
    (error) => {
        console.error('API Error:', error.config?.url, error.message);
        if (error.response) {
            console.error('Response data:', error.response.data);
            console.error('Response status:', error.response.status);
        } else if (error.request) {
            console.error('No response received:', error.request);
        }
        return Promise.reject(error);
    }
);

export const UserAPI = {
    login: async (googleToken: string) => {
        console.log('Calling login API with token length:', googleToken?.length);
        try {
            const res = await api.post('/auth/login', { token: googleToken });
            console.log('Login successful:', res.data);
            return res.data;
        } catch (error: any) {
            console.error('Login API failed:', error);
            throw error;
        }
    },
    getStats: async () => (await api.get('/stats')).data,
    getQueue: async () => (await api.get('/queue')).data,
    getHistory: async () => (await api.get('/history')).data,
    getOptions: async () => (await api.get('/options')).data,
    getLogs: async () => (await api.get('/logs')).data,
    getErrors: async () => (await api.get('/errors')).data,
    approve: async (id: string, data: { team: string, playlist: string }) =>
        (await api.post(`/approve/${id}`, data)).data,
    sync: async () => (await api.post('/sync')).data,
    getSheetsUrl: async () => (await api.get('/sheets-url')).data,

    // Service Management
    getServiceHealth: async () => (await api.get('/service/health')).data,
    startService: async () => (await api.post('/service/start')).data,
    stopService: async () => (await api.post('/service/stop')).data,
    restartService: async () => (await api.post('/service/restart')).data,
};
