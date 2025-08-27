import api from './base';

// Helper function to build query parameters
const buildQueryParams = (params) => {
  const searchParams = new URLSearchParams();
  
  Object.keys(params).forEach(key => {
    const value = params[key];
    if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, value);
    }
  });
  
  return searchParams.toString();
};

// Patients API calls
export const patientsAPI = {
  // Enhanced getPatients with comprehensive filtering
  getPatients: (options = {}) => {
    const {
      page = 1,
      pageSize = 12,
      search = '',
      riskLevel = '',
      cultureStatus = '',
      treatmentStatus = '',
      diagnosis = '',
      pathogen = '',
      antibiotic = '',
      allergy = '',
      gender = '',
      ageMin = '',
      ageMax = '',
      dateFrom = '',
      dateTo = '',
      tempMin = '',
      tempMax = '',
      crpMin = '',
      crpMax = '',
      wbcMin = '',
      wbcMax = '',
      crclMin = '',
      crclMax = '',
      ordering = '-date_recorded'
    } = options;

    const params = {
      page,
      page_size: pageSize,
      search,
      risk_level: riskLevel,
      culture_status: cultureStatus,
      treatment_status: treatmentStatus,
      diagnosis,
      pathogen,
      antibiotic,
      allergy,
      gender,
      age_min: ageMin,
      age_max: ageMax,
      date_from: dateFrom,
      date_to: dateTo,
      temp_min: tempMin,
      temp_max: tempMax,
      crp_min: crpMin,
      crp_max: crpMax,
      wbc_min: wbcMin,
      wbc_max: wbcMax,
      crcl_min: crclMin,
      crcl_max: crclMax,
      ordering
    };

    const queryString = buildQueryParams(params);
    return api.get(`/api/patients/?${queryString}`);
  },

  // Legacy method for backward compatibility
  getPatientsLegacy: (page = 1, pageSize = 12) => api.get(`/api/patients/?page=${page}&page_size=${pageSize}`),
  
  getPatient: (id) => api.get(`/api/patients/${id}/`),
  getAntibioticRecommendations: (id) => api.get(`/api/patients/${id}/antibiotic_recommendations/`),
  
  // Enhanced search with additional options
  searchPatients: (query, limit = 10) => {
    const params = buildQueryParams({ q: query, limit });
    return api.get(`/api/patients/search/?${params}`);
  },
  
  // Get filter options for dropdowns
  getFilterOptions: () => api.get('/api/patients/filter_options/'),
  
  // Get comprehensive statistics
  getStatistics: () => api.get('/api/patients/statistics/'),
  
  // Quick filters
  getHighRiskPatients: (page = 1, pageSize = 12) => {
    const params = buildQueryParams({ 
      page, 
      page_size: pageSize, 
      risk_level: 'high',
      ordering: '-date_recorded'
    });
    return api.get(`/api/patients/?${params}`);
  },
  
  getCulturePositivePatients: (page = 1, pageSize = 12) => {
    const params = buildQueryParams({ 
      page, 
      page_size: pageSize, 
      culture_status: 'positive',
      ordering: '-date_recorded'
    });
    return api.get(`/api/patients/?${params}`);
  },
  
  getOnTreatmentPatients: (page = 1, pageSize = 12) => {
    const params = buildQueryParams({ 
      page, 
      page_size: pageSize, 
      treatment_status: 'on_treatment',
      ordering: '-date_recorded'
    });
    return api.get(`/api/patients/?${params}`);
  },
  
  // Patient management
  createPatient: (patientData) => api.post('/api/patients/', patientData),
  updatePatient: (id, patientData) => api.put(`/api/patients/${id}/`, patientData),
  deletePatient: (id) => api.delete(`/api/patients/${id}/`),
  
  // Advanced filtering methods
  filterByDiagnosis: (diagnosis, page = 1, pageSize = 12) => {
    const params = buildQueryParams({ 
      page, 
      page_size: pageSize, 
      diagnosis,
      ordering: '-date_recorded'
    });
    return api.get(`/api/patients/?${params}`);
  },
  
  filterByPathogen: (pathogen, page = 1, pageSize = 12) => {
    const params = buildQueryParams({ 
      page, 
      page_size: pageSize, 
      pathogen,
      ordering: '-date_recorded'
    });
    return api.get(`/api/patients/?${params}`);
  },
  
  filterByAntibiotic: (antibiotic, page = 1, pageSize = 12) => {
    const params = buildQueryParams({ 
      page, 
      page_size: pageSize, 
      antibiotic,
      ordering: '-date_recorded'
    });
    return api.get(`/api/patients/?${params}`);
  },
  
  filterByAgeRange: (ageMin, ageMax, page = 1, pageSize = 12) => {
    const params = buildQueryParams({ 
      page, 
      page_size: pageSize, 
      age_min: ageMin,
      age_max: ageMax,
      ordering: '-age'
    });
    return api.get(`/api/patients/?${params}`);
  },
  
  filterByDateRange: (dateFrom, dateTo, page = 1, pageSize = 12) => {
    const params = buildQueryParams({ 
      page, 
      page_size: pageSize, 
      date_from: dateFrom,
      date_to: dateTo,
      ordering: '-date_recorded'
    });
    return api.get(`/api/patients/?${params}`);
  },
  
  filterByLabValues: (labFilters, page = 1, pageSize = 12) => {
    const params = {
      page,
      page_size: pageSize,
      ordering: '-date_recorded',
      ...labFilters
    };
    const queryString = buildQueryParams(params);
    return api.get(`/api/patients/?${queryString}`);
  }
};
