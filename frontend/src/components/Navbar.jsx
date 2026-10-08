import { Link, useNavigate } from "react-router-dom";
import { djangoApi } from "../api";
import { useTheme } from "../context/ThemeContext";


function Navbar() {
  const navigate = useNavigate();

  const {
    theme,
    toggleTheme,
  } = useTheme();


  const isAdmin =
    localStorage.getItem("is_admin")
    === "true";


  const handleLogout = async () => {
    const refreshToken =
      localStorage.getItem("refresh_token");

    try {
      if (refreshToken) {
        await djangoApi.post(
          "/auth/logout/",
          {
            refresh: refreshToken,
          }
        );
      }
    } catch (error) {
      // Always clear local session.
    } finally {
      localStorage.removeItem(
        "access_token"
      );

      localStorage.removeItem(
        "refresh_token"
      );

      localStorage.removeItem(
        "is_admin"
      );

      navigate("/login", {
        replace: true,
      });
    }
  };


  const isDark =
    theme === "dark";


  return (
    <nav className="border-b border-slate-200 bg-white shadow-sm transition-colors duration-200 dark:border-slate-700 dark:bg-slate-900">

      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">

        <Link
          to="/dashboard"
          className="text-xl font-bold text-blue-600"
        >
          CreditPay
        </Link>


        <div className="flex flex-wrap items-center justify-end gap-3 text-sm font-medium sm:gap-5">

          <Link
            to="/dashboard"
            className="text-slate-700 transition-colors hover:text-blue-600 dark:text-slate-200 dark:hover:text-blue-400"
          >
            Dashboard
          </Link>


          <Link
            to="/cards/add"
            className="text-slate-700 transition-colors hover:text-blue-600 dark:text-slate-200 dark:hover:text-blue-400"
          >
            Add Card
          </Link>


          <Link
            to="/payment"
            className="text-slate-700 transition-colors hover:text-blue-600 dark:text-slate-200 dark:hover:text-blue-400"
          >
            Make Payment
          </Link>


          <Link
            to="/transactions"
            className="text-slate-700 transition-colors hover:text-blue-600 dark:text-slate-200 dark:hover:text-blue-400"
          >
            Transactions
          </Link>


          {isAdmin && (
            <Link
              to="/admin"
              className="font-semibold text-purple-600 transition-colors hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300"
            >
              Admin Dashboard
            </Link>
          )}


          <button
            type="button"
            onClick={toggleTheme}
            aria-label={
              isDark
                ? "Switch to light mode"
                : "Switch to dark mode"
            }
            aria-pressed={isDark}
            title={
              isDark
                ? "Switch to light mode"
                : "Switch to dark mode"
            }
            className="rounded-lg border border-slate-300 bg-slate-100 px-3 py-2 text-base text-slate-700 transition-colors duration-200 hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 dark:focus:ring-offset-slate-900"
          >
            {isDark ? "☀️" : "🌙"}
          </button>


          <button
            type="button"
            onClick={handleLogout}
            className="rounded-lg bg-slate-900 px-4 py-2 text-white transition-colors duration-200 hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white dark:focus:ring-offset-slate-900"
          >
            Logout
          </button>

        </div>

      </div>

    </nav>
  );
}

export default Navbar;