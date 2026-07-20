import { useParams } from 'react-router-dom';
import RequestDetail from '../components/RequestDetail';

export default function RequestDetailPage() {
  const { requestId } = useParams();
  const id = Number(requestId);

  if (!requestId || Number.isNaN(id)) {
    return (
      <p className="form-error" role="alert">
        Invalid request id.
      </p>
    );
  }

  return <RequestDetail requestId={id} />;
}
