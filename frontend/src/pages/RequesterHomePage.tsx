import { Link, useLocation } from 'react-router-dom';

export default function RequesterHomePage() {
  const location = useLocation();
  const requestSubmitted = (location.state as { requestSubmitted?: { id: number; status: string } } | null)
    ?.requestSubmitted;

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
      <p>Your submitted reimbursement requests will appear here.</p>
    </div>
  );
}
