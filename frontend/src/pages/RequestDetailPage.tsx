import { useParams } from 'react-router-dom';
import RequestDetail from '../components/RequestDetail';
import ResubmitForm from '../components/ResubmitForm';
import { useAuth } from '../context/AuthContext';

export default function RequestDetailPage() {
  const { requestId } = useParams();
  const id = Number(requestId);
  const { user } = useAuth();

  if (!requestId || Number.isNaN(id)) {
    return (
      <p className="form-error" role="alert">
        Invalid request id.
      </p>
    );
  }

  return (
    <RequestDetail requestId={id}>
      {({ request, refetch }) =>
        request.status === 'more_info_needed' && user?.id === request.requester_id ? (
          <ResubmitForm request={request} onResubmitted={refetch} />
        ) : null
      }
    </RequestDetail>
  );
}
