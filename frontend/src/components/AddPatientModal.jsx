import React, { useState } from 'react';
import { patientsAPI } from '../api';

const AddPatientModal = ({ isOpen, onClose, onPatientAdded }) => {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    weight: '',
    height: '',
    allergies: '',
    antibiotics: '',
    pathogen: '',
    diagnosis1: '',
    cockcroft_gault_crcl: '',
    body_temperature: '',
    wbc: '',
    crp: '',
    // Additional required fields
    date_recorded: new Date().toISOString().split('T')[0], // Today's date
    body_weight: '',
    hb: '', // Hemoglobin
    platelet: '',
    ast: '', // Aspartate aminotransferase
    alt: '', // Alanine aminotransferase
    scr: '', // Serum creatinine
    sample_type: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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

    try {
      // Convert numeric fields
      const processedData = {
        ...formData,
        age: formData.age ? parseInt(formData.age) : null,
        weight: formData.weight ? parseFloat(formData.weight) : null,
        body_weight: formData.body_weight ? parseFloat(formData.body_weight) : null,
        height: formData.height ? parseFloat(formData.height) : null,
        cockcroft_gault_crcl: formData.cockcroft_gault_crcl ? parseFloat(formData.cockcroft_gault_crcl) : null,
        body_temperature: formData.body_temperature ? parseFloat(formData.body_temperature) : null,
        wbc: formData.wbc ? parseFloat(formData.wbc) : null,
        crp: formData.crp ? parseFloat(formData.crp) : null,
        hb: formData.hb ? parseFloat(formData.hb) : null,
        platelet: formData.platelet ? parseFloat(formData.platelet) : null,
        ast: formData.ast ? parseFloat(formData.ast) : null,
        alt: formData.alt ? parseFloat(formData.alt) : null,
        scr: formData.scr ? parseFloat(formData.scr) : null,
      };

      const response = await patientsAPI.createPatient(processedData);
      onPatientAdded(response.data);
      onClose();
      
      // Reset form
      setFormData({
        name: '',
        age: '',
        gender: '',
        weight: '',
        height: '',
        allergies: '',
        antibiotics: '',
        pathogen: '',
        diagnosis1: '',
        cockcroft_gault_crcl: '',
        body_temperature: '',
        wbc: '',
        crp: '',
        // Additional required fields
        date_recorded: new Date().toISOString().split('T')[0],
        body_weight: '',
        hb: '',
        platelet: '',
        ast: '',
        alt: '',
        scr: '',
        sample_type: '',
      });
    } catch (error) {
      console.error('Error adding patient:', error);
      
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
          setError(errorData.error || 'Failed to add patient');
        }
      } else {
        setError('Failed to add patient. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Add New Patient</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            <pre className="whitespace-pre-wrap text-sm">{error}</pre>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Basic Information */}
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
                Age
              </label>
              <input
                type="number"
                name="age"
                value={formData.age}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Age"
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
                <option value="">Select Gender</option>
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="O">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Weight (kg) *
              </label>
              <input
                type="number"
                step="0.1"
                name="weight"
                value={formData.weight}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Weight"
              />
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
                placeholder="Body Weight"
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
                placeholder="Height"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CrCl (mL/min)
              </label>
              <input
                type="number"
                step="0.01"
                name="cockcroft_gault_crcl"
                value={formData.cockcroft_gault_crcl}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Creatinine Clearance"
              />
            </div>
          </div>

          {/* Clinical Information */}
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
                placeholder="e.g., PO ciprofloxacin 500mg bid"
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
                placeholder="e.g., E. coli"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Diagnosis
              </label>
              <input
                type="text"
                name="diagnosis1"
                value={formData.diagnosis1}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Primary diagnosis"
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
                placeholder="e.g., Penicillin, None"
              />
            </div>
          </div>

          {/* Lab Values */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature (°C) *
              </label>
              <input
                type="number"
                step="0.1"
                max="99.9"
                name="body_temperature"
                value={formData.body_temperature}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Body temperature"
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
                placeholder="White blood cell count"
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
                placeholder="C-reactive protein"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hemoglobin (Hb) *
              </label>
              <input
                type="number"
                step="0.1"
                name="hb"
                value={formData.hb}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Hemoglobin level"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Platelet Count *
              </label>
              <input
                type="number"
                step="1"
                name="platelet"
                value={formData.platelet}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Platelet count"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                AST *
              </label>
              <input
                type="number"
                step="0.1"
                name="ast"
                value={formData.ast}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Aspartate aminotransferase"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ALT *
              </label>
              <input
                type="number"
                step="0.1"
                name="alt"
                value={formData.alt}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Alanine aminotransferase"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Serum Creatinine (SCr) *
              </label>
              <input
                type="number"
                step="0.01"
                name="scr"
                value={formData.scr}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Serum creatinine"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sample Type *
              </label>
              <select
                name="sample_type"
                value={formData.sample_type}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Sample Type</option>
                <option value="Blood">Blood</option>
                <option value="Urine">Urine</option>
                <option value="Sputum">Sputum</option>
                <option value="CSF">CSF</option>
                <option value="Wound">Wound</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Adding...' : 'Add Patient'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddPatientModal;
