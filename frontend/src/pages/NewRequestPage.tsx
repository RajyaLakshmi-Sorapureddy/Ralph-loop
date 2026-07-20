import { useState, type ChangeEvent, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../api/client';
import type { ReimbursementRequest } from '../types';

const CATEGORIES = ['Travel', 'Meals', 'Lodging', 'Office Supplies', 'Software', 'Other'];
const CURRENCIES = ['USD', 'EUR', 'GBP', 'INR'];
const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];
const MAX_FILE_SIZE_MB = 10;
const MAX_FILES = 5;

function getExtension(fileName: string): string {
  const index = fileName.lastIndexOf('.');
  return index === -1 ? '' : fileName.slice(index).toLowerCase();
}

export default function NewRequestPage() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState(CURRENCIES[0]);
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [expenseDate, setExpenseDate] = useState('');
  const [description, setDescription] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleFilesChange(event: ChangeEvent<HTMLInputElement>) {
    setFiles(Array.from(event.target.files ?? []));
  }

  function validate(): string | null {
    if (!amount || !currency || !category || !expenseDate || !description.trim()) {
      return 'Please fill in all required fields.';
    }
    const amountValue = Number(amount);
    if (!Number.isFinite(amountValue) || amountValue <= 0) {
      return 'Amount must be greater than 0.';
    }
    if (files.length > MAX_FILES) {
      return `A request may have at most ${MAX_FILES} documents.`;
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
      const created = await api.post<ReimbursementRequest>(
        '/requests',
        {
          amount: Number(amount),
          currency,
          category,
          expense_date: expenseDate,
          description: description.trim(),
        },
        token,
      );

      if (files.length > 0) {
        const formData = new FormData();
        files.forEach((file) => formData.append('files', file));
        await api.postForm(`/requests/${created.id}/documents`, formData, token);
      }

      navigate('/my-requests', {
        replace: true,
        state: { requestSubmitted: { id: created.id, status: created.status } },
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to submit request. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="form-page">
      <h1>New Request</h1>
      <form className="request-form" onSubmit={handleSubmit}>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        <div className="form-row">
          <label htmlFor="amount">Amount</label>
          <input
            id="amount"
            type="number"
            min="0.01"
            step="0.01"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            required
          />
        </div>

        <div className="form-row">
          <label htmlFor="currency">Currency</label>
          <select id="currency" value={currency} onChange={(event) => setCurrency(event.target.value)}>
            {CURRENCIES.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <div className="form-row">
          <label htmlFor="category">Category</label>
          <select id="category" value={category} onChange={(event) => setCategory(event.target.value)}>
            {CATEGORIES.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <div className="form-row">
          <label htmlFor="expense_date">Expense date</label>
          <input
            id="expense_date"
            type="date"
            value={expenseDate}
            onChange={(event) => setExpenseDate(event.target.value)}
            required
          />
        </div>

        <div className="form-row">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            required
            rows={4}
          />
        </div>

        <div className="form-row">
          <label htmlFor="documents">Supporting documents (PDF, JPG, PNG — up to {MAX_FILE_SIZE_MB}MB each, max{' '}
            {MAX_FILES})</label>
          <input id="documents" type="file" multiple accept=".pdf,.jpg,.jpeg,.png" onChange={handleFilesChange} />
          {files.length > 0 && (
            <ul className="file-list">
              {files.map((file) => (
                <li key={file.name}>{file.name}</li>
              ))}
            </ul>
          )}
        </div>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Submitting...' : 'Submit request'}
        </button>
      </form>
    </div>
  );
}
