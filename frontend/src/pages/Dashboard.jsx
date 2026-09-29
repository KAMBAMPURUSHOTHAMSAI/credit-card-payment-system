import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import Navbar from "../components/Navbar";
import { djangoApi } from "../api";


function Dashboard() {
  const [cards, setCards] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError("");

      try {
        const [
          cardsResponse,
          transactionsResponse,
        ] = await Promise.all([
          djangoApi.get("/cards/"),
          djangoApi.get("/transactions/"),
        ]);

        setCards(
          cardsResponse.data || []
        );

        setTransactions(
          transactionsResponse.data || []
        );

      } catch (error) {
        setError(
          "Unable to load dashboard data."
        );
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);


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

        <div className="mb-8">

          <h1 className="text-3xl font-bold text-slate-900">
            Dashboard
          </h1>

          <p className="mt-2 text-slate-600">
            Manage your cards and payments from one place.
          </p>

        </div>


        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            {error}
          </div>
        )}


        {loading ? (
          <div className="rounded-xl bg-white p-8 text-center shadow-sm">
            <p className="text-slate-600">
              Loading dashboard...
            </p>
          </div>
        ) : (
          <>
            {/* SUMMARY CARDS */}

            <div className="grid grid-cols-1 gap-5 md:grid-cols-3">

              <div className="rounded-xl bg-white p-6 shadow-sm">
                <p className="text-sm font-medium text-slate-500">
                  Saved Cards
                </p>

                <p className="mt-2 text-3xl font-bold text-slate-900">
                  {cards.length}
                </p>

              </div>


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


            {/* QUICK ACTIONS */}

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
                  <div className="text-center py-8">

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

                      </div>
                    ))}

                  </div>
                )}

              </div>

            </div>


            {/* RECENT TRANSACTIONS */}

            <div className="mt-8 rounded-xl bg-white shadow-sm">

              <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">

                <h2 className="text-xl font-bold text-slate-900">
                  Recent Transactions
                </h2>

                <Link
                  to="/transactions"
                  className="text-sm font-semibold text-blue-600 hover:text-blue-700"
                >
                  View All
                </Link>

              </div>


              <div className="overflow-x-auto">

                {transactions.length === 0 ? (
                  <div className="px-6 py-10 text-center text-slate-500">
                    No transactions found.
                  </div>
                ) : (
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
                      </tr>
                    </thead>

                    <tbody>

                      {transactions
                        .slice(0, 5)
                        .map((transaction) => (
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

                            <td className="px-6 py-4 text-slate-600">
                              {transaction.amount}{" "}
                              {transaction.currency}
                            </td>

                            <td className="px-6 py-4">

                              <span
                                className={
                                  transaction.status === "SUCCESS"
                                    ? "rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700"
                                    : transaction.status === "FAILED"
                                      ? "rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700"
                                      : "rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-700"
                                }
                              >
                                {transaction.status}
                              </span>

                            </td>

                          </tr>
                        ))}

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