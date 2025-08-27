import api from './base';

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
