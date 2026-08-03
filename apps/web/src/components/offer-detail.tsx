"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { ErrorPanel } from "@/components/error-panel";
import { PriceDisclaimer } from "@/components/price-disclaimer";
import { getOffer } from "@/lib/api-client";
import {
  formatDateTime,
  formatDuration,
  formatMoney,
  stopsLabel,
} from "@/lib/format";
import { queryKeys } from "@/lib/query-keys";
import { ApiError } from "@/lib/types";

export function OfferDetail({ offerId }: { offerId: string }) {
  const query = useQuery({
    queryKey: queryKeys.offer(offerId),
    queryFn: ({ signal }) => getOffer(offerId, signal),
  });

  if (query.isLoading) {
    return (
      <div className="stack" aria-busy="true">
        <div className="skeleton detail-skeleton" />
        <p className="muted">Loading offer…</p>
      </div>
    );
  }

  if (query.isError) {
    const err = query.error;
    const expired = err instanceof ApiError && err.code === "OFFER_NOT_FOUND";
    return (
      <div className="stack">
        <ErrorPanel
          error={err}
          title={expired ? "This offer expired" : "Could not load offer"}
        />
        {expired ? (
          <p>
            Offers are only kept for a limited time.{" "}
            <Link href="/">Search again</Link> for current prices.
          </p>
        ) : null}
      </div>
    );
  }

  const offer = query.data;
  if (!offer) return null;

  return (
    <article className="stack detail">
      <header className="detail-header panel">
        <div>
          <p className="eyebrow">{offer.validating_airline}</p>
          <h1 className="h1">{formatMoney(offer.price)}</h1>
          <p className="muted">
            {offer.cabin_class.replaceAll("_", " ")} · provider {offer.provider}
          </p>
        </div>
        <Link className="btn secondary" href="/">
          New search
        </Link>
      </header>

      <PriceDisclaimer />

      {offer.baggage_summary ? (
        <p className="panel muted">Baggage: {offer.baggage_summary}</p>
      ) : null}

      {offer.slices.map((slice) => (
        <section key={`${slice.direction}-${slice.duration_minutes}`} className="panel">
          <h2 className="h2">
            {slice.direction === "outbound" ? "Outbound" : "Return"} ·{" "}
            {stopsLabel(slice.stops)} · {formatDuration(slice.duration_minutes)}
          </h2>
          <ol className="segments">
            {slice.segments.map((seg, idx) => (
              <li key={`${seg.flight_number}-${idx}`} className="segment">
                <div className="segment-route">
                  <strong>
                    {seg.origin} → {seg.destination}
                  </strong>
                  <span className="muted">
                    {seg.marketing_carrier}
                    {seg.flight_number.replace(seg.marketing_carrier, "")} ·{" "}
                    {formatDuration(seg.duration_minutes)}
                  </span>
                </div>
                <div className="segment-times muted">
                  <span>Dep {formatDateTime(seg.depart_at)}</span>
                  <span>Arr {formatDateTime(seg.arrive_at)}</span>
                </div>
              </li>
            ))}
          </ol>
        </section>
      ))}

      {offer.expires_at ? (
        <p className="muted small">Offer cache expires around {formatDateTime(offer.expires_at)}.</p>
      ) : null}
    </article>
  );
}
