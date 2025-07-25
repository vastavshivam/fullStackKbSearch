import React from 'react';
import { Navigate } from 'react-router-dom';

interface PrivateRouteProps {
  children: React.ReactNode;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const token = localStorage.getItem('token'); // Token from localStorage

  return token ? <>{children}</> : <Navigate to="/login" replace />;
};

export default PrivateRoute;
