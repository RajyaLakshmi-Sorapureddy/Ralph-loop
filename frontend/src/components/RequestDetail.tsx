import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../api/client';
import StatusBadge from './StatusBadge';
import type { RequestDetail as RequestDetailData, RequestDocument } from '../types';

interface RequestDetailProps {
  requestId: number;
  children?: (context: { request: RequestDetailData; refetch: () => void }) => ReactNode;
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString();
}

function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString();
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  const kb = bytes / 1024;
  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`;
  }
  return `${(kb / 1024).toFixed(1)} MB`;
}

export default function RequestDetail({ requestId, children }: RequestDetailProps) {
  const { token, user } = useAuth();
  const [request, setRequest] = useState<RequestDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await api.get<RequestDetailData>(`/requests/${requestId}`, token);
      setRequest(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load this request.');
    }
  }, [requestId, token]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleDownload(document: RequestDocument) {
    setDownloadError(null);
    try {
      const blob = await api.getBlob(`/requests/${requestId}/documents/${document.id}`, token);
      const url = URL.createObjectURL(blob);
      const link = window.document.createElement('a');
      link.href = url;
      link.download = document.file_name;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setDownloadError(err instanceof ApiError ? err.message : 'Unable to download this document.');
    }
  }

  if (error) {
    return (
      <p className="form-error" role="alert">
        {error}
      </p>
    );
  }

  if (!request) {
    return <p>Loading request...</p>;
  }

  return (
    <div className="request-detail">
      <div className="page-header">
        <h1>Request #{request.id}</h1>
        <StatusBadge status={request.status} />
      </div>

      <dl className="request-detail-fields">
        <div>
          <dt>Amount</dt>
          <dd>
            {request.currency} {request.amount}
          </dd>
        </div>
        <div>
          <dt>Category</dt>
          <dd>{request.category}</dd>
        </div>
        <div>
          <dt>Expense date</dt>
          <dd>{formatDate(request.expense_date)}</dd>
        </div>
        <div>
          <dt>Submitted</dt>
          <dd>{formatDateTime(request.created_at)}</dd>
        </div>
        <div className="request-detail-description">
          <dt>Description</dt>
          <dd>{request.description}</dd>
        </div>
      </dl>

      <section>
        <h2>Documents</h2>
        {downloadError && (
          <p className="form-error" role="alert">
            {downloadError}
          </p>
        )}
        {request.documents.length === 0 ? (
          <p>No documents attached.</p>
        ) : (
          <ul className="document-list">
            {request.documents.map((document) => (
              <li key={document.id}>
                <button type="button" className="link-button" onClick={() => void handleDownload(document)}>
                  {document.file_name}
                </button>{' '}
                <span className="document-meta">({formatFileSize(document.file_size)})</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Status history</h2>
        <table className="request-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Reason</th>
              <th>Changed by</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {request.status_history.map((entry) => (
              <tr key={entry.id}>
                <td>
                  <StatusBadge status={entry.status} />
                </td>
                <td>{entry.reason ?? '—'}</td>
                <td>{user?.id === entry.changed_by_user_id ? 'You' : `User #${entry.changed_by_user_id}`}</td>
                <td>{formatDateTime(entry.changed_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {children?.({ request, refetch: () => void load() })}
    </div>
  );
}
