import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link href="/" className="brand">
        WingSaver
      </Link>
      <nav aria-label="Primary">
        <Link href="/">Search</Link>
      </nav>
    </header>
  );
}
