const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

// Register a new user
router.post('/register', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    // Check if user already exists
    const users = req.app.locals.users;
    const userExists = users.find(user => user.username === username);
    
    if (userExists) {
      return res.status(400).json({ message: 'User already exists' });
    }
    
    // Hash password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    
    // Create new user
    const newUser = {
      id: Date.now().toString(),
      username,
      password: hashedPassword
    };
    
    // Save user
    users.push(newUser);
    
    // Create and assign token using default secret if JWT_SECRET is not provided
    const token = jwt.sign(
      { id: newUser.id }, 
      process.env.JWT_SECRET || 'default-dev-secret', 
      { expiresIn: '1h' }
    );
    
    res.status(201).json({ token, user: { id: newUser.id, username } });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Login user
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    // Find user
    const users = req.app.locals.users;
    const user = users.find(user => user.username === username);
    
    if (!user) {
      return res.status(400).json({ message: 'Invalid credentials' });
    }
    
    // Validate password
    const validPassword = await bcrypt.compare(password, user.password);
    if (!validPassword) {
      return res.status(400).json({ message: 'Invalid credentials' });
    }
    
    // Create and assign token using default secret if JWT_SECRET is not provided
    const token = jwt.sign(
      { id: user.id }, 
      process.env.JWT_SECRET || 'default-dev-secret', 
      { expiresIn: '1h' }
    );
    
    res.status(200).json({ token, user: { id: user.id, username } });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

module.exports = router;