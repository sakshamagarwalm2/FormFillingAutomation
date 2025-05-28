import React, { useState, useContext, useEffect, useRef } from 'react';
import { AuthContext } from '../context/AuthContext';
import { FormContext } from '../context/FormContext';
import { ChatContext } from '../context/ChatContext';
import '../styles/Dashboard.css';

// Add this function to format message content
const formatMessage = (content) => {
  if (!content) return '';
  
  // Convert line breaks to <br>
  return content.split('\n').map((line, i) => (
    <React.Fragment key={i}>
      {line}
      {i < content.split('\n').length - 1 && <br />}
    </React.Fragment>
  ));
};

const Dashboard = () => {
  const { user, logout } = useContext(AuthContext);
  const { formFields, formData, updateFormData, loading: formLoading } = useContext(FormContext);
  const { chatHistory, sendMessage, loading: chatLoading } = useContext(ChatContext);
  const [message, setMessage] = useState('');
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'form'
  const messagesEndRef = useRef(null);
  
  // Auto-scroll to bottom of chat when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory]);
  
  // Handle form field change
  const handleFieldChange = (field, value) => {
    updateFormData({ [field]: value });
  };
  
  // Handle chat message submission
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    
    try {
      await sendMessage(message);
      setMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  // Function to console log all form data
  const handleConsoleLog = () => {
    const completeData = {
    //   user: user,
    //   formFields: formFields,
      formData: formData,
    //   chatHistory: chatHistory,
      timestamp: new Date().toISOString()
    };
    
    console.log('=== COMPLETE FORM DATA ===');
    console.log(JSON.stringify(completeData, null, 2));
    console.log('=== END FORM DATA ===');
  };
  
  // Render form fields based on their type without using switch case
  const renderFormField = (fieldName, fieldInfo) => {
    const value = formData[fieldName] || '';
    
    // For string type fields
    if (fieldInfo.type === 'string') {
      // If the field name contains 'date', render a date input
      if (fieldName.includes('date')) {
        return (
          <input
            type="date"
            value={value}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            placeholder={fieldInfo.description}
          />
        );
      }
      return (
        <input
          type="text"
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          placeholder={fieldInfo.description}
        />
      );
    }
    
    // For number type fields
    if (fieldInfo.type === 'number') {
      return (
        <input
          type="number"
          value={value}
          onChange={(e) => handleFieldChange(fieldName, parseFloat(e.target.value))}
          placeholder={fieldInfo.description}
          min={fieldInfo.min_value}
          max={fieldInfo.max_value}
        />
      );
    }
    
    // For enum type fields
    if (fieldInfo.type === 'enum') {
      return (
        <select
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
        >
          <option value="">Select {fieldName.replace('_', ' ')}</option>
          {fieldInfo.values.map(option => (
            <option key={option} value={option}>
              {option.replace('_', ' ')}
            </option>
          ))}
        </select>
      );
    }
    
    // For boolean type fields
    if (fieldInfo.type === 'boolean') {
      return (
        <input
          type="checkbox"
          checked={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.checked)}
        />
      );
    }
    
    // Default case
    return null;
  };
  
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Form Filling Assistant</h1>
        <div className="user-info">
          <span>Welcome, {user?.username}</span>
          <button onClick={logout} className="logout-btn">Logout</button>
          <button onClick={handleConsoleLog} className="console-log-btn">
            Log Data to Console
          </button>
        </div>
      </header>
      
      <div className="dashboard-tabs">
        <button 
          className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          AI Chat
        </button>
        <button 
          className={`tab-btn ${activeTab === 'form' ? 'active' : ''}`}
          onClick={() => setActiveTab('form')}
        >
          Form
        </button>
      </div>
      
      <div className="dashboard-content">
        {activeTab === 'chat' ? (
          <div className="chat-container">
            <div className="chat-messages">
              {chatHistory.length === 0 ? (
                <div className="welcome-message">
                  <p>Welcome to the AI Form Assistant! I can help you fill out your form.</p>
                  <p>Try saying something like: "My campaign name is Summer Promotion 2023"</p>
                </div>
              ) : (
                chatHistory.map((msg, index) => (
                  <div key={index} className={`message ${msg.role}`}>
                    <div className="message-avatar">
                      {msg.role === 'user' ? '👤' : '🤖'}
                    </div>
                    <div className="message-content">
                      {formatMessage(msg.content)}
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
            
            <form onSubmit={handleSendMessage} className="chat-input-form">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your message here..."
                disabled={chatLoading}
              />
              <button type="submit" disabled={chatLoading || !message.trim()}>
                {chatLoading ? 'Sending...' : 'Send'}
              </button>
            </form>
          </div>
        ) : (
          <div className="form-container">
            <div className="form-header">
              <h2>Campaign Form</h2>
              <button onClick={handleConsoleLog} className="console-log-btn secondary">
                📋 Log Data to Console
              </button>
            </div>
            {formLoading ? (
              <p>Loading form...</p>
            ) : (
              <div className="form-fields">
                {Object.entries(formFields).map(([fieldName, fieldInfo]) => {
                  // Check if field should be displayed based on dependencies
                  const shouldDisplay = !fieldInfo.depends_on || 
                    Object.entries(fieldInfo.depends_on).every(
                      ([depField, depValue]) => formData[depField] === depValue
                    );
                  
                  if (!shouldDisplay) return null;
                  
                  return (
                    <div key={fieldName} className="form-field">
                      <label>
                        {fieldName.replace(/_/g, ' ')}
                        {fieldInfo.required && <span className="required">*</span>}
                      </label>
                      <div className="field-input">
                        {renderFormField(fieldName, fieldInfo)}
                      </div>
                      <p className="field-description">{fieldInfo.description}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;