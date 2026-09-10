import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, Bell, CheckCircle2, Download, FileUp, RefreshCw, Search, Trash2, UploadCloud, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './livePrediction.css';

const API = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:5000/api`;
const stages = [
  'Validating uploaded data',
  'Preparing historical sequence',
  'Loading iTransformer model',
  'Generating next-month forecast',
  'Calculating continuous WQI & CPCB status',
  'Analyzing hotspot risk & severity',
  'Evaluating critical & warning alerts',
  'Saving results to database',
  'Prediction completed'
];

async function request(path, options) { const response = await fetch(`${API}${path}`, options); const body = await response.json().catch(() => ({})); if (!response.ok) throw new Error(body.error || 'The request could not be completed.'); return body; }
const number = (value, digits = 2) => value === null || value === undefined ? '—' : Number(value).toFixed(digits);
const csvEscape = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;

function StatusBadge({ children, kind = '' }) { return <span className={`live-status ${kind || String(children).toLowerCase().replaceAll(' ', '-')}`}>{children}</span>; }

export function LivePrediction() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const [stage, setStage] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [filters, setFilters] = useState({ search: '', state: '', wqi: '', hotspot: '', cpcb: '', sort: 'wqi' });

  const loadHistory = () => request('/live-predictions').then(setHistory).catch(() => setHistory([]));
  useEffect(() => { loadHistory(); }, []);

  const chooseFile = (candidate) => {
    setError('');
    setResult(null);
    if (!candidate) return;
    if (!candidate.name.toLowerCase().endsWith('.csv')) {
      setError('Only CSV files are accepted.');
      return;
    }
    if (candidate.size === 0) {
      setError('The selected CSV is empty.');
      return;
    }
    setFile(candidate);
  };

  const onDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files?.[0]);
  };

  const predict = async () => {
    if (!file || processing) return;
    setError('');
    setProcessing(true);
    setStage(0);
    const form = new FormData();
    form.append('file', file);
    const interval = window.setInterval(() => setStage((current) => Math.min(current + 1, stages.length - 1)), 900);
    try {
      const body = await request('/live-prediction', { method: 'POST', body: form });
      setResult(body);
      setStage(stages.length - 1);
      setFile(null);
      await loadHistory();
      window.dispatchEvent(new Event('notifications-updated'));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      window.clearInterval(interval);
      setProcessing(false);
    }
  };

  const loadUpload = async (uploadId) => {
    try {
      const data = await request(`/live-predictions/${uploadId}`);
      if (data && (data.predictions || Array.isArray(data))) {
        const payload = data.predictions ? data : {
          upload_id: uploadId,
          input_month: data[0]?.input_month || 'Upload',
          input_year: data[0]?.input_year || '',
          forecast_month: data[0]?.Forecast_Month || '',
          forecast_year: data[0]?.Forecast_Year || '',
          stations_processed: new Set(data.map(d => d['Station Code'])).size,
          predictions: data,
          high_hotspots: data.filter(d => d.Severity === 'High Risk' || d.Hotspot_Level === 'High Hotspot').length,
          warnings: data.filter(d => d.Severity === 'Warning').length,
        };
        setResult(payload);
        window.scrollTo({ top: 350, behavior: 'smooth' });
      }
    } catch (err) {
      console.error('Failed to load live prediction:', err);
    }
  };

  const filtered = useMemo(() => {
    if (!result?.predictions) return [];
    const rows = result.predictions
      .filter((row) => `${row['Station Name']} ${row['Station Code']} ${row.State}`.toLowerCase().includes(filters.search.toLowerCase()))
      .filter((row) => !filters.state || row.State === filters.state)
      .filter((row) => !filters.hotspot || row.Hotspot_Level === filters.hotspot)
      .filter((row) => !filters.cpcb || (filters.cpcb === 'Compliant' ? [row.CPCB_DO_Status, row.CPCB_pH_Status, row.CPCB_BOD_Status].every((status) => status === 'Compliant') : [row.CPCB_DO_Status, row.CPCB_pH_Status, row.CPCB_BOD_Status].some((status) => status === 'Violation')))
      .filter((row) => !filters.wqi || (filters.wqi === 'High' ? row.Predicted_WQI >= 90 : filters.wqi === 'Medium' ? row.Predicted_WQI >= 70 && row.Predicted_WQI < 90 : row.Predicted_WQI < 70));
    return rows.sort((a, b) => filters.sort === 'do' ? b.Predicted_DO - a.Predicted_DO : filters.sort === 'bod' ? b.Predicted_BOD - a.Predicted_BOD : a.Predicted_WQI - b.Predicted_WQI);
  }, [result, filters]);

  const download = () => {
    if (!result) return;
    const columns = ['Forecast_Year', 'Forecast_Month', 'State', 'Station Code', 'Station Name', 'Predicted_DO', 'Predicted_pH', 'Predicted_BOD', 'Predicted_WQI', 'WQI_Class', 'Hotspot_Level', 'Severity', 'CPCB_DO_Status', 'CPCB_pH_Status', 'CPCB_BOD_Status'];
    const csv = [columns, ...result.predictions.map((row) => columns.map((key) => csvEscape(row[key])))].map((row) => row.join(',')).join('\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `live_prediction_${result.forecast_year}_${result.forecast_month}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const states = [...new Set(result?.predictions?.map((row) => row.State) || [])];

  return <>
    <div className="page-heading">
      <div>
        <div className="eyebrow">Live model inference / 11</div>
        <h1>Live Water Quality Prediction</h1>
        <p>Upload a monthly reading CSV to predict the next month's water quality across stations.</p>
      </div>
      {result && <button className="button primary" onClick={download}><Download size={16} /> Download Prediction CSV</button>}
    </div>
    <section className="live-upload-grid">
      <div className="panel live-upload-panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">iTransformer Inference Pipeline</div>
            <h2>Upload monthly observations</h2>
          </div>
          <StatusBadge kind="forecast">CSV only</StatusBadge>
        </div>
        <div className={`drop-zone ${dragging ? 'dragging' : ''}`} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop}>
          <UploadCloud size={30} />
          <strong>Drop your monthly CSV here</strong>
          <span>Required fields: Year, Month_No, Month, Round, State, Station Code, Station Name, DO, pH, BOD</span>
          <button className="button ghost" onClick={() => inputRef.current?.click()}><FileUp size={15} /> Browse / Choose File</button>
          <input ref={inputRef} type="file" accept=".csv,text/csv" hidden onChange={(event) => chooseFile(event.target.files?.[0])} />
        </div>
        {file && (
          <div className="selected-file">
            <FileUp size={17} />
            <div>
              <strong>{file.name}</strong>
              <span>{(file.size / 1024).toFixed(1)} KB · Ready for next-month forecast</span>
            </div>
            <button title="Remove file" onClick={() => setFile(null)}><Trash2 size={16} /></button>
          </div>
        )}
        {error && <div className="live-error"><AlertTriangle size={17} />{error}</div>}
        <button className="button primary predict-button" disabled={!file || processing} onClick={predict}>
          {processing ? <><RefreshCw size={16} className="spin" />{stages[stage]}...</> : <>Predict next month <span>→</span></>}
        </button>
        <p className="live-note">
          Upload any single-month observation. The system builds the 12-month historical sequence, forecasts the next month's values, records critical or warning alerts in notifications, and saves the output.
        </p>
      </div>
      <div className="panel live-method-panel">
        <div className="eyebrow">Automatic workflow</div>
        <h2>One month forward.</h2>
        <div className="live-flow">
          <div><span>01</span><strong>Latest Input</strong><small>CSV month detected</small></div>
          <div><span>02</span><strong>12-Mo. Lookback</strong><small>11 MySQL months + upload</small></div>
          <div><span>03</span><strong>Next Month Forecast</strong><small>DO · pH · BOD · WQI</small></div>
        </div>
        <div className="live-boundary">
          <CheckCircle2 size={18} />
          <span>
            <strong>Predictive Alert Intelligence</strong>
            If next month's predicted output is critical (High Hotspot, WQI &lt; 70) or warning (CPCB criteria exceedance), it automatically triggers an alert in notifications. Normal results are saved cleanly.
          </span>
        </div>
      </div>
    </section>
    {processing && (
      <div className="live-progress panel">
        <div className="progress-heading">
          <div>
            <div className="eyebrow">Inference in progress</div>
            <strong>{stages[stage]}</strong>
          </div>
          <span>{stage + 1} / {stages.length}</span>
        </div>
        <div className="progress-track"><span style={{ width: `${((stage + 1) / stages.length) * 100}%` }} /></div>
      </div>
    )}
    {result && <LiveResults result={result} filtered={filtered} states={states} filters={filters} setFilters={setFilters} download={download} />}
    <PreviousPredictions history={history} onSelectUpload={loadUpload} selectedId={result?.upload_id} />
  </>;
}

