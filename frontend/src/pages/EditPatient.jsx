import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { patientsAPI } from '../api';
import { useAuth } from '../contexts/AuthContext';

const EditPatient = () => {
  const navigate = useNavigate();
  const { patientId } = useParams();
  const { user, logout } = useAuth();
  const [formData, setFormData] = useState({
    // Essential fields - REQUIRED
    name: '',
    age: '',
    date_recorded: '',
    body_weight: '',
    diagnosis1: '',
    body_temperature: '',
    scr: '',
    cockcroft_gault_crcl: '',
    
    // Important but optional fields
    gender: '',
    height: '',
    wbc: '',
    crp: '',
    hb: '',
    platelet: '',
    ast: '',
    alt: '',
    pathogen: '',
    sample_type: '',
    antibiotics: '',
    allergies: '',
    
    // Additional optional fields
    diagnosis2: '',
    current_medications: '',
  });
  const [loading, setLoading] = useState(false);
  const [loadingPatient, setLoadingPatient] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    fetchPatient();
  }, [patientId]);

  const fetchPatient = async () => {
    try {
      setLoadingPatient(true);
      const response = await patientsAPI.getPatient(patientId);
      const patient = response.data;
      
      // Populate form with existing patient data
      setFormData({
        name: patient.name || '',
        age: patient.age || '',
        date_recorded: patient.date_recorded || '',
        body_weight: patient.body_weight || '',
        diagnosis1: patient.diagnosis1 || '',
        body_temperature: patient.body_temperature || '',
        scr: patient.scr || '',
        cockcroft_gault_crcl: patient.cockcroft_gault_crcl || '',
        gender: patient.gender || '',
        height: patient.height || '',
        wbc: patient.wbc || '',
        crp: patient.crp || '',
        hb: patient.hb || '',
        platelet: patient.platelet || '',
        ast: patient.ast || '',
        alt: patient.alt || '',
        pathogen: patient.pathogen || '',
        sample_type: patient.sample_type || '',
        antibiotics: patient.antibiotics || '',
        allergies: patient.allergies || '',
        diagnosis2: patient.diagnosis2 || '',
        current_medications: patient.current_medications || '',
      });
      setLoadingPatient(false);
    } catch (error) {
      console.error('Error fetching patient:', error);
      setError('Failed to load patient data');
      setLoadingPatient(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);

    // Client-side validation - Only check truly essential fields
    const validationErrors = [];
    
    if (!formData.name.trim()) validationErrors.push('Patient name is required');
    if (!formData.age) validationErrors.push('Patient age is required');
    if (!formData.date_recorded) validationErrors.push('Date recorded is required');
    if (!formData.body_weight) validationErrors.push('Body weight is required (needed for dosing)');
    if (!formData.diagnosis1.trim()) validationErrors.push('Primary diagnosis is required');
    if (!formData.body_temperature) validationErrors.push('Body temperature is required');
    if (!formData.scr) validationErrors.push('Serum creatinine is required (needed for dosing)');
    if (!formData.cockcroft_gault_crcl) validationErrors.push('Creatinine clearance is required (needed for dosing)');
    
    if (validationErrors.length > 0) {
      setError('Please fill in all required fields:\n' + validationErrors.join('\n'));
      setLoading(false);
      return;
    }

    try {
      // Process form data with sensible defaults
      const processedData = {
        ...formData,
        // Convert numeric fields
        age: formData.age ? parseInt(formData.age) : null,
        body_weight: formData.body_weight ? parseFloat(formData.body_weight) : null,
        height: formData.height ? parseFloat(formData.height) : null,
        body_temperature: formData.body_temperature ? parseFloat(formData.body_temperature) : null,
        scr: formData.scr ? parseFloat(formData.scr) : null,
        cockcroft_gault_crcl: formData.cockcroft_gault_crcl ? parseFloat(formData.cockcroft_gault_crcl) : null,
        wbc: formData.wbc ? parseFloat(formData.wbc) : null,
        crp: formData.crp ? parseFloat(formData.crp) : null,
        hb: formData.hb ? parseFloat(formData.hb) : null,
        platelet: formData.platelet ? parseFloat(formData.platelet) : null,
        ast: formData.ast ? parseFloat(formData.ast) : null,
        alt: formData.alt ? parseFloat(formData.alt) : null,
        
        // Ensure default values for text fields that have defaults in the model
        pathogen: formData.pathogen.trim() || 'Unknown',
        sample_type: formData.sample_type.trim() || 'Not specified',
        antibiotics: formData.antibiotics.trim() || 'None',
        allergies: formData.allergies.trim() || 'None',
        gender: formData.gender || null, // Allow null for gender
      };

      const response = await patientsAPI.updatePatient(patientId, processedData);
      setSuccess(true);
      
      // Redirect to patient detail after 2 seconds
      setTimeout(() => {
        navigate(`/patient/${patientId}`);
      }, 2000);
      
    } catch (error) {
      console.error('Error updating patient:', error);
      
      if (error.response?.data) {
        // Handle validation errors
        const errorData = error.response.data;
        if (typeof errorData === 'object' && !errorData.error) {
          // Format field-specific errors
          const errorMessages = Object.entries(errorData)
            .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
            .join('\n');
          setError(`Validation errors:\n${errorMessages}`);
        } else {
          setError(errorData.error || 'Failed to update patient');
        }
      } else {
        setError('Failed to update patient. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  const handleCancel = () => {
    navigate(`/patient/${patientId}`);
  };

  if (loadingPatient) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">
              ImpactUs Antibiotic Advisor
            </h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, {user?.first_name} {user?.last_name} ({user?.username})
              </span>
              <button 
                onClick={handleLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-md font-medium hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* Loading */}
        <div className="container mx-auto px-6 py-8">
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
              <div className="text-xl">Loading patient data...</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">
              ImpactUs Antibiotic Advisor
            </h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, {user?.first_name} {user?.last_name} ({user?.username})
              </span>
              <button 
                onClick={handleLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-md font-medium hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* Success Message */}
        <div className="container mx-auto px-6 py-8">
          <div className="max-w-2xl mx-auto">
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg text-center">
              <div className="text-xl font-bold mb-2">✅ Patient Updated Successfully!</div>
              <div className="text-sm">Redirecting to patient details...</div>
            </div>
          </div>
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
            <span className="text-sm bg-orange-100 text-orange-800 px-2 py-1 rounded-md">
              Edit Patient #{patientId}
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">
              Welcome, {user?.first_name} {user?.last_name} ({user?.username})
            </span>
            <button 
              onClick={() => navigate(`/patient/${patientId}`)}
              className="bg-gray-600 text-white px-4 py-2 rounded-md font-medium hover:bg-gray-700"
            >
              Back to Patient
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
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Edit Patient Information</h2>
              <p className="text-sm text-gray-600 mt-1">Update patient details below</p>
            </div>

            <div className="p-6">
              {error && (
                <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                  <pre className="whitespace-pre-wrap text-sm">{error}</pre>
                </div>
              )}

              {/* Help Text */}
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="text-sm font-medium text-blue-900 mb-2">📋 Field Requirements Guide</h4>
                <div className="text-xs text-blue-800 space-y-1">
                  <p><strong>Essential fields (*)</strong> - Required for antibiotic recommendations:</p>
                  <p>• Patient name, age, weight, diagnosis, temperature</p>
                  <p>• Serum creatinine and creatinine clearance (for dosing calculations)</p>
                  <p><strong>Optional fields</strong> - Helpful but not required:</p>
                  <p>• Lab values (WBC, CRP, Hb, etc.) - improves recommendation accuracy</p>
                  <p>• Height, gender, pathogen details - provides better context</p>
                  <p>• Default values will be used for empty optional text fields</p>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-8">
                {/* Basic Information Section */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Name *
                      </label>
                      <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Patient Name"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Date Recorded *
                      </label>
                      <input
                        type="date"
                        name="date_recorded"
                        value={formData.date_recorded}
                        onChange={handleChange}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Age *
                      </label>
                      <input
                        type="number"
                        name="age"
                        value={formData.age}
                        onChange={handleChange}
                        required
                        min="0"
                        max="150"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Patient age"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Gender
                      </label>
                      <select
                        name="gender"
                        value={formData.gender}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select Gender (Optional)</option>
                        <option value="M">Male</option>
                        <option value="F">Female</option>
                        <option value="O">Other</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Body Weight (kg) *
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        name="body_weight"
                        value={formData.body_weight}
                        onChange={handleChange}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Weight (required for dosing)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Height (cm)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        name="height"
                        value={formData.height}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Height (optional)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        CrCl (mL/min) *
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        name="cockcroft_gault_crcl"
                        value={formData.cockcroft_gault_crcl}
                        onChange={handleChange}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Creatinine Clearance (required for dosing)"
                      />
                    </div>
                  </div>
                </div>

                {/* Clinical Information Section */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Clinical Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Current Antibiotics
                      </label>
                      <input
                        type="text"
                        name="antibiotics"
                        value={formData.antibiotics}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., PO ciprofloxacin 500mg bid (or leave blank for 'None')"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Pathogen
                      </label>
                      <input
                        type="text"
                        name="pathogen"
                        value={formData.pathogen}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., E. coli (or leave blank for 'Unknown')"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Primary Diagnosis *
                      </label>
                      <input
                        type="text"
                        name="diagnosis1"
                        value={formData.diagnosis1}
                        onChange={handleChange}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Primary diagnosis (required)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Secondary Diagnosis
                      </label>
                      <input
                        type="text"
                        name="diagnosis2"
                        value={formData.diagnosis2}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Secondary diagnosis (optional)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Allergies
                      </label>
                      <input
                        type="text"
                        name="allergies"
                        value={formData.allergies}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., Penicillin (or leave blank for 'None')"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Sample Type
                      </label>
                      <select
                        name="sample_type"
                        value={formData.sample_type}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="Not specified">Not specified</option>
                        <option value="Blood">Blood</option>
                        <option value="Urine">Urine</option>
                        <option value="Sputum">Sputum</option>
                        <option value="CSF">CSF</option>
                        <option value="Wound">Wound</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Laboratory Values Section */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Laboratory Values</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Temperature (°C) *
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="30"
                        max="50"
                        name="body_temperature"
                        value={formData.body_temperature}
                        onChange={handleChange}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Body temperature (required)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Serum Creatinine (mg/dL) *
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        name="scr"
                        value={formData.scr}
                        onChange={handleChange}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Serum creatinine (required for dosing)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        WBC
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        name="wbc"
                        value={formData.wbc}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="White blood cell count (optional)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        CRP
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        name="crp"
                        value={formData.crp}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="C-reactive protein (optional)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Hemoglobin (g/dL)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        name="hb"
                        value={formData.hb}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Hemoglobin level (optional)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Platelet Count
                      </label>
                      <input
                        type="number"
                        step="1"
                        name="platelet"
                        value={formData.platelet}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Platelet count (optional)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        AST
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        name="ast"
                        value={formData.ast}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="AST (optional)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        ALT
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        name="alt"
                        value={formData.alt}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="ALT (optional)"
                      />
                    </div>
                  </div>
                </div>

                {/* Additional Information */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Additional Information</h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Current Medications
                    </label>
                    <textarea
                      name="current_medications"
                      value={formData.current_medications}
                      onChange={handleChange}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="List other current medications (optional)"
                    />
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={handleCancel}
                    className="px-6 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {loading ? 'Updating Patient...' : 'Update Patient'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditPatient;
