import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts';
import { ProtectedRoute } from './components';
import { Login, Register, Dashboard, PatientsList, AddPatient, EditPatient } from './pages';

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <PatientsList />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/patients" 
            element={
              <ProtectedRoute>
                <PatientsList />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/add-patient" 
            element={
              <ProtectedRoute>
                <AddPatient />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/edit-patient/:patientId" 
            element={
              <ProtectedRoute>
                <EditPatient />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/patient/:patientId" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
