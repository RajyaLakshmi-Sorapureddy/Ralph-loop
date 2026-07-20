import { useParams } from 'react-router-dom';

export default function RequestDetailPage() {
  const { requestId } = useParams();

  return (
    <div>
      <h1>Request #{requestId}</h1>
      <p>Full request details will appear here.</p>
    </div>
  );
}
