import type { Metadata } from "next";

import { OfferDetail } from "@/components/offer-detail";

type Props = {
  params: Promise<{ offerId: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { offerId } = await params;
  return {
    title: `Flight ${offerId.slice(0, 18)}…`,
  };
}

export default async function FlightDetailPage({ params }: Props) {
  const { offerId } = await params;
  return (
    <main>
      <OfferDetail offerId={decodeURIComponent(offerId)} />
    </main>
  );
}
