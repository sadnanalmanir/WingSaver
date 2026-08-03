import type { SearchRequest } from "@/lib/types";

export const queryKeys = {
  search: (body: SearchRequest) => ["search", body] as const,
  offer: (id: string) => ["offer", id] as const,
};
