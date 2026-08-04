import { Navigate, Route, Routes } from "react-router-dom";

import { SiteHeader } from "@/components/site-header";
import { FlightDetailPage } from "@/pages/flight-detail";
import { HomePage } from "@/pages/home";
import { SearchPage } from "@/pages/search";

export function App() {
  return (
    <div className="shell">
      <SiteHeader />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/flights/:offerId" element={<FlightDetailPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
