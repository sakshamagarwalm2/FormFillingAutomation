const jwt = require('jsonwebtoken');

module.exports = function(req, res, next) {
  // DEVELOPMENT MODE: Bypass authentication
  const bypassAuth = true; // Set to true to bypass authentication
  
  if (bypassAuth) {
    // Set a dummy user ID for development
    req.user = { id: 'dev-user-123' };
    return next();
  }
  
  // Get token from header
  const token = req.header('x-auth-token');
  
  // Check if no token
  if (!token) {
    return res.status(401).json({ message: 'No token, authorization denied' });
  }
  
  // Verify token
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'default-dev-secret');
    req.user = { id: decoded.id };
    next();
  } catch (error) {
    res.status(401).json({ message: 'Token is not valid' });
  }
};