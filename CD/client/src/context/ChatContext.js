import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from './AuthContext';
import { FormContext } from './FormContext';

export const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const { isAuthenticated } = useContext(AuthContext);
  const { updateFormData } = useContext(FormContext);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Get chat history
  useEffect(() => {
    const getChatHistory = async () => {
      if (isAuthenticated) {
        try {
          setLoading(true);
          const res = await axios.get('/api/chat/history');
          setChatHistory(res.data.history || []);
        } catch (error) {
          console.error('Error fetching chat history:', error);
        } finally {
          setLoading(false);
        }
      }
    };
    
    if (isAuthenticated) {
      getChatHistory();
    }
  }, [isAuthenticated]);
  
  // Send message to AI
  const sendMessage = async (message) => {
    try {
      setLoading(true);
      
      // Add user message to chat history
      setChatHistory(prev => [...prev, { role: 'user', content: message }]);
      
      const res = await axios.post('/api/chat/message', { message });
      
      // Add AI response to chat history
      setChatHistory(prev => [...prev, { role: 'assistant', content: res.data.reply }]);
      
      // Update form data if any was extracted
      if (res.data.extractedData && Object.keys(res.data.extractedData).length > 0) {
        await updateFormData(res.data.extractedData);
      }
      
      return res.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <ChatContext.Provider
      value={{
        chatHistory,
        loading,
        sendMessage
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};