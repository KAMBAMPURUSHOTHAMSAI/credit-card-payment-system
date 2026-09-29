import { useEffect, useState } from "react";

import Navbar from "../components/Navbar";
import { djangoApi } from "../api";


function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);


  useEffect(() => {
    const loadSummary = async () => {
      setLoading(true);
      setError("");

      try {
        const response =
          await djangoApi.get(
            "/admin/dashboard/"
          );

        setSummary(
          response.data
        );
      } catch (error) {
        if (
          error.response?.status === 403
        ) {
          setError(
            "You do not have permission to access the admin dashboard."
          );
        } else {
          setError(
            "Unable to load admin dashboard."
          );
        }
      } finally {
        setLoading(false);
      }
    };

    loadSummary();
  }, []);


  const handleExport = async () => {
    try {
      const response =
        await djangoApi.get(
          "/admin/transactions/export/",
          {
            responseType: "blob",
          }
        );

      const blob =
        new Blob(
          [response.data],
          {
            type: "text/csv",
          }
        );

      const url =
        window.URL.createObjectURL(
          blob
        );

      const link =
        document.createElement("a");

      link.href = url;

      link.download =
        "transactions.csv";

      document.body.appendChild(
        link
      );

      link.click();

      link.remove();

      window.URL.revokeObjectURL(
        url
      );

    } catch (error) {
      setError(
        "Unable to export transactions."
      );
    }
  };


  return (
    <div className="min-h-screen bg-slate-100">

      <Navbar />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">

        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">

          <div>
            <h1 className="text-3xl font-bold text-slate-900">
              Admin Dashboard
            </h1>

            <p className="mt-2 text-slate-600">
              Monitor today's payment activity.
            </p>
          </div>

          <button
            type="button"
            onClick={handleExport}
            className="rounded-lg bg-slate-900 px-5 py-3 font-semibold text-white hover:bg-slate-800"
          >
            Export Transactions CSV
          </button>

        </div>


        {error && (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            {error}
          </div>
        )}


        {loading ? (
          <div className="mt-8 rounded-xl bg-white p-10 text-center shadow-sm">
            <p className="text-slate-500">
              Loading admin dashboard...
            </p>
          </div>
        ) : summary ? (
          <>

            <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">

              <div className="rounded-xl bg-white p-6 shadow-sm">
                <p className="text-sm text-slate-500">
                  Total Transactions
                </p>

                <p className="mt-2 text-3xl font-bold text-slate-900">
                  {summary.total_transactions}
                </p>
              </div>


              <div className="rounded-xl bg-white p-6 shadow-sm">
                <p className="text-sm text-slate-500">
                  Total Amount
                </p>

                <p className="mt-2 text-3xl font-bold text-blue-600">
                  ₹{summary.total_amount}
                </p>
              </div>


              <div className="rounded-xl bg-white p-6 shadow-sm">
                <p className="text-sm text-slate-500">
                  Successful
                </p>

                <p className="mt-2 text-3xl font-bold text-green-600">
                  {summary.success_count}
                </p>
              </div>


              <div className="rounded-xl bg-white p-6 shadow-sm">
                <p className="text-sm text-slate-500">
                  Failed
                </p>

                <p className="mt-2 text-3xl font-bold text-red-600">
                  {summary.failed_count}
                </p>
              </div>


              <div className="rounded-xl bg-white p-6 shadow-sm">
                <p className="text-sm text-slate-500">
                  Pending
                </p>

                <p className="mt-2 text-3xl font-bold text-yellow-600">
                  {summary.pending_count}
                </p>
              </div>

            </div>


            <div className="mt-8 rounded-xl bg-white p-6 shadow-sm">

              <h2 className="text-xl font-bold text-slate-900">
                Daily Payment Summary
              </h2>

              <p className="mt-2 text-slate-500">
                Summary for {summary.date}
              </p>

              <div className="mt-6 h-3 overflow-hidden rounded-full bg-slate-200">

                <div
                  className="h-full bg-green-500"
                  style={{
                    width:
                      summary.total_transactions > 0
                        ? `${(
                            summary.success_count /
                            summary.total_transactions
                          ) * 100}%`
                        : "0%",
                  }}
                />

              </div>

            </div>

          </>
        ) : null}

      </main>

    </div>
  );
}


export default AdminDashboard;