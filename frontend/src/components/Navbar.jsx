import { Link, useNavigate } from "react-router-dom";
import { djangoApi } from "../api";


function Navbar() {
  const navigate = useNavigate();

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


  return (
    <nav className="border-b border-slate-200 bg-white shadow-sm">

      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">

        <Link
          to="/dashboard"
          className="text-xl font-bold text-blue-600"
        >
          CreditPay
        </Link>


        <div className="flex items-center gap-5 text-sm font-medium">

          <Link
            to="/dashboard"
            className="text-slate-700 hover:text-blue-600"
          >
            Dashboard
          </Link>


          <Link
            to="/cards/add"
            className="text-slate-700 hover:text-blue-600"
          >
            Add Card
          </Link>


          <Link
            to="/payment"
            className="text-slate-700 hover:text-blue-600"
          >
            Make Payment
          </Link>


          <Link
            to="/transactions"
            className="text-slate-700 hover:text-blue-600"
          >
            Transactions
          </Link>


          {isAdmin && (
            <Link
              to="/admin"
              className="font-semibold text-purple-600 hover:text-purple-700"
            >
              Admin Dashboard
            </Link>
          )}


          <button
            type="button"
            onClick={handleLogout}
            className="rounded-lg bg-slate-900 px-4 py-2 text-white transition hover:bg-slate-700"
          >
            Logout
          </button>

        </div>

      </div>

    </nav>
  );
}

export default Navbar;