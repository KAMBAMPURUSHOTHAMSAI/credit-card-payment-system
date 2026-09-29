import Navbar from "../components/Navbar";
import PaymentForm from "../components/PaymentForm";


function MakePayment() {
  return (
    <div className="min-h-screen bg-slate-100">

      <Navbar />

      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">

        <div className="mb-8">

          <h1 className="text-3xl font-bold text-slate-900">
            Make Payment
          </h1>

          <p className="mt-2 text-slate-600">
            Make a secure simulated payment using your saved card.
          </p>

        </div>

        <PaymentForm />

      </main>

    </div>
  );
}


export default MakePayment;