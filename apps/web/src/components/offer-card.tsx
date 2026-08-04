import { Link } from "react-router-dom";

import {
  formatDateTime,
  formatDuration,
  formatMoney,
  maxStopsOnOffer,
  sliceRoute,
  stopsLabel,
  totalDuration,
} from "@/lib/format";
import type { OfferPublic } from "@/lib/types";

export function OfferCard({ offer }: { offer: OfferPublic }) {
  const outbound = offer.slices[0];
  const inbound = offer.slices[1];

  return (
    <article className="offer-card panel">
      <div className="offer-main">
        <div className="offer-airline">
          <span className="airline-code">{offer.validating_airline}</span>
          <span className="muted">{stopsLabel(maxStopsOnOffer(offer))}</span>
        </div>
        <div className="offer-slices">
          {outbound ? (
            <div className="slice-row">
              <span className="slice-label">Out</span>
              <span className="slice-route">{sliceRoute(outbound)}</span>
              <span className="muted">
                {formatDateTime(outbound.segments[0]?.depart_at ?? "")} ·{" "}
                {formatDuration(outbound.duration_minutes)}
              </span>
            </div>
          ) : null}
          {inbound ? (
            <div className="slice-row">
              <span className="slice-label">Ret</span>
              <span className="slice-route">{sliceRoute(inbound)}</span>
              <span className="muted">
                {formatDateTime(inbound.segments[0]?.depart_at ?? "")} ·{" "}
                {formatDuration(inbound.duration_minutes)}
              </span>
            </div>
          ) : null}
        </div>
      </div>
      <div className="offer-side">
        <p className="price">{formatMoney(offer.price)}</p>
        <p className="muted small">Total trip {formatDuration(totalDuration(offer))}</p>
        <Link className="btn secondary" to={`/flights/${encodeURIComponent(offer.id)}`}>
          View details
        </Link>
      </div>
    </article>
  );
}
