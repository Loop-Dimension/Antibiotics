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
  const [editingDiagnosis2, setEditingDiagnosis2] = useState(false);
  const [diagnosis2Value, setDiagnosis2Value] = useState('');
  const [editingRecommendations, setEditingRecommendations] = useState({});
  const [selectedRecommendations, setSelectedRecommendations] = useState(new Set());
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [manualEntry, setManualEntry] = useState({
    antibiotic_name: '',
    dose: '',
    interval: '',
    duration: '',
    route: '',
    isManual: true
  });
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
      setDiagnosis2Value(response.data.diagnosis2 || '');
      
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

  const handleEditDiagnosis2 = () => {
    setEditingDiagnosis2(true);
  };

  const handleSaveDiagnosis2 = async () => {
    try {
      const updatedData = {
        ...patientData,
        diagnosis2: diagnosis2Value
      };
      
      await patientsAPI.updatePatient(patientId, updatedData);
      
      // Update local state
      setPatientData(prev => ({
        ...prev,
        diagnosis2: diagnosis2Value
      }));
      
      setEditingDiagnosis2(false);
    } catch (error) {
      console.error('Error updating diagnosis2:', error);
      alert('Failed to update diagnosis. Please try again.');
    }
  };

  const handleCancelEdit = () => {
    setDiagnosis2Value(patientData.diagnosis2 || '');
    setEditingDiagnosis2(false);
  };

  const handleSelectRecommendation = (index) => {
    const newSelected = new Set(selectedRecommendations);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedRecommendations(newSelected);
  };

  const handleEditRecommendation = (index, field, value) => {
    setRecommendations(prev => {
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        [field]: value
      };
      return updated;
    });
  };

  const handleSaveSelectedRecommendations = async () => {
    try {
      const selectedRecs = recommendations.filter((_, index) => 
        selectedRecommendations.has(index)
      );
      
      if (selectedRecs.length === 0) {
        alert('Please select at least one recommendation to save.');
        return;
      }
      
      const response = await patientsAPI.saveRecommendations(patientId, selectedRecs);
      
      if (response.data.success) {
        alert(`${selectedRecs.length} recommendation(s) saved successfully!`);
        // Optionally clear selections after saving
        setSelectedRecommendations(new Set());
      }
    } catch (error) {
      console.error('Error saving recommendations:', error);
      alert('Failed to save recommendations. Please try again.');
    }
  };

  const handleAddManualEntry = () => {
    setShowManualEntry(true);
  };

  const handleCancelManualEntry = () => {
    setShowManualEntry(false);
    setManualEntry({
      antibiotic_name: '',
      dose: '',
      interval: '',
      duration: '',
      route: '',
      isManual: true
    });
  };

  const handleSaveManualEntry = () => {
    if (!manualEntry.antibiotic_name.trim()) {
      alert('Please enter an antibiotic name.');
      return;
    }

    // Add manual entry to recommendations
    const newRecommendation = {
      ...manualEntry,
      antibiotic: manualEntry.antibiotic_name,
      isManual: true
    };

    setRecommendations(prev => [...prev, newRecommendation]);
    handleCancelManualEntry();
  };

  const handleManualEntryChange = (field, value) => {
    setManualEntry(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDeleteRecommendation = (index) => {
    if (window.confirm('Are you sure you want to delete this recommendation?')) {
      setRecommendations(prev => prev.filter((_, i) => i !== index));
      // Update selected recommendations set
      const newSelected = new Set();
      selectedRecommendations.forEach(selectedIndex => {
        if (selectedIndex < index) {
          newSelected.add(selectedIndex);
        } else if (selectedIndex > index) {
          newSelected.add(selectedIndex - 1);
        }
      });
      setSelectedRecommendations(newSelected);
    }
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

                {/* Diagnosis 1 */}
                {patientData.diagnosis1 && (
                  <div>
                    <label className="text-xs font-medium text-gray-500">Current Diagnosis:</label>
                    <div className="text-sm font-semibold text-gray-900">
                      {patientData.diagnosis1}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Diagnosis 2 Card */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 mb-6">
              <div className="flex items-center justify-between mb-3">
                <label className="text-xs font-medium text-gray-500">Second Diagnosis:</label>
                {!editingDiagnosis2 && (
                  <button
                    onClick={handleEditDiagnosis2}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Edit
                  </button>
                )}
              </div>
              
              {editingDiagnosis2 ? (
                <div className="space-y-3">
                  <input
                    type="text"
                    value={diagnosis2Value}
                    onChange={(e) => setDiagnosis2Value(e.target.value)}
                    placeholder="Enter second diagnosis..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autoFocus
                  />
                  <div className="flex space-x-2">
                    <button
                      onClick={handleSaveDiagnosis2}
                      className="px-3 py-1 bg-green-600 text-white text-xs rounded-md hover:bg-green-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="px-3 py-1 bg-gray-400 text-white text-xs rounded-md hover:bg-gray-500"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-sm font-semibold text-gray-900">
                  {patientData.diagnosis2 || (
                    <span className="text-gray-400 italic">No second diagnosis</span>
                  )}
                </div>
              )}
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
                <div className="flex space-x-2">
                  <button 
                    onClick={handleAddManualEntry}
                    className="px-3 py-1 bg-green-100 text-green-800 rounded-md text-sm font-medium hover:bg-green-200"
                  >
                    Add Manual Entry
                  </button>
                  <button 
                    onClick={() => fetchAIRecommendations(patientId)}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded-md text-sm font-medium hover:bg-blue-200"
                  >
                    Refresh
                  </button>
                </div>
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

              {/* Manual Entry Form */}
              {showManualEntry && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-blue-900">Add Manual Recommendation</h4>
                    <button 
                      onClick={handleCancelManualEntry}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      ✕ Cancel
                    </button>
                  </div>
                  <div className="grid grid-cols-5 gap-3 mb-3">
                    <div>
                      <label className="block text-xs font-medium text-blue-800 mb-1">Antibiotic Name *</label>
                      <input
                        type="text"
                        value={manualEntry.antibiotic_name}
                        onChange={(e) => handleManualEntryChange('antibiotic_name', e.target.value)}
                        placeholder="e.g., Not Recommended"
                        className="w-full px-2 py-1 text-sm border border-blue-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-blue-800 mb-1">Dose</label>
                      <input
                        type="text"
                        value={manualEntry.dose}
                        onChange={(e) => handleManualEntryChange('dose', e.target.value)}
                        placeholder="N/A or dose"
                        className="w-full px-2 py-1 text-sm border border-blue-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-blue-800 mb-1">Interval</label>
                      <input
                        type="text"
                        value={manualEntry.interval}
                        onChange={(e) => handleManualEntryChange('interval', e.target.value)}
                        placeholder="N/A or interval"
                        className="w-full px-2 py-1 text-sm border border-blue-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-blue-800 mb-1">Duration</label>
                      <input
                        type="text"
                        value={manualEntry.duration}
                        onChange={(e) => handleManualEntryChange('duration', e.target.value)}
                        placeholder="N/A or duration"
                        className="w-full px-2 py-1 text-sm border border-blue-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-blue-800 mb-1">Route</label>
                      <input
                        type="text"
                        value={manualEntry.route}
                        onChange={(e) => handleManualEntryChange('route', e.target.value)}
                        placeholder="N/A or route"
                        className="w-full px-2 py-1 text-sm border border-blue-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <button 
                      onClick={handleSaveManualEntry}
                      className="bg-blue-600 text-white px-4 py-1 rounded text-sm font-medium hover:bg-blue-700"
                    >
                      Add Entry
                    </button>
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
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Select</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Antibiotic</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dose</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Interval</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {recommendations.map((rec, index) => (
                          <tr key={index} className={`hover:bg-gray-50 ${rec.isManual ? 'bg-blue-25 border-l-4 border-l-blue-400' : ''}`}>
                            <td className="px-4 py-4 whitespace-nowrap">
                              <input
                                type="checkbox"
                                checked={selectedRecommendations.has(index)}
                                onChange={() => handleSelectRecommendation(index)}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                              />
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap">
                              <div className="flex items-center space-x-2">
                                <div>
                                  <div className="text-sm font-medium text-gray-900">{rec.antibiotic_name || rec.antibiotic}</div>
                                  <div className="text-xs text-gray-500">{rec.route || rec.routes_array?.join(', ') || 'Not specified'}</div>
                                </div>
                                {rec.isManual && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                    Manual
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap">
                              <input
                                type="text"
                                value={rec.dose || 'See guidelines'}
                                onChange={(e) => handleEditRecommendation(index, 'dose', e.target.value)}
                                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                              />
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap">
                              <input
                                type="text"
                                value={rec.interval || ''}
                                onChange={(e) => handleEditRecommendation(index, 'interval', e.target.value)}
                                placeholder="e.g., q12h"
                                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                              />
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap">
                              <input
                                type="text"
                                value={rec.duration || 'Per guidelines'}
                                onChange={(e) => handleEditRecommendation(index, 'duration', e.target.value)}
                                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    
                    {/* Action Buttons */}
                    <div className="mt-6 flex justify-between items-center">
                      <div className="text-sm text-gray-600">
                        {selectedRecommendations.size} of {recommendations.length} recommendation(s) selected
                      </div>
                      <div className="flex space-x-3">
                        <button 
                          onClick={handleSaveSelectedRecommendations}
                          disabled={selectedRecommendations.size === 0}
                          className="bg-green-600 text-white px-4 py-2 rounded-md font-medium hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                          Save Selected ({selectedRecommendations.size})
                        </button>
                        <button 
                          onClick={sendOrdersToEMR}
                          className="bg-slate-800 text-white px-6 py-2 rounded-md font-medium hover:bg-slate-900 transition-colors"
                        >
                          Send Orders to EMR
                        </button>
                      </div>
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
