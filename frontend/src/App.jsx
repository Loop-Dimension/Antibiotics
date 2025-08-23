import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './AuthContext';
import { EMRProvider } from './EMRContext';
import ProtectedRoute from './ProtectedRoute';
import Login from './Login';
import Register from './Register';
import Dashboard from './Dashboard';
import PatientsList from './PatientsList';

const App = () => {
  return (
    <AuthProvider>
      <EMRProvider>
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
      </EMRProvider>
    </AuthProvider>
  );
};

export default App;
