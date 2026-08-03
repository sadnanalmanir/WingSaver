import { SearchForm } from "@/components/search-form";
import { getApiBaseUrl } from "@/lib/api-client";

export default function HomePage() {
  return (
    <main>
      <section className="home-hero">
        <p className="eyebrow">WingSaver</p>
        <h1 className="h1">Airline search, done right</h1>
        <p className="lede">
          Search one-way or round-trip flights. Filters and sort run on the server.
          Prices are estimates in the provider&apos;s currency — not a booking lock.
        </p>
      </section>
      <SearchForm />
      <p className="muted small" style={{ marginTop: "1rem" }}>
        API: <code>{getApiBaseUrl()}</code>
      </p>
    </main>
  );
}
