import type { components } from "@wingsaver/openapi/schema";

export type SearchRequest = components["schemas"]["SearchRequest"];
export type SearchResponse = components["schemas"]["SearchResponse"];
export type SearchFilters = components["schemas"]["SearchFilters"];
export type OfferPublic = components["schemas"]["OfferPublic"];
export type Passengers = components["schemas"]["Passengers"];
export type Money = components["schemas"]["Money"];
export type Slice = components["schemas"]["Slice"];
export type Segment = components["schemas"]["Segment"];

export type CabinClass = SearchRequest["cabin_class"];
export type TripType = SearchRequest["trip_type"];
export type SearchSort = SearchRequest["sort"];

export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    request_id?: string | null;
    details?: unknown;
  };
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId?: string | null;
  readonly details?: unknown;

  constructor(opts: {
    status: number;
    code: string;
    message: string;
    requestId?: string | null;
    details?: unknown;
  }) {
    super(opts.message);
    this.name = "ApiError";
    this.status = opts.status;
    this.code = opts.code;
    this.requestId = opts.requestId;
    this.details = opts.details;
  }
}
