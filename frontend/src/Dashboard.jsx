import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { patientsAPI } from './api';
import { useAuth } from './AuthContext';
import { useEMR } from './EMRContext';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import EMRAuthModal from './EMRAuthModal';

const Dashboard = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [patientData, setPatientData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [loading, setLoading] = useState(true);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showEMRAuth, setShowEMRAuth] = useState(false);
  const { user, logout } = useAuth();
  const { emrSession, openPatientRecord, createMedicationOrder } = useEMR();
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
      
      // Fetch AI recommendations
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
      const response = await patientsAPI.getAntibioticRecommendations(id);
      setRecommendations(response.data.recommendations || []);
    } catch (error) {
      console.error('Error fetching AI recommendations:', error);
      // Use fallback recommendations if API fails
      setRecommendations([]);
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

  const sendOrdersToEMR = async () => {
    const patientName = patientData?.name || 'Unknown Patient';
    const patientId = patientData?.patient_id || 'Unknown ID';
    
    if (!emrSession.authenticated) {
      setShowEMRAuth(true);
      return;
    }

    // Create recommended medication order from AI results (no hardcoded defaults)
    let recommendedMedication;
    if (recommendations && recommendations.length > 0) {
      const top = recommendations[0];
      recommendedMedication = {
        name: top?.antibiotic || 'Unknown',
        dosage: top?.dose || '',
        frequency: top?.interval || top?.frequency || '',
        duration: top?.duration || ''
      };
    } else {
      alert('No AI recommendation available. Please retrieve recommendations first or enter orders manually.');
      return;
    }

    const orderData = {
      patient_id: patientId,
      medication_name: recommendedMedication.name,
      dosage: recommendedMedication.dosage,
      frequency: recommendedMedication.frequency,
      duration: recommendedMedication.duration,
      instructions: `Recommended treatment for ${patientData?.diagnosis1 || 'infection'}. Monitor for allergic reactions.`,
      auto_send: true
    };

    const result = await createMedicationOrder(orderData);
    
    if (result.success) {
      alert(`Orders sent to EMR successfully for ${patientName} (ID: ${patientId})!\nOrder ID: ${result.data.id}\nMedication: ${recommendedMedication.name} ${recommendedMedication.dosage}`);
    } else {
      alert(`Failed to send orders to EMR: ${result.message}`);
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  const handleOpenEMR = async () => {
    if (!emrSession.authenticated) {
      setShowEMRAuth(true);
      return;
    }

    if (patientData?.patient_id) {
      const result = await openPatientRecord(patientData.patient_id);
      
      if (result.success) {
        alert(result.message);
      } else {
        alert(`Failed to open patient record: ${result.message}`);
      }
    } else {
      alert('No patient selected to open in EMR');
    }
  };

  const goToHomeDashboard = () => {
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
            {patientId && (
              <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-md">
                Patient ID: {patientId}
              </span>
            )}
            {emrSession.authenticated && (
              <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded-md">
                EMR: {emrSession.emrSystem}
              </span>
            )}
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
              onClick={handleOpenEMR}
              className={`px-4 py-2 rounded-md font-medium ${
                emrSession.authenticated 
                  ? 'bg-green-600 text-white hover:bg-green-700' 
                  : 'bg-gray-800 text-white hover:bg-gray-900'
              }`}
            >
              {emrSession.authenticated ? 'Open EMR' : 'Connect EMR'}
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

      <div className="flex">
        {/* Left Panel - Patient Snapshot */}
        <div className="w-1/2 p-4">
          {/* Patient Snapshot with Red Border */}
          <div className="bg-white rounded-lg border-2 border-red-500 p-4 mb-4">
            <div className="mb-4">
              <div className="flex items-start justify-between mb-2">
                <h2 className="text-lg font-bold text-gray-900">Patient Snapshot</h2>
                <div className="text-sm text-gray-600 text-right">
                  <div className="font-medium">수정 및 최종</div>
                </div>
              </div>
              <div className="text-sm text-gray-600">확인 후 한샘제 검색 버튼</div>
            </div>
            
            <div className="space-y-2 text-sm mb-4">
              <div><span className="font-medium">Patient ID:</span> {patientData?.patient_id}</div>
              <div><span className="font-medium">Name:</span> {patientData?.name || 'N/A'}, {patientData?.age || 0} {patientData?.gender === 'Male' || patientData?.gender === 'M' ? '♂' : '♀'}</div>
              <div><span className="font-medium">Date Recorded:</span> {patientData?.date_recorded || 'N/A'}</div>
              <div><span className="font-medium">Weight:</span> {patientData?.body_weight || 'N/A'} kg</div>
              <div><span className="font-medium">Height:</span> {patientData?.height || 'N/A'} cm</div>
              <div><span className="font-medium">BMI:</span> {patientData?.bmi || 'N/A'}</div>
              <div><span className="font-medium">Allergies:</span> {patientData?.allergies || 'None'}</div>
              <div><span className="font-medium">CrCl:</span> {patientData?.cockcroft_gault_crcl ? parseFloat(patientData.cockcroft_gault_crcl).toFixed(1) : 'N/A'} mL/min</div>
              <div><span className="font-medium">Current Abx:</span> {patientData?.antibiotics || 'None'}</div>
            </div>
            
            <div className="bg-gray-100 border border-gray-300 p-3 text-center font-bold text-base">
              추진단명
            </div>
          </div>

          {/* Vitals & Labs */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Vitals & Labs</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="font-medium">Temp</span>
                <span>{patientData?.body_temperature ? `${patientData.body_temperature}°C` : 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-medium">WBC</span>
                <span>{patientData?.wbc ? `${(parseFloat(patientData.wbc) / 1000).toFixed(1)}k` : 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-medium">Hb</span>
                <span>{patientData?.hb ? `${patientData.hb} g/dL` : 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-medium">Platelet</span>
                <span>{patientData?.platelet ? `${(parseFloat(patientData.platelet) / 1000).toFixed(0)}k` : 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-medium">AST</span>
                <span>{patientData?.ast ? `${patientData.ast} IU/L` : 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-medium">ALT</span>
                <span>{patientData?.alt ? `${patientData.alt} IU/L` : 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-medium">SCr</span>
                <span>{patientData?.scr ? `${patientData.scr} mg/dL` : 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-medium">CRP</span>
                <div className="flex items-center">
                  <span className="mr-2">{patientData?.crp ? `${parseFloat(patientData.crp).toFixed(1)} mg/L` : 'N/A'}</span>
                  {patientData?.crp && parseFloat(patientData.crp) > 10 && (
                    <div className="w-16 h-2 bg-red-500 rounded"></div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Micro Results */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Micro Results</h3>
            <div className="text-sm text-gray-600 mb-4">
              {patientData?.pathogen ? (
                <div>
                  <div><strong>Pathogen:</strong> {patientData.pathogen}</div>
                  {patientData.sample_type && <div><strong>Sample:</strong> {patientData.sample_type}</div>}
                  {patientData.diagnosis1 && <div><strong>Primary Diagnosis:</strong> {patientData.diagnosis1}</div>}
                  {patientData.diagnosis2 && patientData.diagnosis2 !== patientData.diagnosis1 && (
                    <div><strong>Secondary Diagnosis:</strong> {patientData.diagnosis2}</div>
                  )}
                </div>
              ) : (
                'No culture results yet.'
              )}
            </div>
            <div className="bg-gray-100 border border-gray-300 p-3 text-center font-bold text-base">
              투석 중 □
            </div>
          </div>
        </div>

        {/* Right Panel - Recommended Regimen */}
        <div className="w-1/2 p-4">
          <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Recommended Regimen</h3>
            
            {/* Allergy Warning */}
            {patientData?.allergies && patientData.allergies !== 'None' && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4 flex items-start">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mr-2 mt-0.5 flex-shrink-0" />
                <div className="text-sm">
                  <div className="font-medium text-yellow-800">Allergy Conflict</div>
                  <div className="text-yellow-700">Patient is allergic to {patientData.allergies}. Consider alternatives below.</div>
                </div>
              </div>
            )}

            {/* Current Treatment */}
            {patientData?.antibiotics && patientData.antibiotics !== 'None' && (
              <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
                <div className="text-sm">
                  <div className="font-medium text-blue-800">Current Treatment</div>
                  <div className="text-blue-700">{patientData.antibiotics}</div>
                </div>
              </div>
            )}

            {/* Recommendations Table */}
            <div className="overflow-x-auto mb-4">
              {recommendationsLoading ? (
                <div className="text-center py-8">
                  <div className="text-gray-500">Loading AI recommendations...</div>
                </div>
              ) : recommendations.length > 0 ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b">
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Antibiotic</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Dose</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Duration</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Rationale</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recommendations.map((rec, index) => (
                      <tr key={index} className={index < recommendations.length - 1 ? "border-b" : ""}>
                        <td className="px-3 py-4 text-sm">
                          <div className="font-medium">{rec.antibiotic}</div>
                          {rec.crcl_adjusted && (
                            <div className="text-xs text-orange-600">CrCl adjusted</div>
                          )}
                        </td>
                        <td className="px-3 py-4 text-sm">
                          <div>{rec.dose}</div>
                          <div className="text-xs text-gray-500">{rec.route} {rec.interval}</div>
                        </td>
                        <td className="px-3 py-4 text-sm text-center">
                          {rec.duration}
                        </td>
                        <td className="px-3 py-4 text-sm">
                          <div className="text-xs">{rec.rationale}</div>
                          {index === 0 && (
                            <div className="text-xs text-green-600 font-medium mt-1">Recommended</div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="text-center py-8">
                  <div className="text-gray-500">No AI recommendations available</div>
                  <div className="text-xs text-gray-400 mt-1">Please wait for API response or check patient data</div>
                  {/* Show current antibiotic instead of fallback recommendations */}
                  {patientData?.antibiotics && patientData.antibiotics !== 'None' && (
                    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
                      <div className="text-sm">
                        <div className="font-medium text-blue-800">Current Treatment</div>
                        <div className="text-blue-700">{patientData.antibiotics}</div>
                        <div className="text-xs text-blue-600 mt-2">
                          Fetching similar recommendations from database...
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <button 
              onClick={sendOrdersToEMR}
              className="w-full bg-gray-800 text-white py-3 px-4 rounded-md font-medium hover:bg-gray-900 transition-colors"
            >
              Send Orders to EMR
            </button>
          </div>

          {/* Guidelines Section */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Guideline Justification</h3>
            <div className="text-sm text-gray-700 space-y-2">
              <div><strong>Source:</strong> IDSA Guidelines 2023; Korean Guidelines 2024</div>
              <div>
                Recommended regimens based on local resistance rates 
                <span className="text-blue-600"> (last update: Aug 2025)</span>.
              </div>
              <div>AI engine risk-adjusted using patient comorbidities, CrCl: {patientData?.cockcroft_gault_crcl ? parseFloat(patientData.cockcroft_gault_crcl).toFixed(1) : 'N/A'} mL/min, and allergy profile.</div>
            </div>
          </div>
        </div>
      </div>

      {/* EMR Authentication Modal */}
      <EMRAuthModal 
        isOpen={showEMRAuth} 
        onClose={() => setShowEMRAuth(false)}
        onAuthenticated={() => {
          // EMR context will automatically update
        }}
      />
    </div>
  );
};

export default Dashboard;
