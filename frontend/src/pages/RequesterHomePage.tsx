import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import type { ReimbursementRequest } from '../types';

const DESCRIPTION_TRUNCATE_LENGTH = 80;

function truncate(text: string, maxLength: number): string {
  return text.length > maxLength ? `${text.slice(0, maxLength).trimEnd()}...` : text;
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString();
}

export default function RequesterHomePage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const requestSubmitted = (location.state as { requestSubmitted?: { id: number; status: string } } | null)
    ?.requestSubmitted;

  const [requests, setRequests] = useState<ReimbursementRequest[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await api.get<ReimbursementRequest[]>('/requests/mine', token);
        if (!cancelled) {
          setRequests(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Unable to load your requests.');
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div>
      <div className="page-header">
        <h1>My Requests</h1>
        <Link to="/requests/new" className="button-link">
          New Request
        </Link>
      </div>
      {requestSubmitted && (
        <p className="form-success" role="status">
          Request #{requestSubmitted.id} submitted successfully (status: {requestSubmitted.status}).
        </p>
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {requests === null && !error && <p>Loading your requests...</p>}
      {requests !== null && requests.length === 0 && <p>You haven&apos;t submitted any requests yet.</p>}
      {requests !== null && requests.length > 0 && (
        <table className="request-table">
          <thead>
            <tr>
              <th>Date submitted</th>
              <th>Amount</th>
              <th>Category</th>
              <th>Description</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((request) => (
              <tr
                key={request.id}
                className="request-table-row"
                onClick={() => navigate(`/requests/${request.id}`)}
              >
                <td>{formatDate(request.created_at)}</td>
                <td>
                  {request.currency} {request.amount}
                </td>
                <td>{request.category}</td>
                <td>{truncate(request.description, DESCRIPTION_TRUNCATE_LENGTH)}</td>
                <td>
                  <StatusBadge status={request.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