function LiveResults({ result, filtered, states, filters, setFilters, download }) {
  return (
    <section className="live-results">
      <div className="live-result-header">
        <div>
          <div className="eyebrow">Prediction completed · Next Month Forecast</div>
          <h2>{result.input_month} {result.input_year} → {result.forecast_month} {result.forecast_year}</h2>
          <p>Generated from the trained iTransformer model for the following month. All values below are predicted forecasts.</p>
        </div>
        <div className="result-actions">
          <StatusBadge kind="success">Saved to Database</StatusBadge>
          <button className="button ghost" onClick={download}><Download size={15} /> CSV</button>
        </div>
      </div>
      <div className="stats-grid live-stats">
        <div className="stat-card teal">
          <span>Input Observation</span>
          <strong>{result.input_month}<small> {result.input_year}</small></strong>
          <span className="stat-detail">Latest uploaded data</span>
        </div>
        <div className="stat-card blue">
          <span>Forecast Month</span>
          <strong>{result.forecast_month}<small> {result.forecast_year}</small></strong>
          <span className="stat-detail">Next month projection</span>
        </div>
        <div className="stat-card ink">
          <span>Stations Processed</span>
          <strong>{result.stations_processed}</strong>
          <span className="stat-detail">Validated station records</span>
        </div>
        <div className="stat-card orange">
          <span>Alerts & Hotspots</span>
          <strong>{result.high_hotspots} alerts</strong>
          <span className="stat-detail">Notified to system</span>
        </div>
      </div>
      <div className="panel live-table-panel">
        <div className="live-toolbar">
          <div>
            <div className="eyebrow">Station Predictions</div>
            <h2>Predicted water quality for {result.forecast_month} {result.forecast_year}</h2>
          </div>
          <div className="live-filters">
            <div className="search-box small">
              <Search size={15} />
              <input value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} placeholder="Search stations" />
            </div>
            <select value={filters.state} onChange={(event) => setFilters({ ...filters, state: event.target.value })}>
              <option value="">All states</option>
              {states.map((state) => <option key={state} value={state}>{state}</option>)}
            </select>
            <select value={filters.wqi} onChange={(event) => setFilters({ ...filters, wqi: event.target.value })}>
              <option value="">All WQI</option>
              <option value="High">Excellent (≥90)</option>
              <option value="Medium">Good (70–89)</option>
              <option value="Low">Below Good (&lt;70)</option>
            </select>
            <select value={filters.hotspot} onChange={(event) => setFilters({ ...filters, hotspot: event.target.value })}>
              <option value="">All hotspots</option>
              <option>High Hotspot</option>
              <option>Moderate Hotspot</option>
              <option>Low / No Hotspot</option>
            </select>
            <select value={filters.cpcb} onChange={(event) => setFilters({ ...filters, cpcb: event.target.value })}>
              <option value="">All CPCB status</option>
              <option>Compliant</option>
              <option>Violation</option>
            </select>
            <select value={filters.sort} onChange={(event) => setFilters({ ...filters, sort: event.target.value })}>
              <option value="wqi">Sort WQI</option>
              <option value="do">Sort DO</option>
              <option value="bod">Sort BOD</option>
            </select>
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {[
                  ['Forecast_Month', 'Forecast Month'],
                  ['Station Code', 'Code'],
                  ['Station Name', 'Station'],
                  ['State', 'State'],
                  ['Predicted_DO', 'Pred. DO'],
                  ['Predicted_pH', 'Pred. pH'],
                  ['Predicted_BOD', 'Pred. BOD'],
                  ['Predicted_WQI', 'Pred. WQI'],
                  ['WQI_Class', 'WQI class'],
                  ['Hotspot_Level', 'Alert / Severity'],
                  ['CPCB_DO_Status', 'CPCB status']
                ].map(([key, label]) => <th key={key}>{label}</th>)}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr key={`${row['Station Code']}_${row.Forecast_Year}_${row.Forecast_Month_No || row.Forecast_Month}`}>
                  <td><span className="live-forecast-pill"><strong>{row.Forecast_Month}</strong> {row.Forecast_Year}</span></td>
                  <td>{row['Station Code']}</td>
                  <td>{row['Station Name']}</td>
                  <td>{row.State}</td>
                  <td>{number(row.Predicted_DO)}</td>
                  <td>{number(row.Predicted_pH)}</td>
                  <td>{number(row.Predicted_BOD)}</td>
                  <td><strong>{number(row.Predicted_WQI)}</strong></td>
                  <td>{row.WQI_Class}</td>
                  <td>
                    <StatusBadge kind={row.Severity === 'High Risk' ? 'high-hotspot' : row.Severity === 'Warning' ? 'moderate-hotspot' : 'compliant'}>
                      {row.Severity || row.Hotspot_Level}
                    </StatusBadge>
                  </td>
                  <td>
                    <StatusBadge kind={row.CPCB_Violation_Percent ? 'violation' : 'compliant'}>
                      {row.CPCB_Violation_Percent ? 'Violation' : 'Compliant'}
                    </StatusBadge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="table-foot">
          <span>{filtered.length} of {result.predictions.length} stations shown</span>
          <span>Next-month iTransformer forecast · CPCB reference check · Hotspot alert trigger</span>
        </div>
      </div>
      <div className="callout live-callout">
        <Bell size={19} />
        <div>
          <strong>Automatic alerting active</strong>
          <span>Critical and Warning alerts are automatically registered in the Notifications center (Navbar bell and Notifications tab). Normal forecasts are stored cleanly without cluttering alerts.</span>
        </div>
      </div>
    </section>
  );
}

