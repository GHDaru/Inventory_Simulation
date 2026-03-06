import { useRef, useState } from 'react';
import { uploadFile } from '../api/client';

export default function FileUpload({ onUpload }) {
  const inputRef = useRef(null);
  const [column, setColumn] = useState('demand');
  const [status, setStatus] = useState(null); // null | 'loading' | 'success' | 'error'
  const [message, setMessage] = useState('');

  async function handleFile(file) {
    if (!file) return;
    setStatus('loading');
    setMessage('');
    try {
      const result = await uploadFile(file, column);
      setStatus('success');
      setMessage(
        `Loaded ${result.rows} records from "${result.column}" — ` +
        `mean: ${result.mean.toFixed(2)}, std: ${result.std_dev.toFixed(2)}`
      );
      onUpload(result);
    } catch (err) {
      setStatus('error');
      const detail = err.response?.data?.detail || err.message;
      setMessage(`Error: ${detail}`);
    }
  }

  function onInputChange(e) {
    handleFile(e.target.files?.[0]);
  }

  function onDrop(e) {
    e.preventDefault();
    handleFile(e.dataTransfer.files?.[0]);
  }

  function onDragOver(e) {
    e.preventDefault();
  }

  return (
    <div className="file-upload">
      <h3>Upload historical demand data (optional)</h3>
      <p className="hint">
        Upload a CSV or Excel file. The simulator will fit the best distribution
        to the data automatically.
      </p>
      <div className="form-row">
        <label>Demand column name</label>
        <input value={column} onChange={e => setColumn(e.target.value)} placeholder="demand" />
      </div>
      <div
        className={`drop-zone ${status === 'loading' ? 'loading' : ''}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          style={{ display: 'none' }}
          onChange={onInputChange}
        />
        {status === 'loading'
          ? 'Uploading…'
          : 'Drag & drop a CSV / Excel file here, or click to select'}
      </div>
      {message && (
        <p className={`upload-message ${status}`}>{message}</p>
      )}
    </div>
  );
}
