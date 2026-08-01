export default function HomePage() {
  return (
    <main className="page">
      <header className="hero">
        <p className="eyebrow">WingSaver</p>
        <h1>Airline search, done right</h1>
        <p className="lede">
          Production-grade flight search. Scaffold is live — search UI arrives in a later PR.
        </p>
        <p className="meta">
          API base:{" "}
          <code>{process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"}</code>
        </p>
      </header>
    </main>
  );
}
