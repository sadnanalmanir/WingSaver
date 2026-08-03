import type { CabinClass, SearchRequest, SearchSort, TripType } from "@/lib/types";

function tomorrowIso(): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + 14);
  return d.toISOString().slice(0, 10);
}

function plusDaysIso(iso: string, days: number): string {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export type SearchFormState = {
  trip_type: TripType;
  origin: string;
  destination: string;
  departure_date: string;
  return_date: string;
  adults: number;
  children: number;
  infants: number;
  cabin_class: CabinClass;
  currency: string;
  sort: SearchSort;
  page: number;
  page_size: number;
  max_stops: string; // "" | "0" | "1" | "2"
  max_price: string;
  airlines: string;
};

export function defaultFormState(): SearchFormState {
  const departure = tomorrowIso();
  return {
    trip_type: "round_trip",
    origin: "JFK",
    destination: "LHR",
    departure_date: departure,
    return_date: plusDaysIso(departure, 10),
    adults: 1,
    children: 0,
    infants: 0,
    cabin_class: "economy",
    currency: "USD",
    sort: "price_asc",
    page: 1,
    page_size: 10,
    max_stops: "",
    max_price: "",
    airlines: "",
  };
}

export function formFromSearchParams(params: URLSearchParams): SearchFormState {
  const base = defaultFormState();
  const trip = params.get("trip_type") ?? params.get("trip");
  if (trip === "one_way" || trip === "round_trip") base.trip_type = trip;

  base.origin = (params.get("from") ?? params.get("origin") ?? base.origin).toUpperCase();
  base.destination = (params.get("to") ?? params.get("destination") ?? base.destination).toUpperCase();
  base.departure_date = params.get("depart") ?? params.get("departure_date") ?? base.departure_date;
  base.return_date = params.get("return") ?? params.get("return_date") ?? base.return_date;

  const adults = Number(params.get("adults"));
  if (Number.isFinite(adults) && adults >= 1) base.adults = adults;
  const children = Number(params.get("children"));
  if (Number.isFinite(children) && children >= 0) base.children = children;
  const infants = Number(params.get("infants"));
  if (Number.isFinite(infants) && infants >= 0) base.infants = infants;

  const cabin = params.get("cabin") ?? params.get("cabin_class");
  if (
    cabin === "economy" ||
    cabin === "premium_economy" ||
    cabin === "business" ||
    cabin === "first"
  ) {
    base.cabin_class = cabin;
  }

  base.currency = (params.get("currency") ?? base.currency).toUpperCase();

  const sort = params.get("sort");
  if (
    sort === "price_asc" ||
    sort === "price_desc" ||
    sort === "duration_asc" ||
    sort === "departure_asc"
  ) {
    base.sort = sort;
  }

  const page = Number(params.get("page"));
  if (Number.isFinite(page) && page >= 1) base.page = page;
  const pageSize = Number(params.get("page_size"));
  if (Number.isFinite(pageSize) && pageSize >= 1 && pageSize <= 50) base.page_size = pageSize;

  const stops = params.get("stops") ?? params.get("max_stops");
  if (stops === "0" || stops === "1" || stops === "2") base.max_stops = stops;

  base.max_price = params.get("max_price") ?? "";
  base.airlines = (params.get("airlines") ?? "").toUpperCase();

  return base;
}

export function formToSearchParams(form: SearchFormState): URLSearchParams {
  const p = new URLSearchParams();
  p.set("trip_type", form.trip_type);
  p.set("from", form.origin.toUpperCase());
  p.set("to", form.destination.toUpperCase());
  p.set("depart", form.departure_date);
  if (form.trip_type === "round_trip" && form.return_date) {
    p.set("return", form.return_date);
  }
  p.set("adults", String(form.adults));
  if (form.children > 0) p.set("children", String(form.children));
  if (form.infants > 0) p.set("infants", String(form.infants));
  p.set("cabin", form.cabin_class);
  p.set("currency", form.currency);
  p.set("sort", form.sort);
  p.set("page", String(form.page));
  p.set("page_size", String(form.page_size));
  if (form.max_stops !== "") p.set("max_stops", form.max_stops);
  if (form.max_price.trim()) p.set("max_price", form.max_price.trim());
  if (form.airlines.trim()) p.set("airlines", form.airlines.trim().toUpperCase());
  return p;
}

export function formToSearchRequest(form: SearchFormState): SearchRequest {
  const airlines = form.airlines
    .split(/[,\s]+/)
    .map((a) => a.trim().toUpperCase())
    .filter(Boolean);

  const filters =
    form.max_stops !== "" || form.max_price.trim() || airlines.length
      ? {
          max_stops: form.max_stops === "" ? null : Number(form.max_stops),
          max_price: form.max_price.trim() ? Number(form.max_price) : null,
          airlines: airlines.length ? airlines : null,
        }
      : null;

  return {
    trip_type: form.trip_type,
    origin: form.origin.toUpperCase(),
    destination: form.destination.toUpperCase(),
    departure_date: form.departure_date,
    return_date: form.trip_type === "round_trip" ? form.return_date || null : null,
    passengers: {
      adults: form.adults,
      children: form.children,
      infants: form.infants,
    },
    cabin_class: form.cabin_class,
    currency: form.currency.toUpperCase(),
    filters,
    sort: form.sort,
    page: form.page,
    page_size: form.page_size,
  };
}

export function searchHref(form: SearchFormState): string {
  return `/search?${formToSearchParams(form).toString()}`;
}
