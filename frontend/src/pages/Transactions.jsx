import { useEffect, useState } from "react";

import Navbar from "../components/Navbar";
import { djangoApi } from "../api";


function Transactions() {
  const [transactions, setTransactions] = useState([]);

  const [filters, setFilters] = useState({
    status: "",
    start_date: "",
    end_date: "",
    min_amount: "",
    max_amount: "",
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  const loadTransactions = async (
    currentFilters = filters
  ) => {
    setLoading(true);
    setError("");

    try {
      const params = {};

      if (currentFilters.status) {
        params.status =
          currentFilters.status;
      }

      if (currentFilters.start_date) {
        params.start_date =
          currentFilters.start_date;
      }

      if (currentFilters.end_date) {
        params.end_date =
          currentFilters.end_date;
      }

      if (currentFilters.min_amount) {
        params.min_amount =
          currentFilters.min_amount;
      }

      if (currentFilters.max_amount) {
        params.max_amount =
          currentFilters.max_amount;
      }

      const response =
        await djangoApi.get(
          "/transactions/",
          {
            params,
          }
        );

      setTransactions(
        response.data || []
      );

    } catch (error) {
      setError(
        "Unable to load transactions."
      );
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadTransactions();
  }, []);


  const handleChange = (event) => {
    const {
      name,
      value,
    } = event.target;

    setFilters(
      (previous) => ({
        ...previous,
        [name]: value,
      })
    );
  };


  const handleFilter = async (
    event
  ) => {
    event.preventDefault();

    await loadTransactions(
      filters
    );
  };


  const handleReset = async () => {
    const emptyFilters = {
      status: "",
      start_date: "",
      end_date: "",
      min_amount: "",
      max_amount: "",
    };

    setFilters(emptyFilters);

    await loadTransactions(
      emptyFilters
    );
  };


  const getStatusClasses = (
    status
  ) => {
    if (status === "SUCCESS") {
      return "bg-green-100 text-green-700";
    }

    if (status === "FAILED") {
      return "bg-red-100 text-red-700";
    }

    return "bg-yellow-100 text-yellow-700";
  };


  return (
    <div className="min-h-screen bg-slate-100">

      <Navbar />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">

        <div className="mb-8">

          <h1 className="text-3xl font-bold text-slate-900">
            Transaction History
          </h1>

          <p className="mt-2 text-slate-600">
            View and filter your payment transactions.
          </p>

        </div>


        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            {error}
          </div>
        )}


        {/* FILTERS */}

        <div className="rounded-xl bg-white p-6 shadow-sm">

          <h2 className="text-lg font-bold text-slate-900">
            Filters
          </h2>

          <form
            onSubmit={handleFilter}
            className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5"
          >

            <div>
              <label
                htmlFor="status"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Status
              </label>

              <select
                id="status"
                name="status"
                value={filters.status}
                onChange={handleChange}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              >
                <option value="">
                  All Statuses
                </option>

                <option value="SUCCESS">
                  Success
                </option>

                <option value="FAILED">
                  Failed
                </option>

                <option value="PENDING">
                  Pending
                </option>
              </select>
            </div>


            <div>
              <label
                htmlFor="start_date"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                From Date
              </label>

              <input
                id="start_date"
                name="start_date"
                type="date"
                value={filters.start_date}
                onChange={handleChange}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </div>


            <div>
              <label
                htmlFor="end_date"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                To Date
              </label>

              <input
                id="end_date"
                name="end_date"
                type="date"
                value={filters.end_date}
                onChange={handleChange}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </div>


            <div>
              <label
                htmlFor="min_amount"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Min Amount
              </label>

              <input
                id="min_amount"
                name="min_amount"
                type="number"
                min="0"
                step="0.01"
                value={filters.min_amount}
                onChange={handleChange}
                placeholder="0"
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </div>


            <div>
              <label
                htmlFor="max_amount"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Max Amount
              </label>

              <input
                id="max_amount"
                name="max_amount"
                type="number"
                min="0"
                step="0.01"
                value={filters.max_amount}
                onChange={handleChange}
                placeholder="1000000"
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </div>


            <div className="md:col-span-2 lg:col-span-5 flex flex-wrap gap-3">

              <button
                type="submit"
                className="rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white hover:bg-blue-700"
              >
                Apply Filters
              </button>

              <button
                type="button"
                onClick={handleReset}
                className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 font-semibold text-slate-700 hover:bg-slate-50"
              >
                Reset
              </button>

            </div>

          </form>

        </div>


        {/* TRANSACTIONS */}

        <div className="mt-8 rounded-xl bg-white shadow-sm">

          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">

            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Transactions
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                {transactions.length} transaction(s)
              </p>
            </div>

          </div>


          {loading ? (
            <div className="px-6 py-12 text-center">
              <p className="text-slate-500">
                Loading transactions...
              </p>
            </div>
          ) : transactions.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <p className="text-slate-500">
                No transactions found.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">

              <table className="min-w-full text-left text-sm">

                <thead className="bg-slate-50 text-slate-500">

                  <tr>

                    <th className="px-6 py-3 font-medium">
                      Reference
                    </th>

                    <th className="px-6 py-3 font-medium">
                      Card
                    </th>

                    <th className="px-6 py-3 font-medium">
                      Amount
                    </th>

                    <th className="px-6 py-3 font-medium">
                      Status
                    </th>

                    <th className="px-6 py-3 font-medium">
                      Description
                    </th>

                    <th className="px-6 py-3 font-medium">
                      Date
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {transactions.map(
                    (transaction) => (
                      <tr
                        key={transaction.id}
                        className="border-t border-slate-100"
                      >

                        <td className="px-6 py-4 font-medium text-slate-900">
                          {transaction.reference}
                        </td>


                        <td className="px-6 py-4 text-slate-600">
                          {transaction.card_number}
                        </td>


                        <td className="px-6 py-4 font-medium text-slate-700">
                          {transaction.amount}{" "}
                          {transaction.currency}
                        </td>


                        <td className="px-6 py-4">

                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${getStatusClasses(
                              transaction.status
                            )}`}
                          >
                            {transaction.status}
                          </span>

                        </td>


                        <td className="px-6 py-4 text-slate-600">
                          {transaction.description ||
                            "—"}
                        </td>


                        <td className="px-6 py-4 text-slate-500">
                          {new Date(
                            transaction.created_at
                          ).toLocaleString()}
                        </td>

                      </tr>
                    )
                  )}

                </tbody>

              </table>

            </div>
          )}

        </div>

      </main>

    </div>
  );
}


export default Transactions;