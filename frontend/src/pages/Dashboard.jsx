import { useEffect, useState } from "react";

import { Link } from "react-router-dom";

import Navbar from "../components/Navbar";

import {
  djangoApi,
  fastApi,
} from "../api";


function formatCurrency(value) {
  const amount = Number(value || 0);

  return amount.toLocaleString(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }
  );
}


function formatDate(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }
  );
}


function getStatusClass(status) {
  if (status === "SUCCESS") {
    return "rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700 dark:bg-green-900/30 dark:text-green-300";
  }

  if (status === "FAILED") {
    return "rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700 dark:bg-red-900/30 dark:text-red-300";
  }

  return "rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300";
}


function StatSkeleton() {
  return (
    <div className="animate-pulse rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">
      <div className="h-4 w-28 rounded bg-slate-200 dark:bg-slate-700" />

      <div className="mt-4 h-9 w-36 rounded bg-slate-200 dark:bg-slate-700" />

      <div className="mt-3 h-3 w-24 rounded bg-slate-100 dark:bg-slate-700" />
    </div>
  );
}


function getCurrentMonthValue() {
  const today = new Date();

  const month = String(
    today.getMonth() + 1
  ).padStart(2, "0");

  return `${today.getFullYear()}-${month}`;
}


function Dashboard() {
  const [cards, setCards] = useState([]);

  const [dashboardSummary, setDashboardSummary] = useState({
    total_transactions: 0,
    total_amount_spent: 0,
    current_month_spending: 0,
    available_credit_limit: 0,
    last_5_transactions: [],
  });

  const [transactions, setTransactions] = useState([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [isJwtError, setIsJwtError] = useState(false);

  const [statementMonth, setStatementMonth] =
    useState(getCurrentMonthValue());

  const [statementLoading, setStatementLoading] =
    useState(false);

  const [statementError, setStatementError] =
    useState("");


  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError("");
      setIsJwtError(false);

      try {
        const [
          cardsResponse,
          transactionsResponse,
          dashboardResponse,
        ] = await Promise.all([
          djangoApi.get("/cards/"),
          djangoApi.get("/transactions/"),
          fastApi.get("/dashboard/summary"),
        ]);

        setCards(
          cardsResponse.data || []
        );

        setTransactions(
          transactionsResponse.data || []
        );

        setDashboardSummary(
          dashboardResponse.data || {
            total_transactions: 0,
            total_amount_spent: 0,
            current_month_spending: 0,
            available_credit_limit: 0,
            last_5_transactions: [],
          }
        );
      } catch (error) {
        const status =
          error.response?.status;

        if (
          status === 401 ||
          status === 403
        ) {
          setIsJwtError(true);

          setError(
            "Your session has expired or the JWT token is invalid. Please log in again."
          );
        } else {
          setError(
            "Unable to load dashboard data. Please try again."
          );
        }
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);


  const recentTransactions =
    dashboardSummary.last_5_transactions || [];


  const successfulPayments =
    transactions.filter(
      (transaction) =>
        transaction.status === "SUCCESS"
    ).length;


  const failedPayments =
    transactions.filter(
      (transaction) =>
        transaction.status === "FAILED"
    ).length;


  const handleDownloadStatement = async () => {
    if (!statementMonth) {
      setStatementError(
        "Please select a statement month."
      );

      return;
    }

    const [
      selectedYear,
      selectedMonth,
    ] = statementMonth.split("-");

    setStatementLoading(true);
    setStatementError("");

    try {
      const response = await djangoApi.get(
        "/transactions/statement/",
        {
          params: {
            year: selectedYear,
            month: selectedMonth,
          },
          responseType: "blob",
        }
      );

      const blob = new Blob(
        [response.data],
        {
          type:
            "application/pdf",
        }
      );

      const downloadUrl =
        window.URL.createObjectURL(
          blob
        );

      const link =
        document.createElement("a");

      link.href = downloadUrl;

      link.download =
        `creditpay_statement_${selectedYear}_${selectedMonth}.pdf`;

      document.body.appendChild(link);

      link.click();

      link.remove();

      window.URL.revokeObjectURL(
        downloadUrl
      );
    } catch (error) {
      setStatementError(
        "Unable to download the monthly statement. Please try again."
      );
    } finally {
      setStatementLoading(false);
    }
  };


  return (
    <div className="theme-transition min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">

      <Navbar />


      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">

        {/* PAGE HEADER */}

        <div className="mb-8">

          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            Dashboard
          </h1>

          <p className="mt-2 text-slate-600 dark:text-slate-400">
            Manage your cards and payments from one place.
          </p>

        </div>


        {/* ERROR */}

        {error && (
          <div
            className={
              isJwtError
                ? "mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300"
                : "mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300"
            }
          >
            <p className="font-medium">
              {error}
            </p>

            {isJwtError && (
              <Link
                to="/login"
                className="mt-2 inline-block text-sm font-semibold underline"
              >
                Go to Login
              </Link>
            )}
          </div>
        )}


        {loading ? (
          <>

            {/* STATISTICS SKELETON */}

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">

              <StatSkeleton />

              <StatSkeleton />

              <StatSkeleton />

              <StatSkeleton />

            </div>


            {/* QUICK ACTION SKELETON */}

            <div className="mt-8 animate-pulse rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

              <div className="h-6 w-36 rounded bg-slate-200 dark:bg-slate-700" />

              <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">

                <div className="h-32 rounded-xl bg-slate-200 dark:bg-slate-700" />

                <div className="h-32 rounded-xl bg-slate-200 dark:bg-slate-700" />

                <div className="h-32 rounded-xl bg-slate-200 dark:bg-slate-700" />

              </div>

            </div>


            {/* TRANSACTION SKELETON */}

            <div className="mt-8 animate-pulse rounded-xl bg-white shadow-sm dark:bg-slate-800">

              <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">

                <div className="h-6 w-48 rounded bg-slate-200 dark:bg-slate-700" />

              </div>

              <div className="space-y-4 p-6">

                <div className="h-12 rounded bg-slate-100 dark:bg-slate-700" />

                <div className="h-12 rounded bg-slate-100 dark:bg-slate-700" />

                <div className="h-12 rounded bg-slate-100 dark:bg-slate-700" />

                <div className="h-12 rounded bg-slate-100 dark:bg-slate-700" />

                <div className="h-12 rounded bg-slate-100 dark:bg-slate-700" />

              </div>

            </div>

          </>
        ) : (
          <>

            {/* REQUIRED DASHBOARD STATISTICS */}

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">

              {/* TOTAL SPENT */}

              <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                  Total Spent
                </p>

                <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
                  {formatCurrency(
                    dashboardSummary.total_amount_spent
                  )}
                </p>

                <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">
                  Total transaction amount
                </p>

              </div>


              {/* AVAILABLE CREDIT */}

              <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                  Available Credit
                </p>

                <p className="mt-2 text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {formatCurrency(
                    dashboardSummary.available_credit_limit
                  )}
                </p>

                <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">
                  Available on active credit cards
                </p>

              </div>


              {/* TOTAL TRANSACTIONS */}

              <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                  Total Transactions
                </p>

                <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
                  {dashboardSummary.total_transactions}
                </p>

                <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">
                  All your transactions
                </p>

              </div>


              {/* CURRENT MONTH */}

              <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                  This Month Spending
                </p>

                <p className="mt-2 text-3xl font-bold text-purple-600 dark:text-purple-400">
                  {formatCurrency(
                    dashboardSummary.current_month_spending
                  )}
                </p>

                <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">
                  Current month spending
                </p>

              </div>

            </div>


            {/* MONTHLY STATEMENT */}

            <div className="mt-8 rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

              <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">

                <div>

                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                    Monthly Statement
                  </h2>

                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    Download your transaction statement as a PDF.
                  </p>

                </div>


                <div className="flex flex-col gap-3 sm:flex-row sm:items-end">

                  <div>

                    <label
                      htmlFor="statement-month"
                      className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
                    >
                      Statement Month
                    </label>

                    <input
                      id="statement-month"
                      type="month"
                      value={statementMonth}
                      onChange={(event) =>
                        setStatementMonth(
                          event.target.value
                        )
                      }
                      className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                    />

                  </div>


                  <button
                    type="button"
                    onClick={
                      handleDownloadStatement
                    }
                    disabled={
                      statementLoading
                    }
                    className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:focus:ring-offset-slate-800"
                  >
                    {statementLoading
                      ? "Downloading..."
                      : "Download PDF"}
                  </button>

                </div>

              </div>


              {statementError && (
                <p className="mt-3 text-sm font-medium text-red-600 dark:text-red-400">
                  {statementError}
                </p>
              )}

            </div>


            {/* EXISTING QUICK ACTIONS */}

            <div className="mt-8">

              <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                Quick Actions
              </h2>

              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">

                <Link
                  to="/cards/add"
                  className="rounded-xl bg-blue-600 p-6 text-white shadow-sm transition hover:bg-blue-700"
                >

                  <h3 className="text-lg font-semibold">
                    Add Card
                  </h3>

                  <p className="mt-2 text-sm text-blue-100">
                    Save a credit or debit card securely.
                  </p>

                </Link>


                <Link
                  to="/payment"
                  className="rounded-xl bg-slate-900 p-6 text-white shadow-sm transition hover:bg-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600"
                >

                  <h3 className="text-lg font-semibold">
                    Make Payment
                  </h3>

                  <p className="mt-2 text-sm text-slate-300">
                    Make a simulated payment using a saved card.
                  </p>

                </Link>


                <Link
                  to="/transactions"
                  className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200 transition hover:ring-blue-300 dark:bg-slate-800 dark:ring-slate-700 dark:hover:ring-blue-500"
                >

                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Transaction History
                  </h3>

                  <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                    View and filter your previous transactions.
                  </p>

                </Link>

              </div>

            </div>


            {/* SAVED CARDS */}

            <div className="mt-8 rounded-xl bg-white shadow-sm dark:bg-slate-800">

              <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-700">

                <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                  Saved Cards
                </h2>

                <Link
                  to="/cards/add"
                  className="text-sm font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  Add Card
                </Link>

              </div>


              <div className="p-6">

                {cards.length === 0 ? (
                  <div className="py-8 text-center">

                    <p className="text-slate-500 dark:text-slate-400">
                      No saved cards yet.
                    </p>

                    <Link
                      to="/cards/add"
                      className="mt-4 inline-block rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white hover:bg-blue-700"
                    >
                      Add Your First Card
                    </Link>

                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">

                    {cards.map((card) => (

                      <div
                        key={card.id}
                        className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-900"
                      >

                        <div className="flex items-center justify-between">

                          <div>

                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                              {card.card_brand}
                            </p>

                            <p className="mt-2 text-lg font-semibold tracking-wider text-slate-900 dark:text-white">
                              {card.masked_number}
                            </p>

                          </div>


                          <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700 dark:bg-green-900/30 dark:text-green-300">
                            {card.card_type}
                          </span>

                        </div>


                        <div className="mt-4 flex justify-between text-sm text-slate-500 dark:text-slate-400">

                          <span>
                            Expires {card.expiry_month}/
                            {card.expiry_year}
                          </span>

                          <span>
                            ****{card.last4}
                          </span>

                        </div>


                        {card.card_type === "CREDIT" && (
                          <div className="mt-3 text-sm font-medium text-slate-700 dark:text-slate-300">
                            Credit Limit:{" "}
                            {formatCurrency(
                              card.credit_limit
                            )}
                          </div>
                        )}

                      </div>
                    ))}

                  </div>
                )}

              </div>

            </div>


            {/* PAYMENT STATUS */}

            <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2">

              <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                  Successful Payments
                </p>

                <p className="mt-2 text-3xl font-bold text-green-600 dark:text-green-400">
                  {successfulPayments}
                </p>

              </div>


              <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                  Failed Payments
                </p>

                <p className="mt-2 text-3xl font-bold text-red-600 dark:text-red-400">
                  {failedPayments}
                </p>

              </div>

            </div>


            {/* LAST 5 TRANSACTIONS */}

            <div className="mt-8 rounded-xl bg-white shadow-sm dark:bg-slate-800">

              <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-700">

                <div>

                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                    Last 5 Transactions
                  </h2>

                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    Your most recent payment activity.
                  </p>

                </div>


                <Link
                  to="/transactions"
                  className="text-sm font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  View All
                </Link>

              </div>


              <div className="overflow-x-auto">

                {recentTransactions.length === 0 ? (
                  <div className="px-6 py-10 text-center text-slate-500 dark:text-slate-400">
                    No transactions found.
                  </div>
                ) : (
                  <table className="min-w-full text-left text-sm">

                    <thead className="bg-slate-50 text-slate-500 dark:bg-slate-900 dark:text-slate-400">

                      <tr>

                        <th className="px-6 py-3 font-medium">
                          Amount
                        </th>

                        <th className="px-6 py-3 font-medium">
                          Masked Card
                        </th>

                        <th className="px-6 py-3 font-medium">
                          Date
                        </th>

                        <th className="px-6 py-3 font-medium">
                          Status
                        </th>

                      </tr>

                    </thead>


                    <tbody>

                      {recentTransactions.map(
                        (
                          transaction,
                          index
                        ) => (

                          <tr
                            key={`${transaction.date}-${transaction.amount}-${index}`}
                            className="border-t border-slate-100 dark:border-slate-700"
                          >

                            <td className="px-6 py-4 font-medium text-slate-900 dark:text-white">
                              {formatCurrency(
                                transaction.amount
                              )}
                            </td>


                            <td className="px-6 py-4 text-slate-600 dark:text-slate-300">
                              {transaction.masked_card_number}
                            </td>


                            <td className="px-6 py-4 text-slate-600 dark:text-slate-300">
                              {formatDate(
                                transaction.date
                              )}
                            </td>


                            <td className="px-6 py-4">

                              <span
                                className={getStatusClass(
                                  transaction.status
                                )}
                              >
                                {transaction.status}
                              </span>

                            </td>

                          </tr>

                        )
                      )}

                    </tbody>

                  </table>
                )}

              </div>

            </div>

          </>
        )}


      </main>

    </div>
  );
}


export default Dashboard;