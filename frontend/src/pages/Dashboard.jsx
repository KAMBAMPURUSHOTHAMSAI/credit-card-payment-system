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
    return "rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700";
  }

  if (status === "FAILED") {
    return "rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700";
  }

  return "rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-700";
}


function StatSkeleton() {
  return (
    <div className="animate-pulse rounded-xl bg-white p-6 shadow-sm">
      <div className="h-4 w-28 rounded bg-slate-200" />

      <div className="mt-4 h-9 w-36 rounded bg-slate-200" />

      <div className="mt-3 h-3 w-24 rounded bg-slate-100" />
    </div>
  );
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


  return (
    <div className="min-h-screen bg-slate-100">

      <Navbar />


      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">

        {/* PAGE HEADER */}

        <div className="mb-8">

          <h1 className="text-3xl font-bold text-slate-900">
            Dashboard
          </h1>

          <p className="mt-2 text-slate-600">
            Manage your cards and payments from one place.
          </p>

        </div>


        {/* ERROR */}

        {error && (
          <div
            className={
              isJwtError
                ? "mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800"
                : "mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700"
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

            <div className="mt-8 animate-pulse rounded-xl bg-white p-6 shadow-sm">

              <div className="h-6 w-36 rounded bg-slate-200" />

              <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">

                <div className="h-32 rounded-xl bg-slate-200" />

                <div className="h-32 rounded-xl bg-slate-200" />

                <div className="h-32 rounded-xl bg-slate-200" />

              </div>

            </div>


            {/* TRANSACTION SKELETON */}

            <div className="mt-8 animate-pulse rounded-xl bg-white shadow-sm">

              <div className="border-b border-slate-200 px-6 py-4">

                <div className="h-6 w-48 rounded bg-slate-200" />

              </div>

              <div className="space-y-4 p-6">

                <div className="h-12 rounded bg-slate-100" />

                <div className="h-12 rounded bg-slate-100" />

                <div className="h-12 rounded bg-slate-100" />

                <div className="h-12 rounded bg-slate-100" />

                <div className="h-12 rounded bg-slate-100" />

              </div>

            </div>
          </>
        ) : (
          <>

            {/* REQUIRED DASHBOARD STATISTICS */}

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">

              {/* TOTAL SPENT */}

              <div className="rounded-xl bg-white p-6 shadow-sm">

                <p className="text-sm font-medium text-slate-500">
                  Total Spent
                </p>

                <p className="mt-2 text-3xl font-bold text-slate-900">
                  {formatCurrency(
                    dashboardSummary.total_amount_spent
                  )}
                </p>

                <p className="mt-2 text-xs text-slate-400">
                  Total transaction amount
                </p>

              </div>


              {/* AVAILABLE CREDIT */}

              <div className="rounded-xl bg-white p-6 shadow-sm">

                <p className="text-sm font-medium text-slate-500">
                  Available Credit
                </p>

                <p className="mt-2 text-3xl font-bold text-blue-600">
                  {formatCurrency(
                    dashboardSummary.available_credit_limit
                  )}
                </p>

                <p className="mt-2 text-xs text-slate-400">
                  Available on active credit cards
                </p>

              </div>


              {/* TOTAL TRANSACTIONS */}

              <div className="rounded-xl bg-white p-6 shadow-sm">

                <p className="text-sm font-medium text-slate-500">
                  Total Transactions
                </p>

                <p className="mt-2 text-3xl font-bold text-slate-900">
                  {dashboardSummary.total_transactions}
                </p>

                <p className="mt-2 text-xs text-slate-400">
                  All your transactions
                </p>

              </div>


              {/* CURRENT MONTH */}

              <div className="rounded-xl bg-white p-6 shadow-sm">

                <p className="text-sm font-medium text-slate-500">
                  This Month Spending
                </p>

                <p className="mt-2 text-3xl font-bold text-purple-600">
                  {formatCurrency(
                    dashboardSummary.current_month_spending
                  )}
                </p>

                <p className="mt-2 text-xs text-slate-400">
                  Current month spending
                </p>

              </div>

            </div>


            {/* EXISTING QUICK ACTIONS */}

            <div className="mt-8">

              <h2 className="text-xl font-bold text-slate-900">
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
                  className="rounded-xl bg-slate-900 p-6 text-white shadow-sm transition hover:bg-slate-800"
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
                  className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200 transition hover:ring-blue-300"
                >

                  <h3 className="text-lg font-semibold text-slate-900">
                    Transaction History
                  </h3>

                  <p className="mt-2 text-sm text-slate-500">
                    View and filter your previous transactions.
                  </p>

                </Link>

              </div>

            </div>


            {/* SAVED CARDS */}

            <div className="mt-8 rounded-xl bg-white shadow-sm">

              <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">

                <h2 className="text-xl font-bold text-slate-900">
                  Saved Cards
                </h2>

                <Link
                  to="/cards/add"
                  className="text-sm font-semibold text-blue-600 hover:text-blue-700"
                >
                  Add Card
                </Link>

              </div>


              <div className="p-6">

                {cards.length === 0 ? (
                  <div className="py-8 text-center">

                    <p className="text-slate-500">
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
                        className="rounded-xl border border-slate-200 bg-slate-50 p-5"
                      >

                        <div className="flex items-center justify-between">

                          <div>

                            <p className="text-sm font-medium text-slate-500">
                              {card.card_brand}
                            </p>

                            <p className="mt-2 text-lg font-semibold tracking-wider text-slate-900">
                              {card.masked_number}
                            </p>

                          </div>


                          <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
                            {card.card_type}
                          </span>

                        </div>


                        <div className="mt-4 flex justify-between text-sm text-slate-500">

                          <span>
                            Expires {card.expiry_month}/
                            {card.expiry_year}
                          </span>

                          <span>
                            ****{card.last4}
                          </span>

                        </div>


                        {card.card_type === "CREDIT" && (
                          <div className="mt-3 text-sm font-medium text-slate-700">
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

              <div className="rounded-xl bg-white p-6 shadow-sm">

                <p className="text-sm font-medium text-slate-500">
                  Successful Payments
                </p>

                <p className="mt-2 text-3xl font-bold text-green-600">
                  {successfulPayments}
                </p>

              </div>


              <div className="rounded-xl bg-white p-6 shadow-sm">

                <p className="text-sm font-medium text-slate-500">
                  Failed Payments
                </p>

                <p className="mt-2 text-3xl font-bold text-red-600">
                  {failedPayments}
                </p>

              </div>

            </div>


            {/* LAST 5 TRANSACTIONS */}

            <div className="mt-8 rounded-xl bg-white shadow-sm">

              <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">

                <div>

                  <h2 className="text-xl font-bold text-slate-900">
                    Last 5 Transactions
                  </h2>

                  <p className="mt-1 text-sm text-slate-500">
                    Your most recent payment activity.
                  </p>

                </div>


                <Link
                  to="/transactions"
                  className="text-sm font-semibold text-blue-600 hover:text-blue-700"
                >
                  View All
                </Link>

              </div>


              <div className="overflow-x-auto">

                {recentTransactions.length === 0 ? (
                  <div className="px-6 py-10 text-center text-slate-500">
                    No transactions found.
                  </div>
                ) : (
                  <table className="min-w-full text-left text-sm">

                    <thead className="bg-slate-50 text-slate-500">

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
                            className="border-t border-slate-100"
                          >

                            <td className="px-6 py-4 font-medium text-slate-900">
                              {formatCurrency(
                                transaction.amount
                              )}
                            </td>


                            <td className="px-6 py-4 text-slate-600">
                              {transaction.masked_card_number}
                            </td>


                            <td className="px-6 py-4 text-slate-600">
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