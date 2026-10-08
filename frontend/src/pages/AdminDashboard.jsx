import { useEffect, useState } from "react";

import Navbar from "../components/Navbar";
import { djangoApi } from "../api";


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


function AdminDashboard() {
  const [summary, setSummary] = useState(null);

  const [cards, setCards] = useState([]);

  const [creditLimitDrafts, setCreditLimitDrafts] =
    useState({});

  const [error, setError] = useState("");

  const [loading, setLoading] = useState(true);

  const [cardsLoading, setCardsLoading] =
    useState(true);

  const [updatingCardId, setUpdatingCardId] =
    useState(null);


  const loadAdminData = async () => {
    setLoading(true);
    setCardsLoading(true);
    setError("");

    try {
      const [
        summaryResponse,
        cardsResponse,
      ] = await Promise.all([
        djangoApi.get(
          "/admin/dashboard/"
        ),
        djangoApi.get(
          "/admin/cards/"
        ),
      ]);

      setSummary(
        summaryResponse.data
      );

      const cardData =
        cardsResponse.data || [];

      setCards(cardData);

      const drafts = {};

      cardData.forEach((card) => {
        drafts[card.id] =
          String(
            card.credit_limit ?? 0
          );
      });

      setCreditLimitDrafts(
        drafts
      );
    } catch (error) {
      if (
        error.response?.status === 401 ||
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
      setCardsLoading(false);
    }
  };


  useEffect(() => {
    loadAdminData();
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


  const handleCardStatusChange = async (
    card
  ) => {
    const action =
      card.is_active
        ? "block"
        : "unblock";

    const confirmed =
      window.confirm(
        `Are you sure you want to ${action} this card (${card.masked_number})?`
      );

    if (!confirmed) {
      return;
    }

    setUpdatingCardId(
      card.id
    );

    setError("");

    try {
      const response =
        await djangoApi.patch(
          `/admin/cards/${card.id}/`,
          {
            is_active:
              !card.is_active,
          }
        );

      const updatedCard =
        response.data;

      setCards((currentCards) =>
        currentCards.map(
          (currentCard) =>
            currentCard.id ===
            updatedCard.id
              ? updatedCard
              : currentCard
        )
      );

      setCreditLimitDrafts(
        (currentDrafts) => ({
          ...currentDrafts,
          [updatedCard.id]:
            String(
              updatedCard.credit_limit ??
                0
            ),
        })
      );
    } catch (error) {
      const detail =
        error.response?.data?.detail;

      setError(
        detail ||
          `Unable to ${action} the card.`
      );
    } finally {
      setUpdatingCardId(
        null
      );
    }
  };


  const handleCreditLimitChange = (
    cardId,
    value
  ) => {
    setCreditLimitDrafts(
      (currentDrafts) => ({
        ...currentDrafts,
        [cardId]: value,
      })
    );
  };


  const handleCreditLimitSave = async (
    card
  ) => {
    const rawValue =
      creditLimitDrafts[
        card.id
      ];

    if (
      rawValue === undefined ||
      rawValue === ""
    ) {
      setError(
        "Please enter a credit limit."
      );

      return;
    }

    const numericValue =
      Number(rawValue);

    if (
      Number.isNaN(
        numericValue
      ) ||
      numericValue < 0
    ) {
      setError(
        "Credit limit must be a valid non-negative number."
      );

      return;
    }

    if (
      card.card_type === "CREDIT" &&
      numericValue <= 0
    ) {
      setError(
        "Credit cards must have a positive credit limit."
      );

      return;
    }

    if (
      card.card_type === "DEBIT" &&
      numericValue !== 0
    ) {
      setError(
        "Debit cards must have a credit limit of 0."
      );

      return;
    }

    const currentLimit =
      Number(
        card.credit_limit || 0
      );

    if (
      numericValue === currentLimit
    ) {
      return;
    }

    setUpdatingCardId(
      card.id
    );

    setError("");

    try {
      const response =
        await djangoApi.patch(
          `/admin/cards/${card.id}/`,
          {
            credit_limit:
              numericValue,
          }
        );

      const updatedCard =
        response.data;

      setCards((currentCards) =>
        currentCards.map(
          (currentCard) =>
            currentCard.id ===
            updatedCard.id
              ? updatedCard
              : currentCard
        )
      );

      setCreditLimitDrafts(
        (currentDrafts) => ({
          ...currentDrafts,
          [updatedCard.id]:
            String(
              updatedCard.credit_limit ??
                0
            ),
        })
      );
    } catch (error) {
      const detail =
        error.response?.data?.detail;

      setError(
        detail ||
          "Unable to update the credit limit."
      );
    } finally {
      setUpdatingCardId(
        null
      );
    }
  };


  return (
    <div className="theme-transition min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">

      <Navbar />


      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">

        {/* PAGE HEADER */}

        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">

          <div>

            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
              Admin Dashboard
            </h1>

            <p className="mt-2 text-slate-600 dark:text-slate-400">
              Monitor payment activity and manage customer cards.
            </p>

          </div>


          <button
            type="button"
            onClick={handleExport}
            className="rounded-lg bg-slate-900 px-5 py-3 font-semibold text-white transition-colors hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white dark:focus:ring-offset-slate-950"
          >
            Export Transactions CSV
          </button>

        </div>


        {/* ERROR */}

        {error && (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
            {error}
          </div>
        )}


        {/* DAILY SUMMARY */}

        {loading ? (
          <div className="mt-8 rounded-xl bg-white p-10 text-center shadow-sm dark:bg-slate-800">
            <p className="text-slate-500 dark:text-slate-400">
              Loading admin dashboard...
            </p>
          </div>
        ) : summary ? (
          <>

            <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">

              <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Total Transactions
                </p>

                <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
                  {summary.total_transactions}
                </p>

              </div>


              <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Total Amount
                </p>

                <p className="mt-2 text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {formatCurrency(
                    summary.total_amount
                  )}
                </p>

              </div>


              <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Successful
                </p>

                <p className="mt-2 text-3xl font-bold text-green-600 dark:text-green-400">
                  {summary.success_count}
                </p>

              </div>


              <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Failed
                </p>

                <p className="mt-2 text-3xl font-bold text-red-600 dark:text-red-400">
                  {summary.failed_count}
                </p>

              </div>


              <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Pending
                </p>

                <p className="mt-2 text-3xl font-bold text-yellow-600 dark:text-yellow-400">
                  {summary.pending_count}
                </p>

              </div>

            </div>


            <div className="mt-8 rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">

              <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                Daily Payment Summary
              </h2>

              <p className="mt-2 text-slate-500 dark:text-slate-400">
                Summary for {summary.date}
              </p>

              <div className="mt-6 h-3 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">

                <div
                  className="h-full bg-green-500 transition-all duration-300"
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


        {/* CARD MANAGEMENT */}

        <section className="mt-8 rounded-xl bg-white shadow-sm dark:bg-slate-800">

          <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">

            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Card Management
            </h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Manage card status, credit limits, and card activity.
            </p>

          </div>


          {cardsLoading ? (
            <div className="px-6 py-10 text-center">

              <p className="text-slate-500 dark:text-slate-400">
                Loading card information...
              </p>

            </div>
          ) : cards.length === 0 ? (
            <div className="px-6 py-10 text-center">

              <p className="text-slate-500 dark:text-slate-400">
                No cards found.
              </p>

            </div>
          ) : (
            <div className="overflow-x-auto">

              <table className="min-w-full text-left text-sm">

                <thead className="bg-slate-50 text-slate-500 dark:bg-slate-900 dark:text-slate-400">

                  <tr>

                    <th className="whitespace-nowrap px-4 py-3 font-medium">
                      Cardholder
                    </th>

                    <th className="whitespace-nowrap px-4 py-3 font-medium">
                      Card
                    </th>

                    <th className="whitespace-nowrap px-4 py-3 font-medium">
                      Expiry
                    </th>

                    <th className="whitespace-nowrap px-4 py-3 font-medium">
                      Status
                    </th>

                    <th className="whitespace-nowrap px-4 py-3 font-medium">
                      Credit Limit
                    </th>

                    <th className="whitespace-nowrap px-4 py-3 font-medium">
                      Available
                    </th>

                    <th className="whitespace-nowrap px-4 py-3 font-medium">
                      Spent
                    </th>

                    <th className="whitespace-nowrap px-4 py-3 font-medium">
                      Transactions
                    </th>

                    <th className="whitespace-nowrap px-4 py-3 font-medium">
                      Last Activity
                    </th>

                    <th className="whitespace-nowrap px-4 py-3 font-medium">
                      Actions
                    </th>

                  </tr>

                </thead>


                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">

                  {cards.map((card) => {

                    const isUpdating =
                      updatingCardId ===
                      card.id;

                    return (
                      <tr
                        key={card.id}
                        className="transition-colors hover:bg-slate-50 dark:hover:bg-slate-900/60"
                      >

                        {/* CARDHOLDER */}

                        <td className="px-4 py-4">

                          <p className="font-semibold text-slate-900 dark:text-white">
                            {card.username}
                          </p>

                          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                            {card.email}
                          </p>

                        </td>


                        {/* CARD */}

                        <td className="px-4 py-4">

                          <p className="font-semibold text-slate-900 dark:text-white">
                            {card.card_brand}
                          </p>

                          <p className="mt-1 whitespace-nowrap font-mono text-xs tracking-wider text-slate-600 dark:text-slate-300">
                            {card.masked_number}
                          </p>

                          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                            {card.card_type}
                          </p>

                        </td>


                        {/* EXPIRY */}

                        <td className="whitespace-nowrap px-4 py-4 text-slate-600 dark:text-slate-300">

                          {card.expiry_month}/
                          {card.expiry_year}

                        </td>


                        {/* STATUS */}

                        <td className="px-4 py-4">

                          <span
                            className={
                              card.is_active
                                ? "rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700 dark:bg-green-900/30 dark:text-green-300"
                                : "rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700 dark:bg-red-900/30 dark:text-red-300"
                            }
                          >
                            {card.is_active
                              ? "Active"
                              : "Blocked"}
                          </span>

                        </td>


                        {/* CREDIT LIMIT */}

                        <td className="px-4 py-4">

                          <div className="flex min-w-[190px] items-center gap-2">

                            <input
                              type="number"
                              min="0"
                              step="0.01"
                              value={
                                creditLimitDrafts[
                                  card.id
                                ] ?? ""
                              }
                              onChange={(
                                event
                              ) =>
                                handleCreditLimitChange(
                                  card.id,
                                  event.target.value
                                )
                              }
                              disabled={
                                isUpdating
                              }
                              aria-label={`Credit limit for ${card.masked_number}`}
                              className="w-32 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                            />

                            <button
                              type="button"
                              onClick={() =>
                                handleCreditLimitSave(
                                  card
                                )
                              }
                              disabled={
                                isUpdating
                              }
                              className="rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:focus:ring-offset-slate-800"
                            >
                              Save
                            </button>

                          </div>

                        </td>


                        {/* AVAILABLE CREDIT */}

                        <td className="whitespace-nowrap px-4 py-4 font-medium text-blue-600 dark:text-blue-400">

                          {formatCurrency(
                            card.available_credit
                          )}

                        </td>


                        {/* SPENT */}

                        <td className="whitespace-nowrap px-4 py-4 text-slate-700 dark:text-slate-300">

                          {formatCurrency(
                            card.spent_amount
                          )}

                        </td>


                        {/* TRANSACTION COUNT */}

                        <td className="px-4 py-4 text-center text-slate-700 dark:text-slate-300">

                          {card.transaction_count}

                        </td>


                        {/* LAST ACTIVITY */}

                        <td className="whitespace-nowrap px-4 py-4 text-slate-600 dark:text-slate-300">

                          {formatDate(
                            card.last_activity
                          )}

                        </td>


                        {/* ACTIONS */}

                        <td className="px-4 py-4">

                          <button
                            type="button"
                            onClick={() =>
                              handleCardStatusChange(
                                card
                              )
                            }
                            disabled={
                              isUpdating
                            }
                            aria-label={
                              card.is_active
                                ? `Block ${card.masked_number}`
                                : `Unblock ${card.masked_number}`
                            }
                            className={
                              card.is_active
                                ? "whitespace-nowrap rounded-lg bg-red-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:focus:ring-offset-slate-800"
                                : "whitespace-nowrap rounded-lg bg-green-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:focus:ring-offset-slate-800"
                            }
                          >
                            {isUpdating
                              ? "Updating..."
                              : card.is_active
                              ? "Block"
                              : "Unblock"}
                          </button>

                        </td>

                      </tr>
                    );
                  })}

                </tbody>

              </table>

            </div>
          )}

        </section>

      </main>

    </div>
  );
}


export default AdminDashboard;