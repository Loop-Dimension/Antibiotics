import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { patientsAPI } from '../api';
import { useAuth } from '../contexts/AuthContext';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const ClinicalDashboard = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [patientData, setPatientData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [recommendationData, setRecommendationData] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [loading, setLoading] = useState(true);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { user, logout } = useAuth();
  const searchTimeoutRef = useRef(null);

  useEffect(() => {
    if (patientId) {
      fetchSpecificPatient(patientId);
    } else {
      fetchInitialPatient();
    }
  }, [patientId]);

  const fetchSpecificPatient = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const response = await patientsAPI.getPatient(id);
      setPatientData(response.data);
      
      // Fetch recommended regimen
      fetchAIRecommendations(id);
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching specific patient:', error);
      if (error.response?.status === 404) {
        setError(`Patient with ID ${id} not found`);
      } else {
        setError('Error loading patient data');
      }
      setLoading(false);
    }
  };

  const fetchAIRecommendations = async (id) => {
    setRecommendationsLoading(true);
    try {
      const response = await patientsAPI.getClinicalRecommendations(id);
      const data = response.data;
      
      if (data.success && data.recommendations) {
        setRecommendations(data.recommendations);
        setRecommendationData(data); // Store full response for analysis display
      } else {
        console.warn('No recommendations returned:', data.error || data.details);
        setRecommendations([]);
        setRecommendationData(data);
      }
    } catch (error) {
      console.error('Error fetching clinical recommendations:', error);
      setRecommendations([]);
      setRecommendationData({
        success: false,
        error: 'Failed to fetch recommendations',
        details: error.response?.data?.details || error.message
      });
    }
    setRecommendationsLoading(false);
  };

  const fetchInitialPatient = async () => {
    try {
      const response = await patientsAPI.getPatients();
      if (response.data && response.data.length > 0) {
        // Set first patient as default
        setPatientData(response.data[0]);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching patient data:', error);
      // Use mock data if API fails
      const mockData = {
        patient_id: 1,
        name: 'Kim',
        age: 65,
        gender: 'M',
        body_temperature: 38.3,
        wbc: 14200,
        crp: 92,
        cockcroft_gault_crcl: 50,
        pathogen: 'Escherichia coli',
        sample_type: 'urine',
        allergies: 'Penicillin'
      };
      setPatientData(mockData);
      setLoading(false);
    }
  };

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);

    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (value.trim().length >= 2) {
      // Debounce search - wait 300ms after user stops typing
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
    // Navigate to specific patient URL
    navigate(`/patient/${patient.patient_id}`);
  };

  const handleSearchBlur = () => {
    // Delay hiding results to allow clicking on them
    setTimeout(() => {
      setShowSearchResults(false);
    }, 200);
  };

  const handleSearchFocus = () => {
    if (searchResults.length > 0 && searchTerm.length >= 2) {
      setShowSearchResults(true);
    }
  };

  const handleLogout = async () => {
    await logout();
  };
      
  const goToHomeDashboard = () => {
    navigate('/');
  };

  const sendOrdersToEMR = () => {
    // Navigate back to home screen when Send Orders to EMR is clicked
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 
              onClick={goToHomeDashboard}
              className="text-2xl font-bold text-gray-900 cursor-pointer hover:text-blue-600"
            >
              ImpactUs Antibiotic Advisor
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Search patient..."
                value={searchTerm}
                onChange={handleSearchChange}
                onFocus={handleSearchFocus}
                onBlur={handleSearchBlur}
                className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-80"
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
              onClick={goToHomeDashboard}
              className="bg-slate-800 text-white px-6 py-2 rounded-md font-medium hover:bg-slate-900"
            >
              Open EMR
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

      {/* Quick Stats Bar - Only show when not viewing specific patient */}
      {!patientId && (
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="grid grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">--</div>
              <div className="text-sm text-gray-600">Total Patients</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">--</div>
              <div className="text-sm text-gray-600">Active Cases</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">--</div>
              <div className="text-sm text-gray-600">High Risk</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">--</div>
              <div className="text-sm text-gray-600">Recent Updates</div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Breadcrumb */}
      <div className="bg-gray-100 border-b border-gray-200 px-6 py-3">
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <button 
            onClick={() => navigate('/')}
            className="hover:text-blue-600"
          >
            Dashboard
          </button>
          {patientId && (
            <>
              <span>›</span>
              <button 
                onClick={() => navigate('/patients')}
                className="hover:text-blue-600"
              >
                Patients
              </button>
              <span>›</span>
              <span className="text-gray-900 font-medium">
                {patientData?.name || `Patient ${patientId}`}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Main Content */}
      {patientId && patientData ? (
        /* Patient View Layout */
        <div className="flex">
          {/* Left Panel - Patient Information */}
          <div className="w-1/3 p-6">
            {/* Patient Snapshot Card */}
            <div className="bg-white rounded-lg border border-red-300 shadow-sm p-4 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-gray-900">Patient Snapshot</h2>
                <div className="flex space-x-2">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                    {patientData.patient_id}
                  </span>
                  {patientData.pathogen && patientData.pathogen !== 'Unknown' && (
                    <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">
                      Culture +
                    </span>
                  )}
                </div>
              </div>
              
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-gray-500">Name:</label>
                  <div className="text-sm font-semibold text-gray-900">
                    {patientData.name}, {patientData.age} {patientData.gender === 'Male' || patientData.gender === 'M' ? '♂' : '♀'}
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500">Allergies:</label>
                  <div className={`text-sm ${patientData.allergies && patientData.allergies !== 'None' ? 'text-red-600 font-medium' : 'text-gray-700'}`}>
                    {patientData.allergies || 'None'}
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500">CrCl:</label>
                  <div className="text-sm text-gray-700">
                    {patientData.cockcroft_gault_crcl ? parseFloat(patientData.cockcroft_gault_crcl).toFixed(1) : 'N/A'} mL/min
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500">Current Abc:</label>
                  <div className="text-sm text-gray-700">
                    {patientData.antibiotics && patientData.antibiotics !== 'None' ? patientData.antibiotics : 'None'}
                  </div>
                </div>
              </div>
            </div>

            {/* Vitals & Labs Card */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 mb-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Vitals & Labs</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Temp</span>
                  <span className={`text-sm font-semibold ${patientData.body_temperature && parseFloat(patientData.body_temperature) > 38 ? 'text-red-600' : 'text-gray-900'}`}>
                    {patientData.body_temperature ? `${patientData.body_temperature}°C` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">WBC</span>
                  <span className={`text-sm font-semibold ${patientData.wbc && (parseFloat(patientData.wbc) > 11000 || parseFloat(patientData.wbc) < 4000) ? 'text-red-600' : 'text-gray-900'}`}>
                    {patientData.wbc ? `${(parseFloat(patientData.wbc) / 1000).toFixed(1)}k` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">CRP</span>
                  <div className="flex items-center">
                    <span className={`text-sm font-semibold mr-2 ${patientData.crp && parseFloat(patientData.crp) > 10 ? 'text-red-600' : 'text-gray-900'}`}>
                      {patientData.crp ? `${parseFloat(patientData.crp).toFixed(0)} mg/L` : 'N/A'}
                    </span>
                    {patientData.crp && parseFloat(patientData.crp) > 10 && (
                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Micro Results Card */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Micro Results</h3>
              {patientData.pathogen && patientData.pathogen !== 'Unknown' ? (
                <div className="space-y-2">
                  <div className="text-sm">
                    <span className="font-medium">Pathogen:</span> {patientData.pathogen}
                  </div>
                  {patientData.sample_type && (
                    <div className="text-sm">
                      <span className="font-medium">Sample:</span> {patientData.sample_type}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-gray-500">No culture results yet.</div>
              )}
            </div>
          </div>

          {/* Right Panel - Recommendations */}
          <div className="w-2/3 p-6">
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">Recommended Regimen</h3>
                <button 
                  onClick={() => fetchAIRecommendations(patientId)}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-md text-sm font-medium hover:bg-blue-200"
                >
                  Refresh
                </button>
              </div>
              
              {/* Allergy Warning */}
              {patientData.allergies && patientData.allergies !== 'None' && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4 flex items-start">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mr-3 mt-0.5 flex-shrink-0" />
                  <div className="text-sm">
                    <div className="font-medium text-yellow-800">Allergy Conflict</div>
                    <div className="text-yellow-700">Patient is allergic to {patientData.allergies}. Avoid β-lactams; consider alternatives below.</div>
                  </div>
                </div>
              )}

              {/* Recommendations Table */}
              <div className="space-y-4">
                {recommendationsLoading ? (
                  <div className="text-center py-8">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <div className="text-gray-500 mt-2">Loading recommended regimen...</div>
                  </div>
                ) : recommendations.length > 0 ? (
                  <div className="overflow-hidden">
                    <table className="min-w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Antibiotic</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dose</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rationale</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {recommendations.map((rec, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-4 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{rec.antibiotic_name || rec.antibiotic}</div>
                              <div className="text-xs text-gray-500">{rec.route || rec.routes_array?.join(', ') || 'Not specified'}</div>
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900">{rec.dose || 'See guidelines'}</div>
                              {rec.interval && (
                                <div className="text-xs text-gray-500">{rec.interval}</div>
                              )}
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900">{rec.duration || 'Per guidelines'}</div>
                            </td>
                            <td className="px-4 py-4">
                              <div className="text-sm text-gray-900">{rec.remark || rec.medical_rationale || 'Evidence-based recommendation'}</div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    
                    {/* Send Orders to EMR Button */}
                    <div className="mt-6 flex justify-start">
                      <button 
                        onClick={sendOrdersToEMR}
                        className="bg-slate-800 text-white px-6 py-3 rounded-md font-medium hover:bg-slate-900 transition-colors"
                      >
                        Send Orders to EMR
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    {recommendationData?.is_fallback ? (
                      <div>
                        <div className="text-amber-600 font-medium">Limited Recommendations Available</div>
                        <div className="text-sm text-gray-600 mt-2 max-w-md mx-auto">
                          {recommendationData.message || "Showing general empirical therapy options. Consider pathogen-specific therapy when culture results are available."}
                        </div>
                      </div>
                    ) : recommendationData?.success === false ? (
                      <div>
                        <div className="text-red-600 font-medium">No Clinical Recommendations Found</div>
                        <div className="text-sm text-gray-600 mt-2">
                          No antibiotic recommendations available for this patient profile.
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div className="text-gray-600 font-medium">Select a patient to view recommendations</div>
                        <div className="text-sm text-gray-500 mt-2">Click "Get Recommendations" to load clinical guidance.</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Home Dashboard Layout - No specific patient selected */
        <div className="p-6">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Clinical Decision Support System</h2>
              <p className="text-gray-600">Evidence-based antibiotic recommendations tailored to patient clinical data.</p>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div 
                onClick={() => navigate('/add-patient')}
                className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm hover:shadow-md cursor-pointer transition-shadow"
              >
                <div className="flex items-center">
                  <div className="bg-emerald-100 p-3 rounded-lg">
                    <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold text-gray-900">New Patient</h3>
                    <p className="text-sm text-gray-600">Add a new patient case</p>
                  </div>
                </div>
              </div>

              <div 
                onClick={() => navigate('/patients')}
                className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm hover:shadow-md cursor-pointer transition-shadow"
              >
                <div className="flex items-center">
                  <div className="bg-blue-100 p-3 rounded-lg">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold text-gray-900">All Patients</h3>
                    <p className="text-sm text-gray-600">Browse patient database</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                <div className="flex items-center">
                  <div className="bg-purple-100 p-3 rounded-lg">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold text-gray-900">Guidelines</h3>
                    <p className="text-sm text-gray-600">Clinical guidelines & resources</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity or Instructions */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Getting Started</h3>
              <div className="space-y-3 text-sm text-gray-600">
                <p>• Use the search bar above to quickly find existing patients</p>
                <p>• Add new patients with comprehensive clinical data for accurate recommendations</p>
                <p>• Recommendations are based on the latest IDSA and Korean clinical guidelines</p>
                <p>• All dosing suggestions are automatically adjusted for renal function</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClinicalDashboard;
