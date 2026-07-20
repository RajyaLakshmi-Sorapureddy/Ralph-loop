import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import type { RequestWithRequester } from '../types';

const DESCRIPTION_TRUNCATE_LENGTH = 80;

type SortKey = 'requester' | 'category' | 'date';
type SortDir = 'asc' | 'desc';

const ALL_FILTER = 'all';

function truncate(text: string, maxLength: number): string {
  return text.length > maxLength ? `${text.slice(0, maxLength).trimEnd()}...` : text;
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString();
}

function sortIndicator(active: boolean, dir: SortDir): string {
  if (!active) return '';
  return dir === 'asc' ? ' ▲' : ' ▼';
}

export default function FinanceHomePage() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [requests, setRequests] = useState<RequestWithRequester[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [requesterFilter, setRequesterFilter] = useState(ALL_FILTER);
  const [categoryFilter, setCategoryFilter] = useState(ALL_FILTER);
  const [sortKey, setSortKey] = useState<SortKey>('date');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await api.get<RequestWithRequester[]>('/requests/pending', token);
        if (!cancelled) {
          setRequests(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Unable to load pending requests.');
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [token]);

  const requesterOptions = useMemo(() => {
    if (!requests) return [];
    return Array.from(new Set(requests.map((r) => r.requester_name))).sort();
  }, [requests]);

  const categoryOptions = useMemo(() => {
    if (!requests) return [];
    return Array.from(new Set(requests.map((r) => r.category))).sort();
  }, [requests]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  }

  const visibleRequests = useMemo(() => {
    if (!requests) return [];
    const filtered = requests.filter(
      (r) =>
        (requesterFilter === ALL_FILTER || r.requester_name === requesterFilter) &&
        (categoryFilter === ALL_FILTER || r.category === categoryFilter),
    );
    const factor = sortDir === 'asc' ? 1 : -1;
    return [...filtered].sort((a, b) => {
      switch (sortKey) {
        case 'requester':
          return factor * a.requester_name.localeCompare(b.requester_name);
        case 'category':
          return factor * a.category.localeCompare(b.category);
        case 'date':
        default:
          return factor * (new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
      }
    });
  }, [requests, requesterFilter, categoryFilter, sortKey, sortDir]);

  return (
    <div>
      <div className="page-header">
        <h1>Pending Requests</h1>
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {requests === null && !error && <p>Loading pending requests...</p>}
      {requests !== null && requests.length === 0 && <p>There are no requests awaiting review.</p>}
      {requests !== null && requests.length > 0 && (
        <>
          <div className="filter-bar">
            <label>
              Requester
              <select value={requesterFilter} onChange={(e) => setRequesterFilter(e.target.value)}>
                <option value={ALL_FILTER}>All requesters</option>
                {requesterOptions.map((name) => (
                  <option key={name} value={name}>
                    {name}
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
          </div>
          <table className="request-table">
            <thead>
              <tr>
                <th>
                  <button type="button" className="sort-header" onClick={() => toggleSort('date')}>
                    Date submitted{sortIndicator(sortKey === 'date', sortDir)}
                  </button>
                </th>
                <th>
                  <button type="button" className="sort-header" onClick={() => toggleSort('requester')}>
                    Requester{sortIndicator(sortKey === 'requester', sortDir)}
                  </button>
                </th>
                <th>Amount</th>
                <th>
                  <button type="button" className="sort-header" onClick={() => toggleSort('category')}>
                    Category{sortIndicator(sortKey === 'category', sortDir)}
                  </button>
                </th>
                <th>Description</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {visibleRequests.map((request) => (
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
        </>
      )}
    </div>
  );
}
