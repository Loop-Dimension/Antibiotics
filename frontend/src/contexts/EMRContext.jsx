import React, { createContext, useContext, useState, useEffect } from 'react';
import { emrAPI } from '../api';

const EMRContext = createContext();

export const useEMR = () => {
  const context = useContext(EMRContext);
  if (!context) {
    throw new Error('useEMR must be used within an EMRProvider');
  }
  return context;
};

export const EMRProvider = ({ children }) => {
  const [emrSession, setEMRSession] = useState({
    authenticated: false,
    emrSystem: null,
    expiresAt: null,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Don't automatically check EMR session to prevent infinite loops
    // checkEMRSession();
    setLoading(false);
  }, []);

  const checkEMRSession = async () => {
    try {
      // Only check EMR session if we have a valid auth token
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        setEMRSession({
          authenticated: false,
          emrSystem: null,
          expiresAt: null,
        });
        setLoading(false);
        return;
      }

      const response = await emrAPI.getSessionStatus();
      setEMRSession({
        authenticated: response.data.authenticated,
        emrSystem: response.data.emr_system || null,
        expiresAt: response.data.expires_at || null,
      });
    } catch (error) {
      console.warn('EMR session check failed (this is normal if not authenticated):', error.response?.status);
      setEMRSession({
        authenticated: false,
        emrSystem: null,
        expiresAt: null,
      });
    } finally {
      setLoading(false);
    }
  };

  const authenticateEMR = async (username, password) => {
    try {
      setLoading(true);
      const response = await emrAPI.authenticate({ username, password });
      
      setEMRSession({
        authenticated: true,
        emrSystem: response.data.emr_system,
        expiresAt: response.data.expires_at,
      });

      return { success: true, message: 'EMR authentication successful' };
    } catch (error) {
      console.error('EMR authentication failed:', error);
      return { 
        success: false, 
        message: error.response?.data?.error || 'EMR authentication failed' 
      };
    } finally {
      setLoading(false);
    }
  };

  const logoutEMR = async () => {
    try {
      await emrAPI.logout();
      setEMRSession({
        authenticated: false,
        emrSystem: null,
        expiresAt: null,
      });
      return { success: true };
    } catch (error) {
      console.error('EMR logout failed:', error);
      return { success: false, error: error.message };
    }
  };

  const openPatientRecord = async (patientId) => {
    try {
      const response = await emrAPI.openPatientRecord(patientId);
      if (response.data.success) {
        // In a real implementation, this would open the EMR in a new window/tab
        window.open(response.data.url, '_blank', 'width=1200,height=800');
        return { success: true, message: `Opening patient ${patientId} in ${response.data.emr_system}` };
      } else {
        return { success: false, message: response.data.error };
      }
    } catch (error) {
      console.error('Error opening patient record:', error);
      return { 
        success: false, 
        message: error.response?.data?.error || 'Failed to open patient record' 
      };
    }
  };

  const createMedicationOrder = async (orderData) => {
    try {
      const response = await emrAPI.createMedicationOrder(orderData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating medication order:', error);
      return { 
        success: false, 
        message: error.response?.data?.error || 'Failed to create medication order' 
      };
    }
  };

  const sendOrderToEMR = async (orderId) => {
    try {
      const response = await emrAPI.sendOrderToEMR(orderId);
      return { 
        success: true, 
        message: response.data.message,
        confirmationNumber: response.data.confirmation_number 
      };
    } catch (error) {
      console.error('Error sending order to EMR:', error);
      return { 
        success: false, 
        message: error.response?.data?.error || 'Failed to send order to EMR' 
      };
    }
  };

  const value = {
    emrSession,
    loading,
    authenticateEMR,
    logoutEMR,
    openPatientRecord,
    createMedicationOrder,
    sendOrderToEMR,
    checkEMRSession,
  };

  return <EMRContext.Provider value={value}>{children}</EMRContext.Provider>;
};

export default EMRContext;
