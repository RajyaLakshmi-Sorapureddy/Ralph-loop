import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../api/client';
import type { RequestDetail, ReviewActionType } from '../types';

interface ReviewActionsProps {
  request: RequestDetail;
  onReviewed: () => void;
}

const SUBMITTING_LABELS: Record<ReviewActionType, string> = {
  approve: 'Approving...',
  reject: 'Rejecting...',
  more_info: 'Submitting...',
};

export default function ReviewActions({ request, onReviewed }: ReviewActionsProps) {
  const { token } = useAuth();
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submittingAction, setSubmittingAction] = useState<ReviewActionType | null>(null);

  async function handleAction(action: ReviewActionType) {
    setError(null);

    if ((action === 'reject' || action === 'more_info') && !reason.trim()) {
      setError('A reason is required to reject or request more info.');
      return;
    }

    setSubmittingAction(action);
    try {
      await api.post(`/requests/${request.id}/review`, { action, reason: reason.trim() || null }, token);
      setReason('');
      onReviewed();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to submit this review. Please try again.');
    } finally {
      setSubmittingAction(null);
    }
  }

  return (
    <section className="review-actions">
      <h2>Review this request</h2>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      <div className="form-row">
        <label htmlFor="review-reason">Reason / comment</label>
        <textarea
          id="review-reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          rows={3}
          placeholder="Required to reject or request more info; optional to approve"
        />
      </div>

      <div className="review-actions-buttons">
        <button
          type="button"
          className="review-action-btn review-action-approve"
          disabled={submittingAction !== null}
          onClick={() => void handleAction('approve')}
        >
          {submittingAction === 'approve' ? SUBMITTING_LABELS.approve : 'Approve'}
        </button>
        <button
          type="button"
          className="review-action-btn review-action-reject"
          disabled={submittingAction !== null}
          onClick={() => void handleAction('reject')}
        >
          {submittingAction === 'reject' ? SUBMITTING_LABELS.reject : 'Reject'}
        </button>
        <button
          type="button"
          className="review-action-btn review-action-more-info"
          disabled={submittingAction !== null}
          onClick={() => void handleAction('more_info')}
        >
          {submittingAction === 'more_info' ? SUBMITTING_LABELS.more_info : 'Request More Info'}
        </button>
      </div>
    </section>
  );
}
