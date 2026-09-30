from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.payments import router as payment_router


app = FastAPI(
    title="Credit Card Payment System - Payment API",
    description=(
        "Payment processing service "
        "for the Credit Card Payment System."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(payment_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "fastapi-payment-service",
    }
