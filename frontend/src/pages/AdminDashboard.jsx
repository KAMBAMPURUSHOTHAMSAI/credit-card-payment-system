
import { useCallback, useEffect, useState } from "react";

import Navbar from "../components/Navbar";
import { djangoApi } from "../api";

const CHART_COLORS = [
  "#2563eb",
  "#16a34a",
  "#ea580c",
  "#9333ea",
  "#db2777",
  "#0891b2",
  "#ca8a04",
  "#64748b",
];

function formatCurrency(value) {
  const amount = Number(value || 0);

  return amount.toLocaleString("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatDate(value) {
  if (!value) return "-";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function ChartPanel({ title, children }) {
  return (
    <section className="min-w-0 rounded-xl bg-white p-5 shadow-sm dark:bg-slate-800 sm:p-6">
      <h3 className="text-lg font-bold text-slate-900 dark:text-white">
        {title}
      </h3>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function getSeries(data, key) {
  if (!Array.isArray(data)) return [];

  return data.map((item) => ({
    label: String(item[key] ?? item.label ?? "Other"),
    amount: Number(item.total ?? item.amount ?? 0),
  })).filter((item) => Number.isFinite(item.amount));
}

function formatMonthLabel(value) {
  if (/^\d{4}-\d{2}$/.test(value)) {
    const date = new Date(`${value}-01T00:00:00`);

    return date.toLocaleDateString("en-IN", {
      month: "short",
      year: "2-digit",
    });
  }

  return value;
}

function MonthlySpendingChart({ data }) {
  const series = getSeries(data, "month");

  if (!series.length) {
    return (
      <p className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
        No monthly spending data available.
      </p>
    );
  }

  const width = 720;
  const height = 250;
  const paddingLeft = 52;
  const paddingRight = 24;
  const paddingTop = 20;
  const paddingBottom = 48;

  const maxValue = Math.max(
    1,
    ...series.map((item) => item.amount)
  );

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const points = series.map((item, index) => {
    const x = series.length === 1
      ? paddingLeft + chartWidth / 2
      : paddingLeft +
        (index / (series.length - 1)) * chartWidth;

    const y = paddingTop +
      chartHeight -
      (Math.max(0, item.amount) / maxValue) * chartHeight;

    return { ...item, x, y };
  });

  const pointString = points
    .map((point) => `${point.x},${point.y}`)
    .join(" ");

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Monthly spending line chart"
        className="w-full min-w-[420px]"
      >
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = paddingTop + chartHeight * ratio;
          const value = maxValue * (1 - ratio);

          return (
            <g key={ratio}>
              <line
                x1={paddingLeft}
                y1={y}
                x2={width - paddingRight}
                y2={y}
                stroke="currentColor"
                opacity="0.12"
              />
              <text
                x={paddingLeft - 8}
                y={y + 4}
                fontSize="10"
                textAnchor="end"
                fill="currentColor"
                opacity="0.7"
              >
                {value.toLocaleString("en-IN", {
                  notation: "compact",
                  maximumFractionDigits: 1,
                })}
              </text>
            </g>
          );
        })}

        {points.length > 1 && (
          <polyline
            points={pointString}
            fill="none"
            stroke="#2563eb"
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        )}

        {points.map((point) => (
          <g key={point.label}>
            <circle
              cx={point.x}
              cy={point.y}
              r="4.5"
              fill="#2563eb"
              stroke="white"
              strokeWidth="2"
            >
              <title>
                {point.label}: {formatCurrency(point.amount)}
              </title>
            </circle>

            <text
              x={point.x}
              y={height - 20}
              fontSize="10"
              textAnchor="middle"
              fill="currentColor"
              opacity="0.8"
            >
              {formatMonthLabel(point.label)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function CategorySpendingChart({ data }) {
  const series = getSeries(data, "category")
    .filter((item) => item.amount >= 0)
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 8);

  if (!series.length) {
    return (
      <p className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
        No category spending data available.
      </p>
    );
  }

  const maxValue = Math.max(
    1,
    ...series.map((item) => item.amount)
  );

  return (
    <div className="space-y-4">
      {series.map((item, index) => (
        <div key={item.label}>
          <div className="mb-1 flex items-center justify-between gap-3 text-sm">
            <span className="truncate text-slate-700 dark:text-slate-300">
              {item.label}
            </span>
            <span className="shrink-0 font-medium text-slate-900 dark:text-white">
              {formatCurrency(item.amount)}
            </span>
          </div>

          <div className="h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{
                width: `${Math.min(
                  100,
                  (item.amount / maxValue) * 100
                )}%`,
                backgroundColor: CHART_COLORS[index % CHART_COLORS.length],
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function polarToCartesian(cx, cy, radius, angle) {
  const radians = (angle * Math.PI) / 180;

  return {
    x: cx + radius * Math.cos(radians),
    y: cy + radius * Math.sin(radians),
  };
}

function describePieSlice(startAngle, endAngle) {
  const center = 100;
  const radius = 78;
  const start = polarToCartesian(center, center, radius, startAngle);
  const end = polarToCartesian(center, center, radius, endAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;

  return [
    `M ${center} ${center}`,
    `L ${start.x} ${start.y}`,
    `A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y}`,
    "Z",
  ].join(" ");
}

function CategoryPieChart({ data }) {
  const series = getSeries(data, "category")
    .filter((item) => item.amount > 0)
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 8);

  const total = series.reduce(
    (sum, item) => sum + item.amount,
    0
  );

  if (!series.length || total <= 0) {
    return (
      <p className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
        No category distribution available.
      </p>
    );
  }

  let currentAngle = -90;

  const slices = series.map((item, index) => {
    const angle = (item.amount / total) * 360;
    const slice = {
      ...item,
      color: CHART_COLORS[index % CHART_COLORS.length],
      startAngle: currentAngle,
      endAngle: currentAngle + angle,
    };

    currentAngle += angle;

    return slice;
  });

  return (
    <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-center">
      <svg
        viewBox="0 0 200 200"
        role="img"
        aria-label="Category spending pie chart"
        className="w-full max-w-[220px] shrink-0"
      >
        {slices.length === 1 ? (
          <circle
            cx="100"
            cy="100"
            r="78"
            fill={slices[0].color}
          />
        ) : (
          slices.map((slice) => (
            <path
              key={slice.label}
              d={describePieSlice(
                slice.startAngle,
                slice.endAngle
              )}
              fill={slice.color}
              stroke="white"
              strokeWidth="1.5"
            >
              <title>
                {slice.label}: {formatCurrency(slice.amount)}
              </title>
            </path>
          ))
        )}
      </svg>

      <div className="w-full min-w-0 space-y-3">
        {slices.map((slice) => (
          <div
            key={slice.label}
            className="flex items-start gap-2 text-sm"
          >
            <span
              className="mt-1 h-3 w-3 shrink-0 rounded-sm"
              style={{ backgroundColor: slice.color }}
            />

            <div className="min-w-0 flex-1">
              <p className="break-words text-slate-700 dark:text-slate-300">
                {slice.label}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {((slice.amount / total) * 100).toFixed(1)}% ·{" "}
                {formatCurrency(slice.amount)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CreditUtilizationCard({ data }) {
  const limit = Number(data?.total_credit_limit ?? data?.credit_limit ?? 0);
  const used = Number(data?.used_credit ?? data?.spent ?? 0);

  const calculatedPercentage = limit > 0
    ? (used / limit) * 100
    : 0;

  const rawPercentage = Number(
    data?.utilization_percent ?? calculatedPercentage
  );

  const percentage = Number.isFinite(rawPercentage)
    ? Math.min(100, Math.max(0, rawPercentage))
    : 0;

  return (
    <section className="rounded-xl bg-white p-5 shadow-sm dark:bg-slate-800 sm:p-6">
      <h3 className="text-lg font-bold text-slate-900 dark:text-white">
        Credit Utilization
      </h3>

      <div className="mt-5 flex items-center gap-5">
        <div
          className="relative grid h-28 w-28 shrink-0 place-items-center rounded-full"
          style={{
            background: `conic-gradient(#2563eb ${percentage * 3.6}deg, #e2e8f0 0deg)`,
          }}
          role="img"
          aria-label={`Credit utilization ${percentage.toFixed(1)} percent`}
        >
          <div className="grid h-20 w-20 place-items-center rounded-full bg-white dark:bg-slate-800">
            <span className="text-xl font-bold text-slate-900 dark:text-white">
              {percentage.toFixed(1)}%
            </span>
          </div>
        </div>

        <div className="min-w-0 space-y-2 text-sm">
          <div>
            <p className="text-slate-500 dark:text-slate-400">
              Used credit
            </p>
            <p className="font-semibold text-slate-900 dark:text-white">
              {formatCurrency(used)}
            </p>
          </div>

          <div>
            <p className="text-slate-500 dark:text-slate-400">
              Total credit limit
            </p>
            <p className="font-semibold text-slate-900 dark:text-white">
              {formatCurrency(limit)}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function HealthValue({ label, value }) {
  const normalized = String(value ?? "unknown").toLowerCase();
  const healthy = ["healthy", "ok", "running", "connected"].includes(normalized);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 py-3 last:border-b-0 dark:border-slate-700">
      <span className="text-sm text-slate-600 dark:text-slate-300">
        {label}
      </span>

      <span
        className={`rounded-full px-3 py-1 text-xs font-semibold ${
          healthy
            ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
            : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
        }`}
      >
        {String(value ?? "Unknown")}
      </span>
    </div>
  );
}

function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [cards, setCards] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [health, setHealth] = useState(null);

  const [creditLimitDrafts, setCreditLimitDrafts] = useState({});

  const [error, setError] = useState("");
  const [analyticsError, setAnalyticsError] = useState("");
  const [healthError, setHealthError] = useState("");

  const [loading, setLoading] = useState(true);
  const [cardsLoading, setCardsLoading] = useState(true);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [healthLoading, setHealthLoading] = useState(true);

  const [updatingCardId, setUpdatingCardId] = useState(null);
  const [exportingFormat, setExportingFormat] = useState("");

  const permissions = summary?.permissions ?? {};
  const canManageCardStatus = Boolean(permissions.can_manage_card_status);
  const canUpdateCreditLimit = Boolean(permissions.can_update_credit_limit);
  const canExportTransactions = Boolean(permissions.can_export_transactions);

  const loadAdminData = useCallback(async () => {
    setLoading(true);
    setCardsLoading(true);
    setAnalyticsLoading(true);
    setHealthLoading(true);

    setError("");
    setAnalyticsError("");
    setHealthError("");

    const results = await Promise.allSettled([
      djangoApi.get("/admin/dashboard/"),
      djangoApi.get("/admin/cards/"),
      djangoApi.get("/admin/analytics/"),
      djangoApi.get("/admin/health/"),
    ]);

    const [
      summaryResult,
      cardsResult,
      analyticsResult,
      healthResult,
    ] = results;

    const coreErrors = [];

    if (summaryResult.status === "fulfilled") {
      setSummary(summaryResult.value.data);
    } else {
      setSummary(null);

      const code = summaryResult.reason?.response?.status;

      coreErrors.push(
        code === 401 || code === 403
          ? "You do not have permission to access the admin dashboard."
          : "Unable to load the admin dashboard summary."
      );
    }

    if (cardsResult.status === "fulfilled") {
      const cardData = Array.isArray(cardsResult.value.data)
        ? cardsResult.value.data
        : [];

      setCards(cardData);

      const drafts = {};

      cardData.forEach((card) => {
        drafts[card.id] = String(card.credit_limit ?? 0);
      });

      setCreditLimitDrafts(drafts);
    } else {
      setCards([]);

      const code = cardsResult.reason?.response?.status;

      coreErrors.push(
        code === 401 || code === 403
          ? "You do not have permission to view card management."
          : "Unable to load card information."
      );
    }

    if (analyticsResult.status === "fulfilled") {
      setAnalytics(analyticsResult.value.data);
    } else {
      setAnalytics(null);
      setAnalyticsError(
        "Analytics are currently unavailable. The analytics API must be enabled on the backend."
      );
    }

    if (healthResult.status === "fulfilled") {
      setHealth(healthResult.value.data);
    } else {
      setHealth(null);
      setHealthError(
        "System health information is currently unavailable."
      );
    }

    setError(coreErrors.join(" "));
    setLoading(false);
    setCardsLoading(false);
    setAnalyticsLoading(false);
    setHealthLoading(false);
  }, []);

  useEffect(() => {
    loadAdminData();
  }, [loadAdminData]);

  const downloadBlob = (data, filename, contentType) => {
    const blob = new Blob([data], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    link.remove();

    window.URL.revokeObjectURL(url);
  };

  const handleExportTransactions = async () => {
    setError("");

    try {
      const response = await djangoApi.get(
        "/admin/transactions/export/",
        { responseType: "blob" }
      );

      downloadBlob(
        response.data,
        "transactions.csv",
        "text/csv"
      );
    } catch {
      setError("Unable to export transactions.");
    }
  };

  const handleAnalyticsExport = async (format) => {
    setExportingFormat(format);
    setError("");

    try {
      const response = await djangoApi.get(
        "/admin/analytics/export/",
        {
          params: { format },
          responseType: "blob",
        }
      );

      const extension = format === "pdf" ? "pdf" : "csv";
      const contentType = format === "pdf"
        ? "application/pdf"
        : "text/csv";

      downloadBlob(
        response.data,
        `creditpay-analytics.${extension}`,
        contentType
      );
    } catch {
      setError(`Unable to export analytics as ${format.toUpperCase()}.`);
    } finally {
      setExportingFormat("");
    }
  };

  const handleCardStatusChange = async (card) => {
    const action = card.is_active ? "block" : "unblock";

    const confirmed = window.confirm(
      `Are you sure you want to ${action} this card (${card.masked_number})?`
    );

    if (!confirmed) return;

    setUpdatingCardId(card.id);
    setError("");

    try {
      const response = await djangoApi.patch(
        `/admin/cards/${card.id}/`,
        { is_active: !card.is_active }
      );

      const updatedCard = response.data;

      setCards((currentCards) =>
        currentCards.map((currentCard) =>
          currentCard.id === updatedCard.id
            ? updatedCard
            : currentCard
        )
      );

      setCreditLimitDrafts((currentDrafts) => ({
        ...currentDrafts,
        [updatedCard.id]: String(updatedCard.credit_limit ?? 0),
      }));
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
        `Unable to ${action} the card.`
      );
    } finally {
      setUpdatingCardId(null);
    }
  };

  const handleCreditLimitChange = (cardId, value) => {
    setCreditLimitDrafts((currentDrafts) => ({
      ...currentDrafts,
      [cardId]: value,
    }));
  };

  const handleCreditLimitSave = async (card) => {
    const rawValue = creditLimitDrafts[card.id];

    if (rawValue === undefined || rawValue === "") {
      setError("Please enter a credit limit.");
      return;
    }

    const numericValue = Number(rawValue);

    if (!Number.isFinite(numericValue) || numericValue < 0) {
      setError("Credit limit must be a valid non-negative number.");
      return;
    }

    if (card.card_type === "CREDIT" && numericValue <= 0) {
      setError("Credit cards must have a positive credit limit.");
      return;
    }

    if (card.card_type === "DEBIT" && numericValue !== 0) {
      setError("Debit cards must have a credit limit of 0.");
      return;
    }

    if (numericValue === Number(card.credit_limit || 0)) {
      return;
    }

    setUpdatingCardId(card.id);
    setError("");

    try {
      const response = await djangoApi.patch(
        `/admin/cards/${card.id}/`,
        { credit_limit: numericValue }
      );

      const updatedCard = response.data;

      setCards((currentCards) =>
        currentCards.map((currentCard) =>
          currentCard.id === updatedCard.id
            ? updatedCard
            : currentCard
        )
      );

      setCreditLimitDrafts((currentDrafts) => ({
        ...currentDrafts,
        [updatedCard.id]: String(updatedCard.credit_limit ?? 0),
      }));
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
        "Unable to update the credit limit."
      );
    } finally {
      setUpdatingCardId(null);
    }
  };

  const summaryCards = [
    {
      label: "Total Transactions",
      value: summary?.total_transactions ?? 0,
      className: "text-slate-900 dark:text-white",
    },
    {
      label: "Total Amount",
      value: formatCurrency(summary?.total_amount ?? 0),
      className: "text-blue-600 dark:text-blue-400",
    },
    {
      label: "Successful",
      value: summary?.success_count ?? 0,
      className: "text-green-600 dark:text-green-400",
    },
    {
      label: "Failed",
      value: summary?.failed_count ?? 0,
      className: "text-red-600 dark:text-red-400",
    },
    {
      label: "Pending",
      value: summary?.pending_count ?? 0,
      className: "text-yellow-600 dark:text-yellow-400",
    },
  ];

  const utilization = analytics?.credit_utilization ?? {};

  return (
    <div className="theme-transition min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <Navbar />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
              Admin Dashboard
            </h1>
            <p className="mt-2 text-slate-600 dark:text-slate-400">
              Monitor payment activity, analytics, system health, and customer cards.
            </p>
          </div>

          {canExportTransactions && (
            <button
              type="button"
              onClick={handleExportTransactions}
              className="rounded-lg bg-slate-900 px-5 py-3 font-semibold text-white transition-colors hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white dark:focus:ring-offset-slate-950"
            >
              Export Transactions CSV
            </button>
          )}
        </div>

        {error && (
          <div
            role="alert"
            className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300"
          >
            {error}
          </div>
        )}

        {/* EXISTING DAILY SUMMARY */}
        {loading ? (
          <div className="mt-8 rounded-xl bg-white p-10 text-center shadow-sm dark:bg-slate-800">
            <p className="text-slate-500 dark:text-slate-400">
              Loading admin dashboard...
            </p>
          </div>
        ) : summary ? (
          <>
            <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
              {summaryCards.map((item) => (
                <div
                  key={item.label}
                  className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800"
                >
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {item.label}
                  </p>
                  <p className={`mt-2 break-words text-2xl font-bold ${item.className}`}>
                    {item.value}
                  </p>
                </div>
              ))}
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
                    width: summary.total_transactions > 0
                      ? `${(summary.success_count / summary.total_transactions) * 100}%`
                      : "0%",
                  }}
                />
              </div>
            </div>
          </>
        ) : null}

        {/* ANALYTICS AND REPORT EXPORTS */}
        <section className="mt-8">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                Analytics & Reports
              </h2>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                Monthly spending, category expenses and credit utilization.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => handleAnalyticsExport("csv")}
                disabled={Boolean(exportingFormat)}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                {exportingFormat === "csv" ? "Exporting..." : "Analytics CSV"}
              </button>

              <button
                type="button"
                onClick={() => handleAnalyticsExport("pdf")}
                disabled={Boolean(exportingFormat)}
                className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60"
              >
                {exportingFormat === "pdf" ? "Exporting..." : "Analytics PDF"}
              </button>
            </div>
          </div>

          {analyticsLoading ? (
            <div className="mt-5 rounded-xl bg-white p-10 text-center shadow-sm dark:bg-slate-800">
              <p className="text-slate-500 dark:text-slate-400">
                Loading analytics...
              </p>
            </div>
          ) : analyticsError ? (
            <div
              role="status"
              className="mt-5 rounded-xl border border-yellow-200 bg-yellow-50 p-5 text-sm text-yellow-800 dark:border-yellow-900/50 dark:bg-yellow-950/30 dark:text-yellow-200"
            >
              {analyticsError}
            </div>
          ) : (
            <>
              <div className="mt-5">
                <ChartPanel title="Monthly Spending">
                  <MonthlySpendingChart
                    data={analytics?.monthly_spending}
                  />
                </ChartPanel>
              </div>

              <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
                <ChartPanel title="Category-wise Expenses">
                  <CategorySpendingChart
                    data={analytics?.category_spending}
                  />
                </ChartPanel>

                <ChartPanel title="Expense Distribution">
                  <CategoryPieChart
                    data={analytics?.category_spending}
                  />
                </ChartPanel>
              </div>

              <div className="mt-5">
                <CreditUtilizationCard data={utilization} />
              </div>
            </>
          )}
        </section>

        {/* SYSTEM HEALTH */}
        <section className="mt-8 rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                System Health
              </h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                Basic API and database health information.
              </p>
            </div>

            <button
              type="button"
              onClick={loadAdminData}
              disabled={healthLoading || loading}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              Refresh Status
            </button>
          </div>

          {healthLoading ? (
            <p className="mt-5 text-sm text-slate-500 dark:text-slate-400">
              Checking system health...
            </p>
          ) : healthError ? (
            <p
              role="status"
              className="mt-5 text-sm text-yellow-700 dark:text-yellow-300"
            >
              {healthError}
            </p>
          ) : (
            <div className="mt-4 divide-y divide-slate-100 dark:divide-slate-700">
              <HealthValue
                label="Application status"
                value={health?.status}
              />
              <HealthValue
                label="Database status"
                value={health?.database_status ?? health?.database}
              />
              {health?.response_time_ms !== undefined && (
                <HealthValue
                  label="Latest response time"
                  value={`${health.response_time_ms} ms`}
                />
              )}
              <div className="pt-3 text-xs text-slate-500 dark:text-slate-400">
                Last checked: {formatDate(health?.checked_at ?? health?.timestamp)}
              </div>
            </div>
          )}
        </section>

        {/* EXISTING CARD MANAGEMENT */}
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
                    {[
                      "Cardholder",
                      "Card",
                      "Expiry",
                      "Status",
                      "Credit Limit",
                      "Available",
                      "Spent",
                      "Transactions",
                      "Last Activity",
                      "Actions",
                    ].map((heading) => (
                      <th
                        key={heading}
                        className="whitespace-nowrap px-4 py-3 font-medium"
                      >
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {cards.map((card) => {
                    const isUpdating = updatingCardId === card.id;

                    return (
                      <tr
                        key={card.id}
                        className="transition-colors hover:bg-slate-50 dark:hover:bg-slate-900/60"
                      >
                        <td className="px-4 py-4">
                          <p className="font-semibold text-slate-900 dark:text-white">
                            {card.username}
                          </p>
                          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                            {card.email}
                          </p>
                        </td>

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

                        <td className="whitespace-nowrap px-4 py-4 text-slate-600 dark:text-slate-300">
                          {card.expiry_month}/{card.expiry_year}
                        </td>

                        <td className="px-4 py-4">
                          <span
                            className={
                              card.is_active
                                ? "rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700 dark:bg-green-900/30 dark:text-green-300"
                                : "rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700 dark:bg-red-900/30 dark:text-red-300"
                            }
                          >
                            {card.is_active ? "Active" : "Blocked"}
                          </span>
                        </td>

                        <td className="px-4 py-4">
                          {canUpdateCreditLimit ? (
                            <div className="flex min-w-[190px] items-center gap-2">
                              <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={creditLimitDrafts[card.id] ?? ""}
                                onChange={(event) =>
                                  handleCreditLimitChange(
                                    card.id,
                                    event.target.value
                                  )
                                }
                                disabled={isUpdating}
                                aria-label={`Credit limit for ${card.masked_number}`}
                                className="w-32 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:opacity-60 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                              />

                              <button
                                type="button"
                                onClick={() => handleCreditLimitSave(card)}
                                disabled={isUpdating}
                                className="rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60"
                              >
                                Save
                              </button>
                            </div>
                          ) : (
                            <span className="whitespace-nowrap text-slate-700 dark:text-slate-300">
                              {formatCurrency(card.credit_limit)}
                            </span>
                          )}
                        </td>

                        <td className="whitespace-nowrap px-4 py-4 font-medium text-blue-600 dark:text-blue-400">
                          {formatCurrency(card.available_credit)}
                        </td>

                        <td className="whitespace-nowrap px-4 py-4 text-slate-700 dark:text-slate-300">
                          {formatCurrency(card.spent_amount)}
                        </td>

                        <td className="px-4 py-4 text-center text-slate-700 dark:text-slate-300">
                          {card.transaction_count}
                        </td>

                        <td className="whitespace-nowrap px-4 py-4 text-slate-600 dark:text-slate-300">
                          {formatDate(card.last_activity)}
                        </td>

                        <td className="px-4 py-4">
                          {canManageCardStatus ? (
                            <button
                              type="button"
                              onClick={() => handleCardStatusChange(card)}
                              disabled={isUpdating}
                              aria-label={
                                card.is_active
                                  ? `Block ${card.masked_number}`
                                  : `Unblock ${card.masked_number}`
                              }
                              className={
                                card.is_active
                                  ? "whitespace-nowrap rounded-lg bg-red-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-red-700 disabled:opacity-60"
                                  : "whitespace-nowrap rounded-lg bg-green-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-green-700 disabled:opacity-60"
                              }
                            >
                              {isUpdating
                                ? "Updating..."
                                : card.is_active
                                  ? "Block"
                                  : "Unblock"}
                            </button>
                          ) : (
                            <span className="text-xs text-slate-500 dark:text-slate-400">
                              View only
                            </span>
                          )}
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
