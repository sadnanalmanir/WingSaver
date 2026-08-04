import { Link } from "react-router-dom";

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link to="/" className="brand">
        WingSaver
      </Link>
      <nav aria-label="Primary">
        <Link to="/">Search</Link>
      </nav>
    </header>
  );
}
