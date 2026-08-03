import type { Money, OfferPublic, Slice } from "@/lib/types";

export function formatMoney(price: Money): string {
  const amount = Number(price.amount);
  if (Number.isFinite(amount)) {
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: price.currency,
        maximumFractionDigits: 2,
      }).format(amount);
    } catch {
      // invalid currency code
    }
  }
  return `${price.amount} ${price.currency}`;
}

export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h <= 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(d);
}

export function stopsLabel(stops: number): string {
  if (stops === 0) return "Nonstop";
  if (stops === 1) return "1 stop";
  return `${stops} stops`;
}

export function maxStopsOnOffer(offer: OfferPublic): number {
  return Math.max(0, ...offer.slices.map((s) => s.stops));
}

export function totalDuration(offer: OfferPublic): number {
  return offer.slices.reduce((sum, s) => sum + s.duration_minutes, 0);
}

export function sliceRoute(slice: Slice): string {
  const first = slice.segments[0];
  const last = slice.segments[slice.segments.length - 1];
  if (!first || !last) return "";
  return `${first.origin} → ${last.destination}`;
}
