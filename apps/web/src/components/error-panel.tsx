import { ApiError } from "@/lib/types";

export function ErrorPanel({ error, title = "Something went wrong" }: { error: unknown; title?: string }) {
  const api = error instanceof ApiError ? error : null;
  const message =
    api?.message ?? (error instanceof Error ? error.message : "Unexpected error");

  return (
    <div className="panel error-panel" role="alert">
      <h2 className="panel-title">{title}</h2>
      <p>{message}</p>
      {api ? (
        <dl className="error-meta">
          <div>
            <dt>Code</dt>
            <dd>
              <code>{api.code}</code>
            </dd>
          </div>
          {api.requestId ? (
            <div>
              <dt>Request ID</dt>
              <dd>
                <code>{api.requestId}</code>
              </dd>
            </div>
          ) : null}
          <div>
            <dt>HTTP</dt>
            <dd>
              <code>{api.status}</code>
            </dd>
          </div>
        </dl>
      ) : null}
    </div>
  );
}
