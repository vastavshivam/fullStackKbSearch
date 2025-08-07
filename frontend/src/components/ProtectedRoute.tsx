import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
  requireAuth?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  allowedRoles = [], 
  requireAuth = true 
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  // Show loading while checking authentication
  if (isLoading) {
    return <div>Loading...</div>;
  }

  // Check if authentication is required
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // Check if user has the required role
  if (allowedRoles.length > 0 && user && !allowedRoles.includes(user.role)) {
    // Redirect based on user's role
    if (user.role === 'user') {
      return <Navigate to="/user-dashboard" replace />;
    } else if (user.role === 'admin') {
      return <Navigate to="/dashboard" replace />;
    }
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
