import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if it exists
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Don't redirect for EMR endpoints or if already on login/home page
      const isEMREndpoint = error.config.url.includes('/api/emr/');
      const isOnAuthPage = ['/login', '/', '/register'].includes(window.location.pathname);
      
      if (!isEMREndpoint && !isOnAuthPage) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Authentication API calls
export const authAPI = {
  login: (credentials) => api.post('/api/auth/login/', credentials),
  register: (userData) => api.post('/api/auth/register/', userData),
  logout: () => api.post('/api/auth/logout/'),
  getProfile: () => api.get('/api/auth/profile/'),
};

// Patients API calls
export const patientsAPI = {
  getPatients: (page = 1, pageSize = 12) => api.get(`/api/patients/?page=${page}&page_size=${pageSize}`),
  getPatient: (id) => api.get(`/api/patients/${id}/`),
  getAntibioticRecommendations: (id) => api.get(`/api/patients/${id}/antibiotic_recommendations/`),
  searchPatients: (query) => api.get(`/api/patients/search/?q=${encodeURIComponent(query)}`),
  createPatient: (patientData) => api.post('/api/patients/', patientData),
  updatePatient: (id, patientData) => api.put(`/api/patients/${id}/`, patientData),
  deletePatient: (id) => api.delete(`/api/patients/${id}/`),
};

// EMR API calls
export const emrAPI = {
  authenticate: (credentials) => api.post('/api/emr/authenticate/', credentials),
  getSessionStatus: () => api.get('/api/emr/session_status/'),
  logout: () => api.post('/api/emr/logout/'),
  openPatientRecord: (patientId) => api.post('/api/emr/open_patient_record/', { patient_id: patientId }),
  
  // EMR Orders
  getOrders: () => api.get('/api/emr-orders/'),
  createOrder: (orderData) => api.post('/api/emr-orders/', orderData),
  sendOrderToEMR: (orderId) => api.post(`/api/emr-orders/${orderId}/send_to_emr/`),
  createMedicationOrder: (orderData) => api.post('/api/emr-orders/create_medication_order/', orderData),
  
  // EMR Systems
  getEMRSystems: () => api.get('/api/emr-systems/'),
};

// Auth helper functions
export const auth = {
  getToken: () => localStorage.getItem('authToken'),
  setToken: (token) => localStorage.setItem('authToken', token),
  removeToken: () => localStorage.removeItem('authToken'),
  getUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },
  setUser: (user) => localStorage.setItem('user', JSON.stringify(user)),
  removeUser: () => localStorage.removeItem('user'),
  isAuthenticated: () => !!localStorage.getItem('authToken'),
  logout: () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
  }
};

export default api;
