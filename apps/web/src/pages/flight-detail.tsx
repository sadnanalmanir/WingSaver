import { useParams } from "react-router-dom";

import { OfferDetail } from "@/components/offer-detail";

export function FlightDetailPage() {
  const { offerId } = useParams<{ offerId: string }>();
  const id = offerId ? decodeURIComponent(offerId) : "";

  if (!id) {
    return (
      <main>
        <p className="muted">Missing offer id.</p>
      </main>
    );
  }

  return (
    <main>
      <OfferDetail offerId={id} />
    </main>
  );
}
