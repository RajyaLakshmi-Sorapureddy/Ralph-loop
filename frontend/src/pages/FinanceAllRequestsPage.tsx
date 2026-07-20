import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import type { RequestStatus, RequestWithRequester } from '../types';

const DESCRIPTION_TRUNCATE_LENGTH = 80;
const ALL_FILTER = 'all';

const STATUS_OPTIONS: { value: RequestStatus; label: string }[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'more_info_needed', label: 'More Info Needed' },
];

function truncate(text: string, maxLength: number): string {
  return text.length > maxLength ? `${text.slice(0, maxLength).trimEnd()}...` : text;
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString();
}

export default function FinanceAllRequestsPage() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [requesterOptions, setRequesterOptions] = useState<{ id: number; name: string }[]>([]);
  const [categoryOptions, setCategoryOptions] = useState<string[]>([]);
  const [requests, setRequests] = useState<RequestWithRequester[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [requesterFilter, setRequesterFilter] = useState(ALL_FILTER);
  const [statusFilter, setStatusFilter] = useState(ALL_FILTER);
  const [categoryFilter, setCategoryFilter] = useState(ALL_FILTER);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Fetch the full, unfiltered set once to populate the requester/category dropdown options,
  // independent of whatever filters later narrow the displayed list.
  useEffect(() => {
    let cancelled = false;
    api
      .get<RequestWithRequester[]>('/requests', token)
      .then((data) => {
        if (cancelled) return;
        const requesters = new Map<number, string>();
        const categories = new Set<string>();
        for (const item of data) {
          requesters.set(item.requester_id, item.requester_name);
          categories.add(item.category);
        }
        setRequesterOptions(
          Array.from(requesters, ([id, name]) => ({ id, name })).sort((a, b) =>
            a.name.localeCompare(b.name),
          ),
        );
        setCategoryOptions(Array.from(categories).sort());
      })
      .catch(() => {
        // Filter options are a convenience; a failed fetch here just leaves the dropdowns empty.
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (requesterFilter !== ALL_FILTER) params.set('requester_id', requesterFilter);
    if (statusFilter !== ALL_FILTER) params.set('status', statusFilter);
    if (categoryFilter !== ALL_FILTER) params.set('category', categoryFilter);
    if (dateFrom) params.set('date_from', dateFrom);
    if (dateTo) params.set('date_to', dateTo);
    const qs = params.toString();
    return qs ? `?${qs}` : '';
  }, [requesterFilter, statusFilter, categoryFilter, dateFrom, dateTo]);

  useEffect(() => {
    let cancelled = false;
    setError(null);

    async function load() {
      try {
        const data = await api.get<RequestWithRequester[]>(`/requests${queryString}`, token);
        if (!cancelled) {
          setRequests(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Unable to load requests.');
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [queryString, token]);

  return (
    <div>
      <div className="page-header">
        <h1>All Requests</h1>
        <Link to="/finance/pending" className="button-link">
          Pending Requests
        </Link>
      </div>
      <div className="filter-bar">
        <label>
          Requester
          <select value={requesterFilter} onChange={(e) => setRequesterFilter(e.target.value)}>
            <option value={ALL_FILTER}>All requesters</option>
            {requesterOptions.map((requester) => (
              <option key={requester.id} value={requester.id}>
                {requester.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value={ALL_FILTER}>All statuses</option>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Category
          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            <option value={ALL_FILTER}>All categories</option>
            {categoryOptions.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>
        <label>
          From
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </label>
        <label>
          To
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </label>
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {requests === null && !error && <p>Loading requests...</p>}
      {requests !== null && requests.length === 0 && <p>No requests match the selected filters.</p>}
      {requests !== null && requests.length > 0 && (
        <table className="request-table">
          <thead>
            <tr>
              <th>Date submitted</th>
              <th>Requester</th>
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
                  {request.requester_name}
                  <div className="document-meta">{request.requester_email}</div>
                </td>
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
