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
  const { user, logout } = useAuth();
  const searchTimeoutRef = useRef(null);

  useEffect(() => {
    fetchPatients(currentPage);
  }, [currentPage]);

  const fetchPatients = async (page = 1) => {
    setLoading(true);
    setError(null);
    try {
      const response = await patientsAPI.getPatients(page, 12);
      setPatients(response.data.results);
      setTotalCount(response.data.count);
      setTotalPages(Math.ceil(response.data.count / 12));
      setLoading(false);
    } catch (error) {
      console.error('Error fetching patients:', error);
      setError('Error loading patient data');
      setLoading(false);
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
      const response = await patientsAPI.searchPatients(query);
      setSearchResults(response.data);
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
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-900">
              ImpactUs Antibiotic Advisor
            </h1>
            <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-md">
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
            <button 
              onClick={handleAddPatient}
              className="bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700"
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
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        {/* Patients Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
          {patients.map((patient) => {
            const risk = getRiskLevel(patient);
            return (
              <div 
                key={patient.patient_id}
                className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer h-[420px] flex flex-col"
                onClick={() => viewPatient(patient.patient_id)}
              >
                {/* Patient Card Header */}
                <div className="p-4 border-b border-gray-100">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {patient.name || 'Unknown'}
                      </h3>
                      <p className="text-sm text-gray-600">
                        ID: {patient.patient_id} | {patient.age} years | {patient.gender === 'Male' || patient.gender === 'M' ? '♂' : '♀'}
                      </p>
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${risk.color} ${risk.textColor}`}>
                      {risk.level}
                    </div>
                  </div>
                  
                  {/* Diagnosis */}
                  {patient.diagnosis1 && (
                    <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(patient.diagnosis1)}`}>
                      {patient.diagnosis1}
                    </span>
                  )}
                </div>

                {/* Patient Card Body - Flexible to fill available space */}
                <div className="p-4 space-y-3 flex-1">
                  {/* Vitals Row */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Temp:</span>
                      <span className={`ml-1 font-medium ${patient.body_temperature && parseFloat(patient.body_temperature) > 38.5 ? 'text-red-600' : 'text-gray-900'}`}>
                        {patient.body_temperature ? `${patient.body_temperature}°C` : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">WBC:</span>
                      <span className={`ml-1 font-medium ${patient.wbc && parseFloat(patient.wbc) > 12000 ? 'text-red-600' : 'text-gray-900'}`}>
                        {patient.wbc ? `${(parseFloat(patient.wbc) / 1000).toFixed(1)}k` : 'N/A'}
                      </span>
                    </div>
                  </div>

                  {/* Lab Values Row */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">CRP:</span>
                      <span className={`ml-1 font-medium ${patient.crp && parseFloat(patient.crp) > 50 ? 'text-red-600' : 'text-gray-900'}`}>
                        {patient.crp ? `${parseFloat(patient.crp).toFixed(1)}` : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">CrCl:</span>
                      <span className={`ml-1 font-medium ${patient.cockcroft_gault_crcl && parseFloat(patient.cockcroft_gault_crcl) < 50 ? 'text-yellow-600' : 'text-gray-900'}`}>
                        {patient.cockcroft_gault_crcl ? `${Math.round(patient.cockcroft_gault_crcl)}` : 'N/A'}
                      </span>
                    </div>
                  </div>

                  {/* Pathogen & Current Treatment */}
                  {patient.pathogen && (
                    <div className="text-sm">
                      <span className="text-gray-500">Pathogen:</span>
                      <span className="ml-1 font-medium text-gray-900 break-words">{patient.pathogen}</span>
                    </div>
                  )}
                  
                  {patient.antibiotics && patient.antibiotics !== 'None' && (
                    <div className="text-sm">
                      <span className="text-gray-500">Current Abx:</span>
                      <span className="ml-1 font-medium text-blue-600 break-words">{patient.antibiotics}</span>
                    </div>
                  )}

                  {/* Allergies Warning */}
                  {patient.allergies && patient.allergies !== 'None' && (
                    <div className="flex items-center text-xs bg-yellow-50 text-yellow-800 px-2 py-1 rounded">
                      ⚠️ Allergic to: {patient.allergies}
                    </div>
                  )}
                  
                  {/* Date Recorded */}
                  {patient.date_recorded && (
                    <div className="text-xs text-gray-500 border-t border-gray-100 pt-2 mt-auto">
                      Recorded: {new Date(patient.date_recorded).toLocaleDateString()}
                    </div>
                  )}
                </div>

                {/* Card Footer - Always at bottom */}
                <div className="px-4 py-3 bg-gray-50 rounded-b-lg mt-auto">
                  <div className="space-y-2">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        viewPatient(patient.patient_id);
                      }}
                      className="w-full text-sm bg-blue-600 text-white py-2 px-4 rounded-md font-medium hover:bg-blue-700 transition-colors"
                    >
                      View Details
                    </button>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/edit-patient/${patient.patient_id}`);
                      }}
                      className="w-full text-sm bg-green-600 text-white py-2 px-4 rounded-md font-medium hover:bg-green-700 transition-colors"
                    >
                      Edit Patient
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Pagination */}
        <div className="bg-white px-6 py-4 rounded-lg border border-gray-200">
          <div className="text-sm text-gray-700 text-center mb-4">
            Showing {((currentPage - 1) * 12) + 1} to {Math.min(currentPage * 12, totalCount)} of {totalCount} patients
          </div>
          
          <div className="flex items-center justify-center space-x-2">
            <button
              onClick={() => goToPage(1)}
              disabled={currentPage === 1}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              First
            </button>
            
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              Previous
            </button>

            {/* Page Numbers */}
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
                    className={`px-3 py-2 text-sm font-medium rounded-md ${
                      currentPage === pageNum
                        ? 'bg-blue-600 text-white border border-blue-600'
                        : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              }
              return null;
            })}

            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              Next
            </button>
            
            <button
              onClick={() => goToPage(totalPages)}
              disabled={currentPage === totalPages}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              Last
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientsList;
