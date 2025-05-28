import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from './AuthContext';

export const FormContext = createContext();

export const FormProvider = ({ children }) => {
  const { isAuthenticated } = useContext(AuthContext);
  const [formFields, setFormFields] = useState({});
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  
  // Get form fields
  useEffect(() => {
    const getFormFields = async () => {
      try {
        const res = await axios.get('/api/form/fields');
        setFormFields(res.data);
      } catch (error) {
        console.error('Error fetching form fields:', error);
      }
    };
    
    getFormFields();
  }, []);
  
  // Get user's form data
  useEffect(() => {
    const getFormData = async () => {
      if (isAuthenticated) {
        try {
          setLoading(true);
          const res = await axios.get('/api/form');
          setFormData(res.data.formData);
        } catch (error) {
          console.error('Error fetching form data:', error);
        } finally {
          setLoading(false);
        }
      }
    };
    
    if (isAuthenticated) {
      getFormData();
    }
  }, [isAuthenticated]);
  
  // Update form data
  const updateFormData = async (newData) => {
    try {
      const updatedData = { ...formData, ...newData };
      setFormData(updatedData);
      
      await axios.post('/api/form', { formData: newData });
      
      return updatedData;
    } catch (error) {
      console.error('Error updating form data:', error);
      throw error;
    }
  };
  
  return (
    <FormContext.Provider
      value={{
        formFields,
        formData,
        loading,
        updateFormData
      }}
    >
      {children}
    </FormContext.Provider>
  );
};