function PreviousPredictions({ history, onSelectUpload, selectedId }) {
  return (
    <section className="panel previous-live">
      <div className="section-header">
        <div>
          <div className="eyebrow">Database prediction history</div>
          <h2>Previous live predictions</h2>
        </div>
        <span className="muted">{history.length} uploads</span>
      </div>
      {history.length ? (
        <div className="previous-list">
          {history.map((item) => (
            <div
              key={item.upload_id}
              className={`previous-item ${selectedId === item.upload_id ? 'active' : ''}`}
              onClick={() => onSelectUpload && onSelectUpload(item.upload_id)}
              style={{ cursor: 'pointer' }}
              title="Click to view full forecast results"
            >
              <div>
                <strong>{item.input_month} {item.input_year} → {item.forecast_month} {item.forecast_year}</strong>
                <span>{new Date(item.created_at).toLocaleString()} · {item.stations_processed} stations · <span style={{ textDecoration: 'underline', color: 'var(--color-primary, #0ea5e9)' }}>View Details →</span></span>
              </div>
              <div>
                <strong>{number(item.average_wqi)}</strong>
                <span>avg predicted WQI</span>
              </div>
              <div>
                <StatusBadge kind={item.high_hotspots > 0 ? "high-hotspot" : "compliant"}>
                  {item.high_hotspots > 0 ? `${item.high_hotspots} alerts` : 'Normal / Compliant'}
                </StatusBadge>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="empty-state">No live predictions have been saved yet. Results will appear here after a successful upload.</p>
      )}
    </section>
  );
}

export function NotificationsPage() { const navigate = useNavigate(); const [notifications, setNotifications] = useState([]); const [filter, setFilter] = useState('all'); const load = () => request('/notifications').then(setNotifications).catch(() => setNotifications([])); useEffect(() => { load(); }, []); const filtered = notifications.filter((item) => filter === 'all' || filter === 'unread' && !item.is_read || filter === 'high' && item.severity === 'High Risk' || filter === 'read' && item.is_read); const markRead = async (item) => { await request(`/notifications/${item.notification_id}/read`, { method: 'PUT' }); window.dispatchEvent(new Event('notifications-updated')); navigate(`/stations/${item.station_code}`); }; return <><div className="page-heading"><div><div className="eyebrow">Single-source alerts / 12</div><h1>Messages & Notifications</h1><p>MySQL-backed forecast alerts generated by the live prediction workflow.</p></div><button className="button ghost" onClick={() => request('/notifications/read-all', { method: 'PUT' }).then(load)}><CheckCircle2 size={15} /> Mark all read</button></div><div className="filter-tabs notification-tabs">{[['all', 'All'], ['unread', 'Unread'], ['high', 'High Risk'], ['read', 'Read']].map(([key, label]) => <button key={key} className={filter === key ? 'selected' : ''} onClick={() => setFilter(key)}>{label}</button>)}</div><section className="panel notification-list">{filtered.length ? filtered.map((item) => <button className={item.is_read ? 'notification-item read' : 'notification-item'} key={item.notification_id} onClick={() => markRead(item)}><span className="notification-icon"><AlertTriangle size={17} /></span><span><strong>{item.station_name} · {item.forecast_month}</strong><small>{item.severity} · Station {item.station_code}, {item.state}</small><em>{item.message}</em></span><span className="notification-wqi">WQI {number(item.predicted_wqi)}</span></button>) : <p className="empty-state">No notifications in this filter.</p>}</section></>; }
