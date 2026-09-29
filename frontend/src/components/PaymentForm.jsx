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
    <div className="rounded-xl bg-white p-6 shadow-sm">

      <h2 className="text-xl font-bold text-slate-900">
        Make Payment
      </h2>

      <p className="mt-1 text-sm text-slate-500">
        Select a saved card and enter the payment amount.
      </p>


      {error && (
        <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}


      {paymentResult && (
        <div
          className={
            paymentResult.status ===
            "SUCCESS"
              ? "mt-5 rounded-lg border border-green-200 bg-green-50 px-4 py-4 text-green-700"
              : "mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-4 text-red-700"
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


      {loadingCards ? (
        <div className="mt-6">
          <p className="text-slate-500">
            Loading saved cards...
          </p>
        </div>
      ) : cards.length === 0 ? (
        <div className="mt-6 rounded-lg bg-slate-50 p-5 text-center">

          <p className="text-slate-600">
            You don't have any saved cards.
          </p>

          <a
            href="/cards/add"
            className="mt-4 inline-block rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white hover:bg-blue-700"
          >
            Add Card
          </a>

        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          className="mt-6 space-y-5"
        >

          <div>

            <label
              htmlFor="card_id"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Select Card
            </label>

            <select
              id="card_id"
              name="card_id"
              value={formData.card_id}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
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


          <div>

            <label
              htmlFor="amount"
              className="mb-2 block text-sm font-medium text-slate-700"
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
              className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />

          </div>


          <div>

            <label
              htmlFor="currency"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Currency
            </label>

            <select
              id="currency"
              name="currency"
              value={formData.currency}
              onChange={handleChange}
              className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              <option value="INR">
                INR
              </option>
            </select>

          </div>


          <div>

            <label
              htmlFor="description"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Description
            </label>

            <textarea
              id="description"
              name="description"
              rows="3"
              maxLength="255"
              value={formData.description}
              onChange={handleChange}
              placeholder="Optional payment description"
              className="w-full resize-none rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />

          </div>


          <button
            type="submit"
            disabled={loadingPayment}
            className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
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