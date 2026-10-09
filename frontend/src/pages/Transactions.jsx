
import { useCallback, useEffect, useState } from "react";

import Navbar from "../components/Navbar";
import { djangoApi } from "../api";

const INITIAL_FILTERS = {
  status: "",
  start_date: "",
  end_date: "",
  min_amount: "",
  max_amount: "",
  card_search: "",
  ordering: "-created_at",
};

const DEFAULT_PAGE_SIZE = 10;

function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [filters, setFilters] = useState({ ...INITIAL_FILTERS });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const pageCount = Math.max(
    1,
    Math.ceil(totalCount / pageSize)
  );

  const loadTransactions = useCallback(
    async (currentFilters, requestedPage, requestedPageSize) => {
      setLoading(true);
      setError("");
      setCurrentPage(requestedPage);

      try {
        const params = {
          page: requestedPage,
          page_size: requestedPageSize,
          ordering: currentFilters.ordering || "-created_at",
        };

        [
          "status",
          "start_date",
          "end_date",
          "min_amount",
          "max_amount",
          "card_search",
        ].forEach((key) => {
          const value = currentFilters[key];

          if (value !== undefined && String(value).trim() !== "") {
            params[key] = String(value).trim();
          }
        });

        const response = await djangoApi.get(
          "/transactions/",
          { params }
        );

        // Supports the existing list response and the
        // paginated Django REST Framework response.
        const responseData = response.data;

        const results = Array.isArray(responseData)
          ? responseData
          : Array.isArray(responseData?.results)
            ? responseData.results
            : [];

        const count = Array.isArray(responseData)
          ? results.length
          : Number(
              responseData?.count ??
              responseData?.total_count ??
              results.length
            );

        setTransactions(results);
        setTotalCount(Number.isFinite(count) ? count : results.length);
      } catch {
        setTransactions([]);
        setTotalCount(0);
        setError("Unable to load transactions. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    loadTransactions(
      INITIAL_FILTERS,
      1,
      DEFAULT_PAGE_SIZE
    );
  }, [loadTransactions]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFilters((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleFilter = async (event) => {
    event.preventDefault();

    if (
      filters.min_amount !== "" &&
      filters.max_amount !== "" &&
      Number(filters.min_amount) > Number(filters.max_amount)
    ) {
      setError("Minimum amount cannot exceed maximum amount.");
      return;
    }

    if (
      filters.start_date &&
      filters.end_date &&
      filters.start_date > filters.end_date
    ) {
      setError("From Date cannot be after To Date.");
      return;
    }

    await loadTransactions(filters, 1, pageSize);
  };

  const handleReset = async () => {
    const emptyFilters = { ...INITIAL_FILTERS };

    setFilters(emptyFilters);

    await loadTransactions(
      emptyFilters,
      1,
      pageSize
    );
  };

  const handlePageSizeChange = async (event) => {
    const newPageSize = Number(event.target.value);

    if (!Number.isInteger(newPageSize) || newPageSize < 1) {
      return;
    }

    setPageSize(newPageSize);

    await loadTransactions(
      filters,
      1,
      newPageSize
    );
  };

  const handlePageChange = async (newPage) => {
    if (loading || newPage < 1 || newPage > pageCount) {
      return;
    }

    await loadTransactions(
      filters,
      newPage,
      pageSize
    );
  };

  const getStatusClasses = (status) => {
    if (status === "SUCCESS") {
      return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300";
    }

    if (status === "FAILED") {
      return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300";
    }

    return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300";
  };

  const getFraudClasses = (fraudStatus) => {
    if (fraudStatus === "FLAGGED") {
      return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300";
    }

    if (fraudStatus === "CLEAR") {
      return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300";
    }

    return "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300";
  };

  const inputClasses =
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-400 dark:focus:ring-blue-900/30";

  const labelClasses =
    "mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300";

  const firstRow = totalCount === 0
    ? 0
    : (currentPage - 1) * pageSize + 1;

  const lastRow = Math.min(
    currentPage * pageSize,
    totalCount
  );

  return (
    <div className="theme-transition min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <Navbar />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            Transaction History
          </h1>

          <p className="mt-2 text-slate-600 dark:text-slate-400">
            Search, sort, and filter your payment transactions.
          </p>
        </div>

        {error && (
          <div
            role="alert"
            className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300"
          >
            {error}
          </div>
        )}

        <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">
            Search & Filters
          </h2>

          <form
            onSubmit={handleFilter}
            className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            <div>
              <label htmlFor="card_search" className={labelClasses}>
                Masked Card Search
              </label>

              <input
                id="card_search"
                name="card_search"
                type="text"
                value={filters.card_search}
                onChange={handleChange}
                placeholder="e.g. ****1234"
                maxLength={20}
                className={inputClasses}
              />
            </div>

            <div>
              <label htmlFor="status" className={labelClasses}>
                Transaction Status
              </label>

              <select
                id="status"
                name="status"
                value={filters.status}
                onChange={handleChange}
                className={inputClasses}
              >
                <option value="">All Statuses</option>
                <option value="SUCCESS">Success</option>
                <option value="FAILED">Failed</option>
                <option value="PENDING">Pending</option>
              </select>
            </div>

            <div>
              <label htmlFor="ordering" className={labelClasses}>
                Sort By
              </label>

              <select
                id="ordering"
                name="ordering"
                value={filters.ordering}
                onChange={handleChange}
                className={inputClasses}
              >
                <option value="-created_at">Newest First</option>
                <option value="created_at">Oldest First</option>
                <option value="-amount">Amount: High to Low</option>
                <option value="amount">Amount: Low to High</option>
                <option value="status">Status</option>
              </select>
            </div>

            <div>
              <label htmlFor="start_date" className={labelClasses}>
                From Date
              </label>

              <input
                id="start_date"
                name="start_date"
                type="date"
                value={filters.start_date}
                onChange={handleChange}
                className={inputClasses}
              />
            </div>

            <div>
              <label htmlFor="end_date" className={labelClasses}>
                To Date
              </label>

              <input
                id="end_date"
                name="end_date"
                type="date"
                value={filters.end_date}
                onChange={handleChange}
                className={inputClasses}
              />
            </div>

            <div>
              <label htmlFor="min_amount" className={labelClasses}>
                Minimum Amount
              </label>

              <input
                id="min_amount"
                name="min_amount"
                type="number"
                min="0"
                step="0.01"
                value={filters.min_amount}
                onChange={handleChange}
                placeholder="0.00"
                className={inputClasses}
              />
            </div>

            <div>
              <label htmlFor="max_amount" className={labelClasses}>
                Maximum Amount
              </label>

              <input
                id="max_amount"
                name="max_amount"
                type="number"
                min="0"
                step="0.01"
                value={filters.max_amount}
                onChange={handleChange}
                placeholder="1000000.00"
                className={inputClasses}
              />
            </div>

            <div>
              <label htmlFor="page_size" className={labelClasses}>
                Rows Per Page
              </label>

              <select
                id="page_size"
                value={pageSize}
                onChange={handlePageSizeChange}
                className={inputClasses}
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
            </div>

            <div className="flex flex-wrap items-end gap-3">
              <button
                type="submit"
                disabled={loading}
                className="rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-slate-800"
              >
                Apply Filters
              </button>

              <button
                type="button"
                onClick={handleReset}
                disabled={loading}
                className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                Reset
              </button>
            </div>
          </form>
        </div>

        <div className="mt-8 rounded-xl bg-white shadow-sm dark:bg-slate-800">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 px-6 py-4 dark:border-slate-700">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                Transactions
              </h2>

              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                {totalCount} transaction(s) found
              </p>
            </div>

            <p className="text-sm text-slate-500 dark:text-slate-400">
              Showing {firstRow}–{lastRow} of {totalCount}
            </p>
          </div>

          {loading ? (
            <div className="px-6 py-12 text-center">
              <p className="text-slate-500 dark:text-slate-400">
                Loading transactions...
              </p>
            </div>
          ) : transactions.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <p className="text-slate-500 dark:text-slate-400">
                No transactions found.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                  <tr>
                    <th className="whitespace-nowrap px-5 py-3 font-medium">
                      Reference
                    </th>
                    <th className="whitespace-nowrap px-5 py-3 font-medium">
                      Card
                    </th>
                    <th className="whitespace-nowrap px-5 py-3 font-medium">
                      Amount
                    </th>
                    <th className="whitespace-nowrap px-5 py-3 font-medium">
                      Status
                    </th>
                    <th className="whitespace-nowrap px-5 py-3 font-medium">
                      Fraud Status
                    </th>
                    <th className="whitespace-nowrap px-5 py-3 font-medium">
                      Description
                    </th>
                    <th className="whitespace-nowrap px-5 py-3 font-medium">
                      Date
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {transactions.map((transaction) => (
                    <tr
                      key={transaction.id}
                      className="border-t border-slate-100 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-900/60"
                    >
                      <td className="whitespace-nowrap px-5 py-4 font-medium text-slate-900 dark:text-white">
                        {transaction.reference}
                      </td>

                      <td className="whitespace-nowrap px-5 py-4 text-slate-600 dark:text-slate-300">
                        {transaction.card_number || "—"}
                      </td>

                      <td className="whitespace-nowrap px-5 py-4 font-medium text-slate-700 dark:text-slate-200">
                        {transaction.amount} {transaction.currency}
                      </td>

                      <td className="whitespace-nowrap px-5 py-4">
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${getStatusClasses(
                            transaction.status
                          )}`}
                        >
                          {transaction.status}
                        </span>
                      </td>

                      <td className="whitespace-nowrap px-5 py-4">
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${getFraudClasses(
                            transaction.fraud_status
                          )}`}
                        >
                          {transaction.fraud_status || "NOT_CHECKED"}
                        </span>
                      </td>

                      <td className="px-5 py-4 text-slate-600 dark:text-slate-300">
                        {transaction.description || "—"}
                      </td>

                      <td className="whitespace-nowrap px-5 py-4 text-slate-500 dark:text-slate-400">
                        {transaction.created_at
                          ? new Date(
                              transaction.created_at
                            ).toLocaleString()
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-6 py-4 dark:border-slate-700">
            <button
              type="button"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={loading || currentPage <= 1}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              Previous
            </button>

            <span className="text-sm text-slate-600 dark:text-slate-300">
              Page {currentPage} of {pageCount}
            </span>

            <button
              type="button"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={loading || currentPage >= pageCount}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              Next
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Transactions;
