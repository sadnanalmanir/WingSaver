import type { Metadata } from "next";
import { Suspense } from "react";

import { SearchResults } from "@/components/search-results";

export const metadata: Metadata = {
  title: "Search results",
};

function SearchFallback() {
  return (
    <div className="stack" aria-busy="true">
      <div className="skeleton offer-skeleton" />
      <p className="muted">Loading search…</p>
    </div>
  );
}

export default function SearchPage() {
  return (
    <main>
      <Suspense fallback={<SearchFallback />}>
        <SearchResults />
      </Suspense>
    </main>
  );
}
