const DEFAULT =
  "Prices are estimates and may change before booking. Fares are display-only and not a price lock.";

export function PriceDisclaimer({ text }: { text?: string | null }) {
  return (
    <p className="disclaimer" role="note">
      {text?.trim() || DEFAULT}
    </p>
  );
}
