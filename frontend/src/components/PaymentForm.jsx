import { useEffect, useState } from "react";

import { djangoApi, fastApi } from "../api";


function PaymentForm() {
  const [cards, setCards] = useState([]);

  const [formData, setFormData] = useState({
    card_id: "",
    amount: "",
    currency: "INR",
    description: "",
  });

  const [loadingCards, setLoadingCards] =
    useState(true);

  const [loadingPayment, setLoadingPayment] =
    useState(false);

  const [error, setError] = useState("");

  const [paymentResult, setPaymentResult] =
    useState(null);


  useEffect(() => {
    const loadCards = async () => {
      setLoadingCards(true);
      setError("");

      try {
        const response =
          await djangoApi.get("/cards/");

        setCards(response.data || []);

      } catch (error) {
        setError(
          "Unable to load saved cards."
        );
      } finally {
        setLoadingCards(false);
      }
    };

    loadCards();
  }, []);


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
    setPaymentResult(null);

    if (!formData.card_id) {
      setError(
        "Please select a card."
      );
      return;
    }

    if (
      !formData.amount ||
      Number(formData.amount) <= 0
    ) {
      setError(
        "Please enter a valid amount."
      );
      return;
    }

    setLoadingPayment(true);

    try {
      const response =
        await fastApi.post(
          "/api/payments/",
          {
            card_id: Number(
              formData.card_id
            ),
            amount: Number(
              formData.amount
            ),
            currency:
              formData.currency,
            description:
              formData.description,
          }
        );

      setPaymentResult(
        response.data
      );

      setFormData(
        (previous) => ({
          ...previous,
          amount: "",
          description: "",
        })
      );

    } catch (error) {
      const detail =
        error.response?.data?.detail;

      if (detail) {
        setError(detail);
      } else {
        setError(
          "Payment could not be processed."
        );
      }

    } finally {
      setLoadingPayment(false);
    }
  };


  return (
    <div className="theme-transition rounded-xl bg-white p-6 text-slate-900 shadow-sm dark:bg-slate-800 dark:text-slate-100">

      <h2 className="text-xl font-bold text-slate-900 dark:text-white">
        Make Payment
      </h2>

      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        Select a saved card and enter the payment amount.
      </p>


      {/* ERROR */}

      {error && (
        <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
          {error}
        </div>
      )}


      {/* PAYMENT RESULT */}

      {paymentResult && (
        <div
          className={
            paymentResult.status ===
            "SUCCESS"
              ? "mt-5 rounded-lg border border-green-200 bg-green-50 px-4 py-4 text-green-700 dark:border-green-900/50 dark:bg-green-950/30 dark:text-green-300"
              : "mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-4 text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300"
          }
        >

          <p className="font-semibold">
            Payment{" "}
            {paymentResult.status}
          </p>

          <p className="mt-2 text-sm">
            Reference:{" "}
            {paymentResult.reference}
          </p>

          <p className="mt-1 text-sm">
            Amount:{" "}
            {paymentResult.amount}{" "}
            {paymentResult.currency}
          </p>

          {paymentResult.failure_reason && (
            <p className="mt-1 text-sm">
              Reason:{" "}
              {paymentResult.failure_reason}
            </p>
          )}

        </div>
      )}


      {/* LOADING CARDS */}

      {loadingCards ? (
        <div className="mt-6">

          <p className="text-slate-500 dark:text-slate-400">
            Loading saved cards...
          </p>

        </div>
      ) : cards.length === 0 ? (
        <div className="mt-6 rounded-lg bg-slate-50 p-5 text-center dark:bg-slate-900">

          <p className="text-slate-600 dark:text-slate-300">
            You don't have any saved cards.
          </p>

          <a
            href="/cards/add"
            className="mt-4 inline-block rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-slate-800"
          >
            Add Card
          </a>

        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          className="mt-6 space-y-5"
        >

          {/* SELECT CARD */}

          <div>

            <label
              htmlFor="card_id"
              className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Select Card
            </label>

            <select
              id="card_id"
              name="card_id"
              value={formData.card_id}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-400 dark:focus:ring-blue-900/30"
            >
              <option value="">
                Select a saved card
              </option>

              {cards.map((card) => (
                <option
                  key={card.id}
                  value={card.id}
                >
                  {card.card_brand}{" "}
                  {card.masked_number}
                </option>
              ))}

            </select>

          </div>


          {/* AMOUNT */}

          <div>

            <label
              htmlFor="amount"
              className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Amount
            </label>

            <input
              id="amount"
              name="amount"
              type="number"
              min="1"
              step="0.01"
              value={formData.amount}
              onChange={handleChange}
              required
              placeholder="Enter amount"
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-blue-400 dark:focus:ring-blue-900/30"
            />

          </div>


          {/* CURRENCY */}

          <div>

            <label
              htmlFor="currency"
              className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Currency
            </label>

            <select
              id="currency"
              name="currency"
              value={formData.currency}
              onChange={handleChange}
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-400 dark:focus:ring-blue-900/30"
            >
              <option value="INR">
                INR
              </option>
            </select>

          </div>


          {/* DESCRIPTION */}

          <div>

            <label
              htmlFor="description"
              className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Description
            </label>

            <textarea
              id="description"
              name="description"
              rows="3"
              maxLength="255"
              value={
                formData.description
              }
              onChange={handleChange}
              placeholder="Optional payment description"
              className="w-full resize-none rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-blue-400 dark:focus:ring-blue-900/30"
            />

          </div>


          {/* SUBMIT */}

          <button
            type="submit"
            disabled={loadingPayment}
            className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:focus:ring-offset-slate-800"
          >
            {loadingPayment
              ? "Processing Payment..."
              : "Make Payment"}
          </button>

        </form>
      )}

    </div>
  );
}


export default PaymentForm;