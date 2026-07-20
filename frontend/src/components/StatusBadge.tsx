import type { RequestStatus } from '../types';

const STATUS_LABELS: Record<RequestStatus, string> = {
  pending: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  more_info_needed: 'More Info Needed',
};

export default function StatusBadge({ status }: { status: RequestStatus }) {
  return <span className={`status-badge status-badge--${status}`}>{STATUS_LABELS[status]}</span>;
}
