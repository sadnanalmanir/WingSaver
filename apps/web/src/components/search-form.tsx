import { useMemo, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { AIRPORTS, airportLabel } from "@/lib/airports";
import {
  defaultFormState,
  searchHref,
  type SearchFormState,
} from "@/lib/search-params";

type Props = {
  initial?: Partial<SearchFormState>;
  submitLabel?: string;
};

export function SearchForm({ initial, submitLabel = "Search flights" }: Props) {
  const navigate = useNavigate();
  const [form, setForm] = useState<SearchFormState>(() => ({
    ...defaultFormState(),
    ...initial,
  }));

  const airportOptions = useMemo(
    () =>
      AIRPORTS.map((a) => (
        <option key={a.iata} value={a.iata}>
          {airportLabel(a)}
        </option>
      )),
    [],
  );

  function update<K extends keyof SearchFormState>(key: K, value: SearchFormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const next = {
      ...form,
      page: 1,
      origin: form.origin.toUpperCase(),
      destination: form.destination.toUpperCase(),
    };
    navigate(searchHref(next));
  }

  return (
    <form className="search-form panel" onSubmit={onSubmit} noValidate>
      <fieldset className="trip-type">
        <legend className="sr-only">Trip type</legend>
        <label className="radio">
          <input
            type="radio"
            name="trip_type"
            checked={form.trip_type === "round_trip"}
            onChange={() => update("trip_type", "round_trip")}
          />
          Round trip
        </label>
        <label className="radio">
          <input
            type="radio"
            name="trip_type"
            checked={form.trip_type === "one_way"}
            onChange={() => update("trip_type", "one_way")}
          />
          One way
        </label>
      </fieldset>

      <div className="form-grid">
        <label>
          Origin
          <input
            list="airport-list"
            name="origin"
            required
            maxLength={3}
            value={form.origin}
            onChange={(e) => update("origin", e.target.value.toUpperCase())}
            autoComplete="off"
            aria-required
          />
        </label>
        <label>
          Destination
          <input
            list="airport-list"
            name="destination"
            required
            maxLength={3}
            value={form.destination}
            onChange={(e) => update("destination", e.target.value.toUpperCase())}
            autoComplete="off"
            aria-required
          />
        </label>
        <datalist id="airport-list">{airportOptions}</datalist>

        <label>
          Departure
          <input
            type="date"
            name="departure_date"
            required
            value={form.departure_date}
            onChange={(e) => update("departure_date", e.target.value)}
          />
        </label>
        {form.trip_type === "round_trip" ? (
          <label>
            Return
            <input
              type="date"
              name="return_date"
              required
              value={form.return_date}
              min={form.departure_date}
              onChange={(e) => update("return_date", e.target.value)}
            />
          </label>
        ) : (
          <div aria-hidden className="form-spacer" />
        )}

        <label>
          Adults
          <input
            type="number"
            min={1}
            max={9}
            value={form.adults}
            onChange={(e) => update("adults", Number(e.target.value) || 1)}
          />
        </label>
        <label>
          Children
          <input
            type="number"
            min={0}
            max={9}
            value={form.children}
            onChange={(e) => update("children", Number(e.target.value) || 0)}
          />
        </label>
        <label>
          Infants
          <input
            type="number"
            min={0}
            max={9}
            value={form.infants}
            onChange={(e) => update("infants", Number(e.target.value) || 0)}
          />
        </label>
        <label>
          Cabin
          <select
            value={form.cabin_class}
            onChange={(e) => update("cabin_class", e.target.value as SearchFormState["cabin_class"])}
          >
            <option value="economy">Economy</option>
            <option value="premium_economy">Premium economy</option>
            <option value="business">Business</option>
            <option value="first">First</option>
          </select>
        </label>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn primary">
          {submitLabel}
        </button>
      </div>
    </form>
  );
}
