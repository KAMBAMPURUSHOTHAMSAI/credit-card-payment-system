import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { djangoApi } from "../api";


function Login() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);


  const handleChange = (event) => {
    const {
      name,
      value,
    } = event.target;

    setFormData(
      (previous) => ({
        ...previous,
        [name]: value,
      })
    );
  };


  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      // =================================================
      // 1. LOGIN
      // =================================================

      const response =
        await djangoApi.post(
          "/auth/login/",
          formData
        );

      const {
        access,
        refresh,
      } = response.data;


      // =================================================
      // 2. STORE JWT TOKENS
      // =================================================

      localStorage.setItem(
        "access_token",
        access
      );

      localStorage.setItem(
        "refresh_token",
        refresh
      );


      // Remove old admin state first.
      localStorage.removeItem(
        "is_admin"
      );


      // =================================================
      // 3. CHECK ADMIN ACCESS
      // =================================================

      try {
        await djangoApi.get(
          "/admin/dashboard/"
        );

        // 200 means the logged-in user
        // has admin permission.
        localStorage.setItem(
          "is_admin",
          "true"
        );

      } catch (adminError) {

        if (
          adminError.response?.status ===
          403
        ) {
          // Normal authenticated user.
          localStorage.setItem(
            "is_admin",
            "false"
          );

        } else {
          // Any other admin-check error:
          // keep user logged in but don't
          // expose the admin UI.
          localStorage.setItem(
            "is_admin",
            "false"
          );
        }
      }


      // =================================================
      // 4. GO TO DASHBOARD
      // =================================================

      navigate(
        "/dashboard",
        {
          replace: true,
        }
      );

    } catch (error) {

      const message =
        error.response?.data?.detail ||
        "Invalid username or password.";

      setError(message);

      // Clear any incomplete session.
      localStorage.removeItem(
        "access_token"
      );

      localStorage.removeItem(
        "refresh_token"
      );

      localStorage.removeItem(
        "is_admin"
      );

    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center px-4">

      <div className="w-full max-w-md">

        <div className="bg-white rounded-2xl shadow-lg p-8">

          <div className="text-center mb-8">

            <h1 className="text-3xl font-bold text-slate-900">
              CreditPay
            </h1>

            <p className="text-slate-500 mt-2">
              Sign in to your account
            </p>

          </div>


          {error && (
            <div className="mb-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}


          <form
            onSubmit={handleSubmit}
            className="space-y-5"
          >

            <div>

              <label
                htmlFor="username"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Username
              </label>

              <input
                id="username"
                name="username"
                type="text"
                value={formData.username}
                onChange={handleChange}
                required
                autoComplete="username"
                placeholder="Enter your username"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />

            </div>


            <div>

              <label
                htmlFor="password"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Password
              </label>

              <input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                required
                autoComplete="current-password"
                placeholder="Enter your password"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />

            </div>


            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading
                ? "Signing in..."
                : "Sign In"}
            </button>

          </form>


          <div className="mt-6 text-center text-sm text-slate-600">

            Don't have an account?{" "}

            <Link
              to="/register"
              className="font-semibold text-blue-600 hover:text-blue-700"
            >
              Create account
            </Link>

          </div>

        </div>

      </div>

    </div>
  );
}


export default Login;