/** Small static airport list for origin/destination pickers (MVP). */
export type Airport = {
  iata: string;
  city: string;
  name: string;
};

export const AIRPORTS: Airport[] = [
  { iata: "JFK", city: "New York", name: "John F. Kennedy International" },
  { iata: "EWR", city: "Newark", name: "Newark Liberty International" },
  { iata: "LGA", city: "New York", name: "LaGuardia" },
  { iata: "LHR", city: "London", name: "Heathrow" },
  { iata: "LGW", city: "London", name: "Gatwick" },
  { iata: "CDG", city: "Paris", name: "Charles de Gaulle" },
  { iata: "AMS", city: "Amsterdam", name: "Schiphol" },
  { iata: "FRA", city: "Frankfurt", name: "Frankfurt Airport" },
  { iata: "MAD", city: "Madrid", name: "Adolfo Suárez Madrid–Barajas" },
  { iata: "FCO", city: "Rome", name: "Leonardo da Vinci–Fiumicino" },
  { iata: "DXB", city: "Dubai", name: "Dubai International" },
  { iata: "DOH", city: "Doha", name: "Hamad International" },
  { iata: "SIN", city: "Singapore", name: "Changi" },
  { iata: "HND", city: "Tokyo", name: "Haneda" },
  { iata: "NRT", city: "Tokyo", name: "Narita" },
  { iata: "SFO", city: "San Francisco", name: "San Francisco International" },
  { iata: "LAX", city: "Los Angeles", name: "Los Angeles International" },
  { iata: "ORD", city: "Chicago", name: "O'Hare International" },
  { iata: "MIA", city: "Miami", name: "Miami International" },
  { iata: "BOS", city: "Boston", name: "Logan International" },
  { iata: "SEA", city: "Seattle", name: "Seattle–Tacoma International" },
  { iata: "YYZ", city: "Toronto", name: "Toronto Pearson" },
  { iata: "YVR", city: "Vancouver", name: "Vancouver International" },
  { iata: "SYD", city: "Sydney", name: "Kingsford Smith" },
  { iata: "MEL", city: "Melbourne", name: "Melbourne Airport" },
  { iata: "HKG", city: "Hong Kong", name: "Hong Kong International" },
  { iata: "ICN", city: "Seoul", name: "Incheon International" },
  { iata: "DEL", city: "Delhi", name: "Indira Gandhi International" },
  { iata: "BOM", city: "Mumbai", name: "Chhatrapati Shivaji Maharaj" },
  { iata: "GRU", city: "São Paulo", name: "Guarulhos" },
];

export function airportLabel(a: Airport): string {
  return `${a.iata} — ${a.city} (${a.name})`;
}
