import type { OfferPublic, SearchRequest, SearchResponse } from "@/lib/types";
import { ApiError, type ApiErrorBody } from "@/lib/types";

function apiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
  return base.replace(/\/$/, "");
}

export async function toApiError(res: Response): Promise<ApiError> {
  let code = "HTTP_ERROR";
  let message = res.statusText || "Request failed";
  let requestId: string | null | undefined = res.headers.get("X-Request-ID");
  let details: unknown;

  try {
    const body = (await res.json()) as ApiErrorBody;
    if (body?.error) {
      code = body.error.code ?? code;
      message = body.error.message ?? message;
      requestId = body.error.request_id ?? requestId;
      details = body.error.details;
    }
  } catch {
    // non-JSON body
  }

  return new ApiError({ status: res.status, code, message, requestId, details });
}

export async function searchFlights(
  body: SearchRequest,
  signal?: AbortSignal,
): Promise<SearchResponse> {
  const res = await fetch(`${apiBase()}/api/v1/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) throw await toApiError(res);
  return res.json() as Promise<SearchResponse>;
}

export async function getOffer(
  offerId: string,
  signal?: AbortSignal,
): Promise<OfferPublic> {
  const res = await fetch(`${apiBase()}/api/v1/offers/${encodeURIComponent(offerId)}`, {
    method: "GET",
    signal,
  });
  if (!res.ok) throw await toApiError(res);
  return res.json() as Promise<OfferPublic>;
}

export function getApiBaseUrl(): string {
  return apiBase();
}
