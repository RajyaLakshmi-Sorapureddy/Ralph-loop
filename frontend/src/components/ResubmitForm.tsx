import { useState, type ChangeEvent, type FormEvent } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../api/client';
import type { RequestDetail } from '../types';

const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];
const MAX_FILE_SIZE_MB = 10;
const MAX_FILES = 5;

function getExtension(fileName: string): string {
  const index = fileName.lastIndexOf('.');
  return index === -1 ? '' : fileName.slice(index).toLowerCase();
}

interface ResubmitFormProps {
  request: RequestDetail;
  onResubmitted: () => void;
}

export default function ResubmitForm({ request, onResubmitted }: ResubmitFormProps) {
  const { token } = useAuth();
  const [description, setDescription] = useState(request.description);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleFilesChange(event: ChangeEvent<HTMLInputElement>) {
    setFiles(Array.from(event.target.files ?? []));
  }

  function validate(): string | null {
    if (!description.trim()) {
      return 'Description cannot be empty.';
    }
    if (request.documents.length + files.length > MAX_FILES) {
      return `A request may have at most ${MAX_FILES} documents in total.`;
    }
    for (const file of files) {
      if (!ALLOWED_EXTENSIONS.includes(getExtension(file.name))) {
        return `Unsupported file type for "${file.name}". Allowed types: PDF, JPG, PNG.`;
      }
      if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
        return `File "${file.name}" exceeds the maximum size of ${MAX_FILE_SIZE_MB}MB.`;
      }
    }
    return null;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('description', description.trim());
      files.forEach((file) => formData.append('files', file));
      await api.postForm(`/requests/${request.id}/resubmit`, formData, token);
      setFiles([]);
      onResubmitted();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to resubmit this request. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="resubmit-form">
      <h2>Resubmit request</h2>
      <p>Finance requested more information. Update the details below and resubmit for review.</p>
      <form className="request-form" onSubmit={handleSubmit}>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        <div className="form-row">
          <label htmlFor="resubmit-description">Description</label>
          <textarea
            id="resubmit-description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            required
            rows={4}
          />
        </div>

        <div className="form-row">
          <label htmlFor="resubmit-documents">
            Add supporting documents (PDF, JPG, PNG — up to {MAX_FILE_SIZE_MB}MB each, max {MAX_FILES} total)
          </label>
          <input
            id="resubmit-documents"
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleFilesChange}
          />
          {files.length > 0 && (
            <ul className="file-list">
              {files.map((file) => (
                <li key={file.name}>{file.name}</li>
              ))}
            </ul>
          )}
        </div>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Resubmitting...' : 'Resubmit request'}
        </button>
      </form>
    </section>
  );
}
