import { Navigate } from "react-router-dom";


function ProtectedRoute({
  children,
  adminOnly = false,
}) {
  const token =
    localStorage.getItem(
      "access_token"
    );

  const isAdmin =
    localStorage.getItem(
      "is_admin"
    ) === "true";


  if (!token) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }


  if (
    adminOnly &&
    !isAdmin
  ) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }


  return children;
}


export default ProtectedRoute;