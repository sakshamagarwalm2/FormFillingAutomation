const express = require('express');
const router = express.Router();
const verifyToken = require('../middleware/auth');
const Groq = require('groq-sdk');

// Initialize Groq client
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY || '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' });

// Get chat history
router.get('/history', verifyToken, (req, res) => {
  const chatHistory = req.app.locals.chatHistory;
  const userHistory = chatHistory[req.user.id] || [];
  
  res.json({ history: userHistory });
});

// Send message to AI
router.post('/message', verifyToken, async (req, res) => {
  try {
    const { message } = req.body;
    const forms = req.app.locals.forms;
    const chatHistory = req.app.locals.chatHistory;
    
    // Initialize user's chat history if it doesn't exist
    if (!chatHistory[req.user.id]) {
      chatHistory[req.user.id] = [];
    }
    
    // Add user message to history
    chatHistory[req.user.id].push({ role: 'user', content: message });
    
    // Get user's form data
    const userForm = forms.find(form => form.userId === req.user.id);
    const formData = userForm ? userForm.data : {};
    
    // Get form fields
    const formFields = {
      // Basic Campaign Information
      "campaign_name": {
        "required": true,
        "type": "string",
        "description": "Enter a unique name for your campaign"
      },
      // ... more fields
    };
    
    // Prepare conversation history for Groq
    const conversationHistory = chatHistory[req.user.id].map(msg => ({
      role: msg.role,
      content: msg.content
    }));
    
    // Add system message at the beginning
    conversationHistory.unshift({
      role: 'system',
      content: `You are an AI assistant helping users fill out an advertising campaign form. Your job is to:
      
      1. Extract structured data from natural language input
      2. Ask about required fields that haven't been provided yet
      3. Validate the information provided by the user
      4. Provide helpful suggestions based on the user's campaign goals
      
      Current form data: ${JSON.stringify(formData)}.
      
      Form fields: ${JSON.stringify(formFields)}.
      
      When you extract values, respond with a JSON object containing the extracted field names and values, but DO NOT include the JSON in your visible response. Instead, place the JSON at the end of your message surrounded by <json></json> tags so it can be parsed programmatically but not displayed to the user.
      
      In your responses:
      1. Be conversational and helpful
      2. If the user hasn't provided all required fields, ask for the missing information
      3. Provide suggestions based on the information provided (e.g., if they mention a specific goal, suggest appropriate targeting options)
      4. Confirm the information you've extracted
      5. When all required fields are filled, let the user know their form is complete
      
      Required fields that need to be collected:
      - campaign_name
      - account
      - start_date
      - end_date
      - network
      - campaign_goal
      - targeting_type
      - iab_category
      - target_device_type
      - media_type
      - pricing_type
      - budget
      - advertiser_domain
      `
    });
    
    // Call Groq API
    const completion = await groq.chat.completions.create({
      messages: conversationHistory,
      model: "llama-3.3-70b-versatile",
    });
    
    let aiResponse = completion.choices[0]?.message?.content || "I couldn't process that request.";
    
    // Try to parse JSON from the response if it contains any
    let extractedData = {};
    try {
      // Look for JSON in the response between <json></json> tags
      const jsonMatch = aiResponse.match(/<json>(.*?)<\/json>/s);
      if (jsonMatch) {
        const jsonStr = jsonMatch[1];
        const parsed = JSON.parse(jsonStr);
        extractedData = parsed;
        
        // Remove the JSON tags and content from the response
        aiResponse = aiResponse.replace(/<json>.*?<\/json>/s, '');
      } else {
        // Fallback to the old method if tags aren't found
        const jsonMatch = aiResponse.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const jsonStr = jsonMatch[0];
          const parsed = JSON.parse(jsonStr);
          extractedData = parsed;
          
          // Remove the JSON from the response
          aiResponse = aiResponse.replace(/\{[\s\S]*\}/, '');
        }
      }
      
      // Clean up the response
      aiResponse = aiResponse.trim();
      
      // Add a user-friendly message about what was updated
      if (Object.keys(extractedData).length > 0) {
        const fieldNames = Object.keys(extractedData).map(key => 
          key.replace(/_/g, ' ')
        );
        
        if (fieldNames.length === 1) {
          aiResponse += `\n\nI've updated the ${fieldNames[0]} field in your form.`;
        } else if (fieldNames.length > 1) {
          const lastField = fieldNames.pop();
          aiResponse += `\n\nI've updated the following fields in your form: ${fieldNames.join(', ')} and ${lastField}.`;
        }
      }
    } catch (error) {
      console.error('Error parsing JSON from AI response:', error);
    }
    
    // Add AI response to history
    chatHistory[req.user.id].push({ role: 'assistant', content: aiResponse });
    
    // If data was extracted, update the form
    if (Object.keys(extractedData).length > 0) {
      if (userForm) {
        userForm.data = { ...userForm.data, ...extractedData };
      } else {
        forms.push({
          userId: req.user.id,
          data: extractedData
        });
      }
    }
    
    res.json({
      reply: aiResponse,
      extractedData,
      updatedFormData: userForm ? userForm.data : extractedData
    });
  } catch (error) {
    console.error('Error processing chat message:', error);
    res.status(500).json({ message: error.message });
  }
});

module.exports = router;