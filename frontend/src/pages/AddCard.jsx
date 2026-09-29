import { useEffect, useState } from "react";
import { djangoApi } from "../api";
import Navbar from "../components/Navbar";


function AddCard() {
  const [cards, setCards] = useState([]);

  const [formData, setFormData] = useState({
    card_type: "CREDIT",
    card_number: "",
    cvv: "",
    expiry_month: "",
    expiry_year: "",
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [cardsLoading, setCardsLoading] = useState(true);


  const loadCards = async () => {
    setCardsLoading(true);

    try {
      const response = await djangoApi.get(
        "/cards/"
      );

      setCards(response.data || []);

    } catch (error) {
      setError(
        "Unable to load saved cards."
      );
    } finally {
      setCardsLoading(false);
    }
  };


  useEffect(() => {
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
    setSuccess("");
    setLoading(true);

    try {
      await djangoApi.post(
        "/cards/",
        {
          card_type: formData.card_type,
          card_number: formData.card_number,
          cvv: formData.cvv,
          expiry_month: Number(
            formData.expiry_month
          ),
          expiry_year: Number(
            formData.expiry_year
          ),
        }
      );

      setSuccess(
        "Card added successfully."
      );

      setFormData({
        card_type: "CREDIT",
        card_number: "",
        cvv: "",
        expiry_month: "",
        expiry_year: "",
      });

      await loadCards();

    } catch (error) {
      const data =
        error.response?.data;

      if (data?.detail) {
        setError(data.detail);
      } else if (data?.card_number) {
        setError(
          data.card_number.join(" ")
        );
      } else {
        setError(
          "Unable to add card."
        );
      }

    } finally {
      setLoading(false);
    }
  };


  const handleDelete = async (
    cardId
  ) => {
    const confirmed =
      window.confirm(
        "Are you sure you want to delete this card?"
      );

    if (!confirmed) {
      return;
    }

    setError("");
    setSuccess("");

    try {
      await djangoApi.delete(
        `/cards/${cardId}/`
      );

      setSuccess(
        "Card deleted successfully."
      );

      await loadCards();

    } catch (error) {
      setError(
        "Unable to delete card."
      );
    }
  };


  return (
    <div className="min-h-screen bg-slate-100">

      <Navbar />

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">

        <div className="mb-8">

          <h1 className="text-3xl font-bold text-slate-900">
            Manage Cards
          </h1>

          <p className="mt-2 text-slate-600">
            Add and manage your saved credit and debit cards.
          </p>

        </div>


        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            {error}
          </div>
        )}


        {success && (
          <div className="mb-6 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-green-700">
            {success}
          </div>
        )}


        {/* ADD CARD FORM */}

        <div className="rounded-xl bg-white p-6 shadow-sm">

          <h2 className="text-xl font-bold text-slate-900">
            Add New Card
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Your full card number and CVV are never stored by the application.
          </p>


          <form
            onSubmit={handleSubmit}
            className="mt-6 space-y-5"
          >

            <div>

              <label
                htmlFor="card_type"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Card Type
              </label>

              <select
                id="card_type"
                name="card_type"
                value={formData.card_type}
                onChange={handleChange}
                className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              >
                <option value="CREDIT">
                  Credit Card
                </option>

                <option value="DEBIT">
                  Debit Card
                </option>
              </select>

            </div>


            <div>

              <label
                htmlFor="card_number"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Card Number
              </label>

              <input
                id="card_number"
                name="card_number"
                type="text"
                inputMode="numeric"
                maxLength={19}
                value={formData.card_number}
                onChange={handleChange}
                required
                placeholder="Enter card number"
                autoComplete="cc-number"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 tracking-wider outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />

            </div>


            <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">

              <div>

                <label
                  htmlFor="cvv"
                  className="mb-2 block text-sm font-medium text-slate-700"
                >
                  CVV
                </label>

                <input
                  id="cvv"
                  name="cvv"
                  type="password"
                  inputMode="numeric"
                  maxLength={4}
                  value={formData.cvv}
                  onChange={handleChange}
                  required
                  placeholder="CVV"
                  autoComplete="cc-csc"
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />

              </div>


              <div>

                <label
                  htmlFor="expiry_month"
                  className="mb-2 block text-sm font-medium text-slate-700"
                >
                  Expiry Month
                </label>

                <input
                  id="expiry_month"
                  name="expiry_month"
                  type="number"
                  min="1"
                  max="12"
                  value={formData.expiry_month}
                  onChange={handleChange}
                  required
                  placeholder="MM"
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />

              </div>


              <div>

                <label
                  htmlFor="expiry_year"
                  className="mb-2 block text-sm font-medium text-slate-700"
                >
                  Expiry Year
                </label>

                <input
                  id="expiry_year"
                  name="expiry_year"
                  type="number"
                  value={formData.expiry_year}
                  onChange={handleChange}
                  required
                  placeholder="YYYY"
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />

              </div>

            </div>


            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto sm:px-8"
            >
              {loading
                ? "Adding Card..."
                : "Add Card"}
            </button>

          </form>

        </div>


        {/* SAVED CARDS */}

        <div className="mt-8 rounded-xl bg-white shadow-sm">

          <div className="border-b border-slate-200 px-6 py-4">

            <h2 className="text-xl font-bold text-slate-900">
              Saved Cards
            </h2>

          </div>


          <div className="p-6">

            {cardsLoading ? (
              <p className="text-slate-500">
                Loading cards...
              </p>
            ) : cards.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-slate-500">
                  No saved cards yet.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-5 md:grid-cols-2">

                {cards.map((card) => (
                  <div
                    key={card.id}
                    className="rounded-xl border border-slate-200 bg-slate-50 p-5"
                  >

                    <div className="flex items-start justify-between">

                      <div>

                        <p className="text-sm font-semibold text-slate-500">
                          {card.card_brand}
                        </p>

                        <p className="mt-2 text-xl font-semibold tracking-widest text-slate-900">
                          {card.masked_number}
                        </p>

                      </div>


                      <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
                        {card.card_type}
                      </span>

                    </div>


                    <div className="mt-5 flex items-center justify-between">

                      <div className="text-sm text-slate-500">
                        Expires{" "}
                        {card.expiry_month}/
                        {card.expiry_year}
                      </div>

                      <button
                        type="button"
                        onClick={() =>
                          handleDelete(card.id)
                        }
                        className="rounded-lg bg-red-50 px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-100"
                      >
                        Delete
                      </button>

                    </div>

                  </div>
                ))}

              </div>
            )}

          </div>

        </div>

      </main>

    </div>
  );
}


export default AddCard;