import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/AppLayout';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import RequesterHomePage from './pages/RequesterHomePage';
import FinanceHomePage from './pages/FinanceHomePage';

function HomeRedirect() {
  const { user } = useAuth();
  return <Navigate to={user?.role === 'finance' ? '/finance/pending' : '/my-requests'} replace />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route element={<AppLayout />}>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <HomeRedirect />
            </ProtectedRoute>
          }
        />
        <Route
          path="/my-requests"
          element={
            <ProtectedRoute>
              <RequesterHomePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/finance/pending"
          element={
            <ProtectedRoute requireRole="finance">
              <FinanceHomePage />
            </ProtectedRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;
