import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { ErrorPanel } from "@/components/error-panel";
import { OfferCard } from "@/components/offer-card";
import { PriceDisclaimer } from "@/components/price-disclaimer";
import { SearchForm } from "@/components/search-form";
import { searchFlights } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";
import {
  formFromSearchParams,
  formToSearchParams,
  formToSearchRequest,
  type SearchFormState,
} from "@/lib/search-params";

function ResultsSkeleton() {
  return (
    <div className="stack" aria-busy="true" aria-live="polite">
      <p className="muted">Searching flights…</p>
      {[0, 1, 2].map((i) => (
        <div key={i} className="skeleton offer-skeleton" />
      ))}
    </div>
  );
}

export function SearchResults() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const form = useMemo(() => formFromSearchParams(searchParams), [searchParams]);
  const body = useMemo(() => formToSearchRequest(form), [form]);

  const query = useQuery({
    queryKey: queryKeys.search(body),
    queryFn: ({ signal }) => searchFlights(body, signal),
  });

  function patchForm(patch: Partial<SearchFormState>) {
    const next = { ...form, ...patch };
    navigate({ pathname: "/search", search: formToSearchParams(next).toString() });
  }

  const totalPages = query.data
    ? Math.max(1, Math.ceil(query.data.total / query.data.page_size))
    : 1;

  return (
    <div className="search-layout">
      <aside className="search-sidebar stack">
        <h2 className="h2">Refine search</h2>
        <SearchForm initial={form} submitLabel="Update search" />

        <div className="panel filters">
          <h3 className="h3">Filters & sort</h3>
          <p className="muted small">Applied on the server for each request.</p>
          <label>
            Sort
            <select
              value={form.sort}
              onChange={(e) =>
                patchForm({ sort: e.target.value as SearchFormState["sort"], page: 1 })
              }
            >
              <option value="price_asc">Price (low to high)</option>
              <option value="price_desc">Price (high to low)</option>
              <option value="duration_asc">Duration (shortest)</option>
              <option value="departure_asc">Departure (earliest)</option>
            </select>
          </label>
          <label>
            Max stops
            <select
              value={form.max_stops}
              onChange={(e) => patchForm({ max_stops: e.target.value, page: 1 })}
            >
              <option value="">Any</option>
              <option value="0">Nonstop only</option>
              <option value="1">1 stop or fewer</option>
              <option value="2">2 stops or fewer</option>
            </select>
          </label>
          <label>
            Max price
            <input
              type="number"
              min={0}
              step={50}
              placeholder="e.g. 800"
              value={form.max_price}
              onChange={(e) => patchForm({ max_price: e.target.value, page: 1 })}
            />
          </label>
          <label>
            Airlines (IATA, comma-separated)
            <input
              type="text"
              placeholder="BA, AA"
              value={form.airlines}
              onChange={(e) => patchForm({ airlines: e.target.value.toUpperCase(), page: 1 })}
            />
          </label>
        </div>
      </aside>

      <section className="search-main stack" aria-live="polite">
        <header className="results-header">
          <div>
            <h1 className="h1">
              {form.origin} → {form.destination}
            </h1>
            <p className="muted">
              {form.departure_date}
              {form.trip_type === "round_trip" && form.return_date
                ? ` · return ${form.return_date}`
                : ""}
              {` · ${form.adults} adult${form.adults === 1 ? "" : "s"}`}
            </p>
          </div>
          {query.data ? (
            <p className="muted small">
              {query.data.total} result{query.data.total === 1 ? "" : "s"}
              {query.data.cache ? ` · cache ${query.data.cache}` : ""}
            </p>
          ) : null}
        </header>

        <PriceDisclaimer text={query.data?.price_disclaimer} />

        {query.isLoading || query.isFetching ? <ResultsSkeleton /> : null}

        {query.isError ? <ErrorPanel error={query.error} title="Search failed" /> : null}

        {query.isSuccess && query.data.offers.length === 0 ? (
          <div className="panel empty">
            <h2 className="h2">No flights match</h2>
            <p className="muted">
              Try relaxing filters (stops, price, airlines) or changing dates.
            </p>
            <Link className="btn secondary" to="/">
              New search
            </Link>
          </div>
        ) : null}

        {query.isSuccess && query.data.offers.length > 0 ? (
          <div className="stack offers">
            {query.data.offers.map((offer) => (
              <OfferCard key={offer.id} offer={offer} />
            ))}
          </div>
        ) : null}

        {query.isSuccess && query.data.total > query.data.page_size ? (
          <nav className="pagination" aria-label="Results pages">
            <button
              type="button"
              className="btn secondary"
              disabled={form.page <= 1}
              onClick={() => patchForm({ page: Math.max(1, form.page - 1) })}
            >
              Previous
            </button>
            <span className="muted">
              Page {form.page} of {totalPages}
            </span>
            <button
              type="button"
              className="btn secondary"
              disabled={form.page >= totalPages}
              onClick={() => patchForm({ page: form.page + 1 })}
            >
              Next
            </button>
          </nav>
        ) : null}
      </section>
    </div>
  );
}
