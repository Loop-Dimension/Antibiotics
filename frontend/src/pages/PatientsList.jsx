import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientsAPI } from '../api';
import { useAuth } from '../contexts/AuthContext';

const PatientsList = () => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [sortType, setSortType] = useState('-date_recorded');
  const [statistics, setStatistics] = useState(null);
  const [filterOptions, setFilterOptions] = useState(null);
  const { user, logout } = useAuth();
  const searchTimeoutRef = useRef(null);

  useEffect(() => {
    fetchPatients(currentPage);
    fetchStatistics();
    fetchFilterOptions();
  }, [currentPage, filterType, sortType]);

  const fetchPatients = async (page = 1) => {
    setLoading(true);
    setError(null);
    try {
      // Build filter options
      const filterOptions = {
        page,
        pageSize: 12,
        ordering: sortType
      };

      // Apply backend filtering
      if (filterType === 'high-risk') {
        filterOptions.riskLevel = 'high';
      } else if (filterType === 'culture-positive') {
        filterOptions.cultureStatus = 'positive';
      } else if (filterType === 'on-treatment') {
        filterOptions.treatmentStatus = 'on_treatment';
      }

      const response = await patientsAPI.getPatients(filterOptions);
      
      setPatients(response.data.results);
      setTotalCount(response.data.count);
      setTotalPages(response.data.total_pages);
      
      // Update statistics if provided
      if (response.data.stats) {
        setStatistics(response.data.stats);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching patients:', error);
      setError('Error loading patient data');
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await patientsAPI.getStatistics();
      setStatistics(response.data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const fetchFilterOptions = async () => {
    try {
      const response = await patientsAPI.getFilterOptions();
      setFilterOptions(response.data);
    } catch (error) {
      console.error('Error fetching filter options:', error);
    }
  };

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (value.trim().length >= 2) {
      searchTimeoutRef.current = setTimeout(() => {
        performSearch(value.trim());
      }, 300);
    } else {
      setSearchResults([]);
      setShowSearchResults(false);
    }
  };

  const performSearch = async (query) => {
    try {
      const response = await patientsAPI.searchPatients(query, 10);
      setSearchResults(response.data.results || response.data);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Error searching patients:', error);
      setSearchResults([]);
      setShowSearchResults(false);
    }
  };

  const selectPatient = (patient) => {
    setSearchTerm('');
    setSearchResults([]);
    setShowSearchResults(false);
    navigate(`/patient/${patient.patient_id}`);
  };

  const handleSearchBlur = () => {
    setTimeout(() => {
      setShowSearchResults(false);
    }, 200);
  };

  const handleSearchFocus = () => {
    if (searchResults.length > 0 && searchTerm.length >= 2) {
      setShowSearchResults(true);
    }
  };

  const viewPatient = (patientId) => {
    navigate(`/patient/${patientId}`);
  };

  const handleLogout = async () => {
    await logout();
  };

  const handleAddPatient = () => {
    navigate('/add-patient');
  };

  const goToPage = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const getStatusColor = (diagnosis) => {
    if (!diagnosis) return 'bg-gray-100 text-gray-800';
    
    const lowerDiagnosis = diagnosis.toLowerCase();
    if (lowerDiagnosis.includes('pneumonia')) return 'bg-red-100 text-red-800';
    if (lowerDiagnosis.includes('uti') || lowerDiagnosis.includes('urinary')) return 'bg-yellow-100 text-yellow-800';
    if (lowerDiagnosis.includes('sepsis')) return 'bg-red-200 text-red-900';
    if (lowerDiagnosis.includes('infection')) return 'bg-orange-100 text-orange-800';
    return 'bg-blue-100 text-blue-800';
  };

  const getRiskLevel = (patient) => {
    let riskScore = 0;
    
    // Age factor
    if (patient.age > 80) riskScore += 3;
    else if (patient.age > 65) riskScore += 2;
    else if (patient.age > 50) riskScore += 1;
    
    // Lab values
    if (patient.crp && parseFloat(patient.crp) > 100) riskScore += 2;
    if (patient.wbc && parseFloat(patient.wbc) > 15000) riskScore += 1;
    if (patient.cockcroft_gault_crcl && parseFloat(patient.cockcroft_gault_crcl) < 30) riskScore += 2;
    
    // Temperature
    if (patient.body_temperature && parseFloat(patient.body_temperature) > 38.5) riskScore += 1;
    
    if (riskScore >= 6) return { level: 'High', color: 'bg-red-500', textColor: 'text-white' };
    if (riskScore >= 3) return { level: 'Medium', color: 'bg-yellow-500', textColor: 'text-white' };
    return { level: 'Low', color: 'bg-green-500', textColor: 'text-white' };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading patients...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg border border-red-300 p-8 max-w-md w-full text-center">
          <div className="text-red-600 text-xl font-bold mb-4">Error</div>
          <div className="text-gray-700 mb-6">{error}</div>
          <button 
            onClick={() => fetchPatients(1)}
            className="bg-blue-600 text-white px-6 py-2 rounded-md font-medium hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Enhanced Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 
              onClick={() => navigate('/')}
              className="text-2xl font-bold text-gray-900 cursor-pointer hover:text-blue-600"
            >
              ImpactUs Antibiotic Advisor
            </h1>
            <span className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-medium">
              {totalCount} Patients
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">
              Welcome, {user?.first_name} {user?.last_name} ({user?.username})
            </span>
            <div className="relative">
              <input
                type="text"
                placeholder="Search patient by name..."
                value={searchTerm}
                onChange={handleSearchChange}
                onFocus={handleSearchFocus}
                onBlur={handleSearchBlur}
                className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
              />
              
              {/* Search Results Dropdown */}
              {showSearchResults && searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-50 max-h-64 overflow-y-auto">
                  {searchResults.map((patient, index) => (
                    <div
                      key={patient.patient_id || index}
                      onClick={() => selectPatient(patient)}
                      className="px-4 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
                    >
                      <div className="font-medium text-gray-900">
                        {patient.name}, {patient.age} {patient.gender === 'Male' || patient.gender === 'M' ? '♂' : '♀'}
                      </div>
                      <div className="text-sm text-gray-600">
                        ID: {patient.patient_id} | {patient.diagnosis1 || 'No diagnosis'} | CrCl: {Math.round(patient.cockcroft_gault_crcl || 0)} mL/min
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* No results message */}
              {showSearchResults && searchResults.length === 0 && searchTerm.length >= 2 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-50 px-4 py-2 text-gray-500">
                  No patients found matching "{searchTerm}"
                </div>
              )}
            </div>
            <div className="flex items-center space-x-2">
             
              <button 
                onClick={handleAddPatient}
                className="bg-emerald-600 text-white px-4 py-2 rounded-md font-medium hover:bg-emerald-700"
              >
                Add Patient
              </button>
              <button 
                onClick={handleLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-md font-medium hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Breadcrumb Navigation */}
      <div className="bg-gray-100 border-b border-gray-200 px-6 py-3">
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <button 
            onClick={() => navigate('/')}
            className="hover:text-blue-600"
          >
            Dashboard
          </button>
          <span>›</span>
          <span className="text-gray-900 font-medium">All Patients</span>
        </div>
      </div>

      {/* Summary Stats Bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {statistics?.total_patients || totalCount}
            </div>
            <div className="text-sm text-gray-600">Total Patients</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {statistics?.risk_levels?.high || '--'}
            </div>
            <div className="text-sm text-gray-600">High Risk</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {statistics?.culture_status?.positive || '--'}
            </div>
            <div className="text-sm text-gray-600">Culture Positive</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {statistics?.treatment_status?.on_treatment || '--'}
            </div>
            <div className="text-sm text-gray-600">On Treatment</div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        {/* Filters and Controls */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-semibold text-gray-900">Patient Overview</h2>
            <select 
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Patients</option>
              <option value="high-risk">High Risk Only</option>
              <option value="culture-positive">Culture Positive</option>
              <option value="on-treatment">On Treatment</option>
            </select>
            <select 
              value={sortType}
              onChange={(e) => setSortType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="-date_recorded">Most Recent</option>
              <option value="date_recorded">Oldest First</option>
              <option value="name">By Name A-Z</option>
              <option value="-name">By Name Z-A</option>
              <option value="-age">By Age (Oldest First)</option>
              <option value="age">By Age (Youngest First)</option>
              <option value="-body_temperature">By Temperature (High to Low)</option>
              <option value="-crp">By CRP (High to Low)</option>
              <option value="-wbc">By WBC (High to Low)</option>
              <option value="cockcroft_gault_crcl">By CrCl (Low to High)</option>
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => fetchPatients(currentPage)}
              className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm font-medium"
            >
              ↻ Refresh
            </button>
            {filterType !== 'all' && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-xs font-medium">
                {filterType === 'high-risk' ? 'High Risk' : 
                 filterType === 'culture-positive' ? 'Culture +' : 
                 'On Treatment'} Filter
              </span>
            )}
            <span className="text-sm text-gray-600">
              Page {currentPage} of {totalPages} • Showing {totalCount} patients
            </span>
          </div>
        </div>

        {/* Enhanced Patients Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
          {patients.map((patient) => {
            const risk = getRiskLevel(patient);
            return (
              <div 
                key={patient.patient_id}
                className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer group h-[450px] flex flex-col"
                onClick={() => viewPatient(patient.patient_id)}
              >
                {/* Enhanced Patient Card Header */}
                <div className="p-4 border-b border-gray-100">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                        {patient.name || 'Unknown'}
                      </h3>
                      <p className="text-sm text-gray-600">
                        ID: {patient.patient_id} | {patient.age} years | {patient.gender === 'Male' || patient.gender === 'M' ? '♂' : '♀'}
                      </p>
                      {patient.date_recorded && (
                        <p className="text-xs text-gray-500 mt-1">
                          Recorded: {new Date(patient.date_recorded).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <div className="flex flex-col items-end space-y-1">
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${risk.color} ${risk.textColor}`}>
                        {risk.level}
                      </div>
                      {patient.pathogen && patient.pathogen !== 'None' && (
                        <div className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Culture +
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Primary Diagnosis */}
                  {patient.diagnosis1 && (
                    <div className="flex items-center space-x-2">
                      <span className={`inline-block px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(patient.diagnosis1)}`}>
                        {patient.diagnosis1}
                      </span>
                      {patient.diagnosis2 && patient.diagnosis2 !== patient.diagnosis1 && (
                        <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full">
                          +{patient.diagnosis2}
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Enhanced Patient Card Body */}
                <div className="p-4 space-y-3 flex-1">
                  

                  {/* Clinical Information */}
                  <div className="space-y-2">
                    {/* Pathogen & Sample */}
                    {patient.pathogen && patient.pathogen !== 'None' && (
                      <div className="bg-red-50 border border-red-200 rounded-md p-2">
                        <div className="text-xs font-medium text-red-800 mb-1">CULTURE RESULTS</div>
                        <div className="text-sm font-medium text-red-900">{patient.pathogen}</div>
                        {patient.sample_type && (
                          <div className="text-xs text-red-700">Sample: {patient.sample_type}</div>
                        )}
                      </div>
                    )}
                    
                    {/* Current Treatment */}
                    {patient.antibiotics && patient.antibiotics !== 'None' && (
                      <div className="bg-blue-50 border border-blue-200 rounded-md p-2">
                        <div className="text-xs font-medium text-blue-800 mb-1">CURRENT TREATMENT</div>
                        <div className="text-sm font-medium text-blue-900 break-words">{patient.antibiotics}</div>
                      </div>
                    )}

                    {/* Allergies Warning */}
                    {patient.allergies && patient.allergies !== 'None' && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-2">
                        <div className="text-xs font-medium text-yellow-800 mb-1">⚠️ ALLERGIES</div>
                        <div className="text-sm font-medium text-yellow-900">{patient.allergies}</div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Enhanced Card Footer */}
                <div className="px-4 py-3 bg-gray-50 rounded-b-lg mt-auto border-t border-gray-100">
                  <div className="flex space-x-2">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        viewPatient(patient.patient_id);
                      }}
                      className="flex-1 text-sm bg-blue-600 text-white py-2 px-3 rounded-md font-medium hover:bg-blue-700 transition-colors"
                    >
                      View Details
                    </button>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/edit-patient/${patient.patient_id}`);
                      }}
                      className="flex-1 text-sm bg-green-600 text-white py-2 px-3 rounded-md font-medium hover:bg-green-700 transition-colors"
                    >
                      Edit
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Enhanced Pagination */}
        <div className="bg-white px-6 py-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm text-gray-700">
              Showing <span className="font-medium">{((currentPage - 1) * 12) + 1}</span> to <span className="font-medium">{Math.min(currentPage * 12, totalCount)}</span> of <span className="font-medium">{totalCount}</span> patients
            </div>
            <div className="text-sm text-gray-500">
              {totalPages > 1 ? `Page ${currentPage} of ${totalPages}` : '1 page'}
            </div>
          </div>
          
          <div className="flex items-center justify-center space-x-2">
            <button
              onClick={() => goToPage(1)}
              disabled={currentPage === 1}
              className="px-4 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              ‹‹ First
            </button>
            
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-4 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              ‹ Previous
            </button>

            {/* Page Numbers */}
            <div className="flex space-x-1">
              {[...Array(Math.min(5, totalPages))].map((_, index) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = index + 1;
                } else if (currentPage <= 3) {
                  pageNum = index + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + index;
                } else {
                  pageNum = currentPage - 2 + index;
                }

                if (pageNum > 0 && pageNum <= totalPages) {
                  return (
                    <button
                      key={pageNum}
                      onClick={() => goToPage(pageNum)}
                      className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        currentPage === pageNum
                          ? 'bg-blue-600 text-white border border-blue-600 shadow-sm'
                          : 'text-gray-700 bg-white border border-gray-300 hover:bg-blue-50 hover:border-blue-300'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                }
                return null;
              })}
            </div>

            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-4 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next ›
            </button>
            
            <button
              onClick={() => goToPage(totalPages)}
              disabled={currentPage === totalPages}
              className="px-4 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Last ››
            </button>
          </div>

          {/* Quick Page Jump */}
          {totalPages > 10 && (
            <div className="flex items-center justify-center mt-4 space-x-2">
              <span className="text-sm text-gray-600">Jump to page:</span>
              <input
                type="number"
                min="1"
                max={totalPages}
                value={currentPage}
                onChange={(e) => {
                  const page = parseInt(e.target.value);
                  if (page >= 1 && page <= totalPages) {
                    goToPage(page);
                  }
                }}
                className="w-16 px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-600">of {totalPages}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PatientsList;
