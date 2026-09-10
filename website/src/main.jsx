import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Link, Navigate, NavLink, Outlet, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom';
import { Activity, AlertTriangle, ArrowRight, BarChart3, Beaker, Bell, BookOpen, ChevronDown, Droplets, Leaf, LogIn, LogOut, MapPin, Menu, Search, Settings, ShieldCheck, UploadCloud, UserCircle, UserPlus, Waves, X } from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, CartesianGrid, Cell, LineChart, Line, PieChart, Pie, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import './styles.css';
import { LivePrediction, NotificationsPage } from './LivePrediction';
import HistoricalRiverMap from './HistoricalRiverMap';

const API = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:5000/api`;
const navItems = [
  ['Dashboard', '/dashboard'], ['River Map', '/river-map'], ['Forecast', '/forecast'], ['WQI Analysis', '/wqi'],
  ['Hotspot Analysis', '/hotspots'], ['CPCB Compliance', '/compliance'], ['Biological Assessment', '/biological'],
  ['Early Warning', '/early-warning'], ['Live Prediction', '/live-prediction'], ['Notifications', '/notifications'], ['About Project', '/about']
];

async function getApi(path, options = {}) { const response = await fetch(`${API}${path}`, { credentials: 'include', ...options }); if (!response.ok) throw new Error('Data service unavailable'); return response.json(); }
function useApi(path, initial = []) { const [data, setData] = useState(initial); const [loading, setLoading] = useState(Boolean(path)); const [error, setError] = useState(''); useEffect(() => { if (!path) { setLoading(false); return; } setLoading(true); getApi(path).then(setData).catch((err) => setError(err.message)).finally(() => setLoading(false)); }, [path]); return { data, loading, error }; }
const fmt = (value, digits = 1) => value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : Number(value).toFixed(digits);
const levelClass = (level = '') => level.toLowerCase().includes('high') ? 'high' : level.toLowerCase().includes('moderate') ? 'moderate' : 'low';
const warningClass = (level = '') => level.toLowerCase().replace(' ', '-');

function ForecastAlerts() { const { data, loading } = useApi('/notifications/high-risk'); return <section className="panel forecast-alerts"><SectionHeader eyebrow="Live forecast alerts" title="Active High Hotspot notifications" link={<Link to="/notifications" className="text-link">View all <ArrowRight size={14} /></Link>} />{loading ? <Loading /> : data.length ? <div className="forecast-alert-list">{data.slice(0, 5).map((item) => <Link key={item.notification_id} to="/notifications"><AlertTriangle size={16} /><span><strong>{item.station_name} · {item.forecast_month}</strong><small>{item.message}</small></span><Badge type="high">High Risk</Badge></Link>)}</div> : <p className="empty-state">No High Hotspot forecast notifications are active.</p>}</section> }
function NotificationBell() { const [open, setOpen] = useState(false); const [items, setItems] = useState([]); const load = () => getApi('/notifications/unread').then((data) => setItems(data.slice(0, 4))).catch(() => setItems([])); useEffect(() => { load(); window.addEventListener('notifications-updated', load); return () => window.removeEventListener('notifications-updated', load); }, []); return <div className="notification-bell"><button title="Notifications" onClick={() => { setOpen(!open); if (!open) load(); }}><Bell size={18} />{items.length > 0 && <b>{items.length}</b>}</button>{open && <div className="notification-dropdown"><div className="notification-dropdown-head"><strong>Recent alerts</strong><span>{items.length} unread</span></div>{items.length ? items.map((item) => <Link key={item.notification_id} to="/notifications" onClick={() => setOpen(false)}><AlertTriangle size={15} /><span><strong>{item.station_name}</strong><small>{item.forecast_month} · {item.severity}</small></span></Link>) : <p>No unread forecast alerts.</p>}<Link className="view-all-notifications" to="/notifications" onClick={() => setOpen(false)}>View all notifications <ArrowRight size={14} /></Link></div>}</div> }
function ProfileMenu() { const navigate = useNavigate(); const [open, setOpen] = useState(false); const [settings, setSettings] = useState(false); const [user, setUser] = useState(null); const [form, setForm] = useState({ full_name: '', mobile: '' }); const [message, setMessage] = useState(''); useEffect(() => { getApi('/auth/me').then((body) => { setUser(body.user); setForm({ full_name: body.user?.full_name || '', mobile: body.user?.mobile || '' }); }).catch(() => {}); }, []); const logout = async () => { await getApi('/auth/logout', { method: 'POST' }); navigate('/'); }; const save = async (event) => { event.preventDefault(); try { const body = await getApi('/auth/profile', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) }); setUser(body.user); setMessage('Profile updated'); } catch (error) { setMessage(error.message); } }; if (!user) return null; return <div className="profile-menu"><button className="profile-trigger" onClick={() => setOpen(!open)}><UserCircle size={21} /><span>{user.full_name}</span><ChevronDown size={14} /></button>{open && <div className="profile-dropdown"><div className="profile-summary"><UserCircle size={28} /><div><strong>{user.full_name}</strong><small>{user.email}</small></div></div><button onClick={() => setSettings(true)}><Settings size={15} />Profile settings</button><button onClick={logout}><LogOut size={15} />Log out</button></div>}{settings && <div className="profile-modal-backdrop" onClick={() => setSettings(false)}><div className="profile-modal" onClick={(event) => event.stopPropagation()}><button className="auth-close" onClick={() => setSettings(false)}><X size={18} /></button><span className="eyebrow">Account</span><h2>Profile settings</h2><p>Update your basic account information.</p><form onSubmit={save}><label>Name<input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} required /></label><label>Email<input value={user.email} disabled /></label><label>Mobile number <small>(optional)</small><input value={form.mobile} onChange={(event) => setForm({ ...form, mobile: event.target.value })} placeholder="Optional" /></label>{message && <span className="profile-message">{message}</span>}<button className="button primary" type="submit">Save changes</button></form></div></div>}</div> }
function Layout() { const [open, setOpen] = useState(false); const location = useLocation(); return <div className="app-shell"><aside className={open ? 'sidebar open' : 'sidebar'}><div className="brand"><div className="brand-mark"><Waves size={21} /></div><div><strong>Ganga Watch</strong><span>Research intelligence</span></div><button className="mobile-close" onClick={() => setOpen(false)}><X size={18} /></button></div><div className="side-label">Workspace</div><nav>{navItems.map(([label, path]) => <NavLink key={path} to={path} onClick={() => setOpen(false)} className={({ isActive }) => isActive ? 'active' : ''}>{iconFor(label)}<span>{label}</span></NavLink>)}</nav><div className="sidebar-note"><div className="pulse-dot" /><div><strong>Forecast horizon</strong><span>Jan–Dec 2026</span></div></div></aside><div className="main-shell"><header className="topbar"><button className="menu-button" onClick={() => setOpen(true)}><Menu size={20} /></button><div className="crumb"><strong>Ganga Watch</strong></div><div className="top-actions"><NotificationBell /><ProfileMenu /></div></header><main>{location.pathname === '/early-warning' && <ForecastAlerts />}<Outlet /></main></div></div> }
function iconFor(label) { const props = { size: 17, strokeWidth: 1.8 }; const icons = { Dashboard: <BarChart3 {...props} />, 'River Map': <MapPin {...props} />, Forecast: <Activity {...props} />, 'WQI Analysis': <Droplets {...props} />, 'Hotspot Analysis': <AlertTriangle {...props} />, 'CPCB Compliance': <ShieldCheck {...props} />, 'Biological Assessment': <Leaf {...props} />, 'Early Warning': <Waves {...props} />, 'Live Prediction': <UploadCloudIcon {...props} />, Notifications: <Bell {...props} />, 'About Project': <BookOpen {...props} /> }; return icons[label]; }
function UploadCloudIcon(props) { return <UploadCloud {...props} />; }
function PageHeading({ eyebrow, title, description, action }) { return <div className="page-heading"><div>{eyebrow && eyebrow !== 'System overview / 01' && <div className="eyebrow">{eyebrow}</div>}<h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</div> }
function Loading() { return <div className="loading"><span />Loading project data...</div> }
function ErrorBox({ message }) { return <div className="error-box"><AlertTriangle size={18} />{message}. Start the Flask service to connect live project data.</div> }
function StatCard({ label, value, unit, tone = 'blue', detail }) { return <div className={`stat-card ${tone}`}><div className="stat-top"><span>{label}</span><Activity size={16} /></div><strong>{value}<small>{unit}</small></strong>{detail && <span className="stat-detail">{detail}</span>}</div> }
function SectionHeader({ eyebrow, title, link }) { return <div className="section-header"><div><div className="eyebrow">{eyebrow}</div><h2>{title}</h2></div>{link}</div> }
function Badge({ children, type }) { return <span className={`badge ${type || levelClass(children)}`}>{children}</span> }
function Sparkline({ data, color = '#168c8c', dataKey = 'value' }) { return <ResponsiveContainer width="100%" height="100%"><AreaChart data={data}><Area type="monotone" dataKey={dataKey} stroke={color} fill={color} fillOpacity={.12} strokeWidth={2} dot={false} /></AreaChart></ResponsiveContainer> }
function DataTable({ columns, rows, onRow }) { return <div className="table-wrap"><table><thead><tr>{columns.map(([key, label]) => <th key={key}>{label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={row['Station Code'] || row.station_code || index} onClick={() => onRow?.(row)}>{columns.map(([key]) => <td key={key}>{key === 'Hotspot_Level' || key === 'Warning_Level' ? <Badge>{row[key]}</Badge> : row[key] ?? '—'}</td>)}</tr>)}</tbody></table></div> }

function Dashboard() { const { data, loading, error } = useApi('/dashboard-summary', {}); const { data: states } = useApi('/state-summary'); const { data: forecast } = useApi('/forecast'); const chart = useMemo(() => Object.values(forecast.reduce((acc, row) => { const key = row.Forecast_Month_No; acc[key] ||= { month: row.Forecast_Month, wqi: row.Pred_WQI }; return acc; }, {})), [forecast]); return <><PageHeading eyebrow="System overview / 01" title="Ganga River intelligence" description="A research decision-support view of predicted water quality across the 2026 forecast horizon." action={<Link className="button primary" to="/river-map">Explore river <ArrowRight size={16} /></Link>} />{error && <ErrorBox message={error} />}{loading ? <Loading /> : <><div className="stats-grid"><StatCard label="Monitoring stations" value={data.total_stations} unit=" sites" detail="Across 5 river states" /><StatCard label="Average predicted WQI" value={fmt(data.average_predicted_wqi)} unit=" / 100" tone="teal" detail="Project-defined index" /><StatCard label="Forecast horizon" value={data.forecast_months} unit=" months" tone="ink" detail="2026 predicted values" /><StatCard label="High hotspots" value={data.high_hotspots} unit=" stations" tone="orange" detail={`${data.moderate_hotspots} moderate hotspots`} /></div><div className="dashboard-grid"><section className="panel chart-panel"><SectionHeader eyebrow="Predicted WQI / 2026" title="River health trajectory" link={<Badge type="forecast">Forecast values</Badge>} /><div className="chart-large"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chart}><defs><linearGradient id="wqiFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#168c8c" stopOpacity=".28" /><stop offset="100%" stopColor="#168c8c" stopOpacity="0" /></linearGradient></defs><CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#dfe9e7" /><XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: '#71817e', fontSize: 11 }} /><YAxis domain={[0, 100]} tickLine={false} axisLine={false} tick={{ fill: '#71817e', fontSize: 11 }} /><Tooltip /><Area type="monotone" dataKey="wqi" stroke="#168c8c" fill="url(#wqiFill)" strokeWidth={3} /></AreaChart></ResponsiveContainer></div><div className="chart-caption"><span><i className="legend-dot teal" /> Predicted WQI</span><span>DO 40% · pH 30% · BOD 30%</span></div></section><section className="panel state-panel"><SectionHeader eyebrow="By geography" title="State signal" link={<Link to="/river-map" className="text-link">View map <ArrowRight size={14} /></Link>} /><div className="state-list">{states.slice(0, 5).map((state) => <div className="state-row" key={state.State}><div className="state-name"><span className="state-icon"><MapPin size={14} /></span><strong>{state.State}</strong></div><div className="state-metric"><strong>{fmt(state.average_wqi)}</strong><span>WQI</span></div><div className="mini-bar"><span style={{ width: `${Math.max(8, state.average_wqi)}%` }} /></div></div>)}</div><Link className="button ghost full" to="/about">Read methodology <ArrowRight size={15} /></Link></section></div><div className="dashboard-grid lower"><section className="panel metric-band"><div><span className="eyebrow">Chemical signals</span><h3>Three parameters, one river story.</h3><p>Forecasts are model-generated 2026 values, evaluated against CPCB Class B reference criteria.</p></div><div className="metric-stack"><div><span>DO</span><strong>{fmt(data.average_do)} <small>mg/L</small></strong></div><div><span>pH</span><strong>{fmt(data.average_ph, 2)}</strong></div><div><span>BOD</span><strong>{fmt(data.average_bod)} <small>mg/L</small></strong></div></div></section><section className="panel warning-preview"><div className="warning-art"><AlertTriangle size={28} /></div><div><span className="eyebrow">Project-based signal</span><h3>Early warning, with context.</h3><p>Potential risk conditions combine predicted WQI and criterion violations. They are analytical indicators, not official alerts.</p><Link to="/early-warning" className="text-link">Open warning center <ArrowRight size={15} /></Link></div></section></div></>}</> }

function RiverMap() { const [filters, setFilters] = useState({ search: '', state: '', hotspot_level: '' }); const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value)).toString(); const { data, loading, error } = useApi(`/stations?${query}`); const [selected, setSelected] = useState(null); const states = ['Uttarakhand', 'Uttar Pradesh', 'Bihar', 'Jharkhand', 'West Bengal']; return <><PageHeading eyebrow="Monitoring network / 02" title="River corridor view" description="Explore station-level project classifications across the Ganga monitoring network." action={<Link className="button ghost" to="/hotspots">Open hotspot table <ArrowRight size={16} /></Link>} /><div className="filter-bar"><div className="search-box"><Search size={17} /><input value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} placeholder="Search station or code" /></div><select value={filters.state} onChange={(e) => setFilters({ ...filters, state: e.target.value })}><option value="">All states</option>{states.map((state) => <option key={state}>{state}</option>)}</select><select value={filters.hotspot_level} onChange={(e) => setFilters({ ...filters, hotspot_level: e.target.value })}><option value="">All hotspot levels</option><option>High Hotspot</option><option>Moderate Hotspot</option><option>Low/No Hotspot</option></select></div>{error && <ErrorBox message={error} />}<div className="map-layout"><section className="river-map panel"><div className="map-top"><div><span className="eyebrow">Schematic station distribution</span><h2>Ganga monitoring corridor</h2></div><span className="map-note"><MapPin size={14} /> Coordinates not present in source exports</span></div><div className="river-canvas"><div className="river-line"><span>UTTARAKHAND</span><span>UTTAR PRADESH</span><span>BIHAR</span><span>JHARKHAND</span><span>WEST BENGAL</span></div>{data.map((station, index) => <button key={station.station_code} className={`map-station ${levelClass(station.hotspot_level)}`} style={{ left: `${9 + (index % 10) * 9}%`, top: `${20 + (index % 4) * 17 + Math.floor(index / 10) * 4}%` }} onClick={() => setSelected(station)} title={station.station_name}><span /><b>{station.station_code}</b></button>)}<div className="map-disclaimer">Schematic corridor grouping by state. Marker positions are for station discovery only and are not geographic coordinates.</div></div><div className="map-legend"><span><i className="legend-dot high" /> High hotspot</span><span><i className="legend-dot moderate" /> Moderate hotspot</span><span><i className="legend-dot low" /> Low / no hotspot</span></div></section><section className="panel station-list-panel"><SectionHeader eyebrow={`${data.length} results`} title="Stations" /><div className="station-cards">{loading ? <Loading /> : data.slice(0, 8).map((station) => <button className="station-card" key={station.station_code} onClick={() => setSelected(station)}><div><span className="station-code">{station.station_code}</span><h3>{station.station_name}</h3><span className="muted">{station.state}</span></div><div className="station-card-right"><Badge>{station.hotspot_level}</Badge><strong>{fmt(station.average_wqi)}</strong><span>predicted WQI</span></div></button>)}</div></section></div>{selected && <StationPopup station={selected} onClose={() => setSelected(null)} />}</> }
function StationPopup({ station, onClose }) { return <div className="modal-backdrop" onClick={onClose}><div className="station-popup" onClick={(e) => e.stopPropagation()}><button className="modal-close" onClick={onClose}><X size={18} /></button><span className="eyebrow">Station {station.station_code}</span><h2>{station.station_name}</h2><p className="muted">{station.state}</p><Badge>{station.hotspot_level}</Badge><div className="popup-stats"><div><strong>{fmt(station.average_wqi)}</strong><span>Mean predicted WQI</span></div><div><strong>{fmt(station.average_bod)}</strong><span>Mean BOD mg/L</span></div><div><strong>{fmt(station.CPCB_Violation_Percent)}%</strong><span>Criterion violations</span></div></div><p className="notice"><AlertTriangle size={16} /> A project forecast classification, not confirmed pollution or an official designation.</p><Link className="button primary full" to={`/stations/${station.station_code}`}>Open station details <ArrowRight size={15} /></Link></div></div> }

function ForecastPage() {
  const [year, setYear] = useState('2026');
  const [station, setStation] = useState('');
  const { data: stations } = useApi(`/stations?year=${year}`);
  const selected = station || stations[0]?.station_code;
  const { data, loading } = useApi(selected ? `/forecast/${selected}?year=${year}` : null);
  const YEARS = Array.from({ length: 13 }, (_, i) => 2026 - i);

  useEffect(() => {
    if (!station && stations[0]) {
      setStation(stations[0].station_code);
    } else if (station && stations.length && !stations.some((s) => String(s.station_code) === String(station))) {
      setStation(stations[0].station_code);
    }
  }, [stations, station]);

  const currentStation = stations.find((s) => String(s.station_code) === String(selected));
  const rows = Array.isArray(data) ? data : [];
  const chart = rows.map((row) => ({
    month: (row.Forecast_Month || row.Month || '')?.slice(0, 3),
    DO: row.Pred_DO ?? row.DO,
    pH: row.Pred_pH ?? row.pH,
    BOD: row.Pred_BOD ?? row.BOD,
  }));

  const stats = [
    ['DO', 'Pred_DO', 'mg/L', '#168c8c'],
    ['pH', 'Pred_pH', '', '#d38b35'],
    ['BOD', 'Pred_BOD', 'mg/L', '#cf5b4f'],
  ];

  return (
    <>
      <PageHeading
        eyebrow="Parameter analysis / 03"
        title={`${year} parameter & forecast explorer`}
        description={`Inspect monthly dissolved oxygen, pH, and biochemical oxygen demand across stations for ${year}.`}
      />
      <div className="filter-bar forecast-filters">
        <label>
          Station
          <select value={station} onChange={(e) => setStation(e.target.value)}>
            {stations.map((s) => (
              <option key={s.station_code} value={s.station_code}>
                {s.station_name} · {s.station_code}
              </option>
            ))}
          </select>
        </label>
        <label>
          Year
          <select value={year} onChange={(e) => setYear(e.target.value)}>
            {YEARS.map((y) => (
              <option key={y} value={y}>
                {y}{y === 2026 ? ' (Forecast)' : ''}
              </option>
            ))}
          </select>
        </label>
      </div>
      {loading ? (
        <Loading />
      ) : (
        <>
          {selected && (
            <div className="forecast-hero">
              <div>
                <span className="eyebrow">Station {selected} · {year === '2026' ? 'forecast values' : `${year} parameters`}</span>
                <h2>{currentStation?.station_name || `Station ${selected}`}</h2>
                <p>{year === '2026' ? 'Monthly 2026 predictions generated by the model.' : `Monthly ${year} water quality parameters and trajectory.`}</p>
              </div>
              <div className="forecast-hero-badge"><Activity size={17} /> {rows.length}-month view</div>
            </div>
          )}
          <div className="parameter-grid">
            {stats.map(([label, key, unit, color]) => {
              const values = rows.map((r) => Number(r[key] ?? r[label])).filter(Number.isFinite);
              const avg = values.reduce((a, b) => a + b, 0) / (values.length || 1);
              const min = values.length ? Math.min(...values) : 0;
              const max = values.length ? Math.max(...values) : 0;
              return (
                <div className="panel parameter-card" key={label}>
                  <div className="param-head">
                    <span className="param-symbol" style={{ background: `${color}18`, color }}>{label}</span>
                    <Badge type={year === '2026' ? 'forecast' : 'historical'}>{year === '2026' ? 'Predicted' : 'Observed'}</Badge>
                  </div>
                  <span className="param-label">Mean {label}</span>
                  <strong>{fmt(avg, 2)}<small>{unit}</small></strong>
                  <div className="param-range">
                    <span>Min {fmt(min, 2)}</span>
                    <span>Max {fmt(max, 2)}</span>
                  </div>
                  <div className="spark">
                    <Sparkline data={values.map((value) => ({ value }))} color={color} />
                  </div>
                </div>
              );
            })}
          </div>
          <section className="panel forecast-chart-panel">
            <SectionHeader
              eyebrow="Monthly trajectory"
              title="Parameter forecast"
              link={<Badge type={year === '2026' ? 'forecast' : 'historical'}>{year === '2026' ? '2026 forecast' : `${year} parameters`}</Badge>}
            />
            <div className="chart-medium">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chart}>
                  <CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#dfe9e7" />
                  <XAxis dataKey="month" tickLine={false} axisLine={false} />
                  <YAxis tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="DO" stroke="#168c8c" strokeWidth={3} dot={false} />
                  <Line type="monotone" dataKey="pH" stroke="#d38b35" strokeWidth={3} dot={false} />
                  <Line type="monotone" dataKey="BOD" stroke="#cf5b4f" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-caption">
              <span><i className="legend-dot teal" /> DO</span>
              <span><i className="legend-dot gold" /> pH</span>
              <span><i className="legend-dot coral" /> BOD</span>
            </div>
          </section>
        </>
      )}
    </>
  );
}


function WQIPage() {
  const [year, setYear] = useState('2026');
  const [station, setStation] = useState('');
  const { data: stations } = useApi(`/stations?year=${year}`);
  const { data, loading, error } = useApi(`/wqi/monthly-trend?year=${year}&station=${station}`);

  const YEARS = Array.from({ length: 13 }, (_, i) => 2026 - i);
  const isForecast = String(year) === '2026';

  const monthlyData = data?.monthly || [];
  const allYears = data?.all_years || [];
  const avgWqi = data?.average_wqi ?? 0;
  const bestMonth = data?.best_month || '—';
  const bestWqi = data?.best_wqi ?? 0;
  const lowestMonth = data?.lowest_month || '—';
  const lowestWqi = data?.lowest_wqi ?? 0;
  const seasonalSpan = bestWqi && lowestWqi ? (bestWqi - lowestWqi).toFixed(2) : '—';

  const wqiValues = monthlyData.map((d) => d.WQI).filter(Boolean);
  const minWqi = wqiValues.length ? Math.floor(Math.min(...wqiValues) - 2) : 80;
  const maxWqi = wqiValues.length ? Math.ceil(Math.max(...wqiValues) + 2) : 100;

  return (
    <>
      <PageHeading
        eyebrow="Index synthesis / 04"
        title="WQI analysis"
        description="The project-defined Water Quality Index combines continuous dissolved oxygen, pH, and biochemical oxygen demand into an interpretable 0–100 signal across all years."
      />

      <div className="filter-bar forecast-filters">
        <label>
          Scope / Station
          <select value={station} onChange={(e) => setStation(e.target.value)}>
            <option value="">All Monitoring Stations (Basin Average)</option>
            {(Array.isArray(stations) ? stations : []).map((s) => (
              <option key={s.station_code} value={s.station_code}>
                {s.station_name} · {s.station_code}
              </option>
            ))}
          </select>
        </label>
        <label>
          Year
          <select value={year} onChange={(e) => setYear(e.target.value)}>
            {YEARS.map((y) => (
              <option key={y} value={y}>
                {y}{y === 2026 ? ' (Forecast)' : ''}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <ErrorBox message={error} />}

      {loading ? (
        <Loading />
      ) : (
        <>
          <div className="wqi-stats-grid">
            <StatCard
              label={isForecast ? 'Average predicted WQI' : `Average observed WQI (${year})`}
              value={fmt(avgWqi, 2)}
              unit=" / 100"
              tone="teal"
              detail={station ? 'Selected monitoring site' : 'Ganga basin average'}
            />
            <StatCard
              label={isForecast ? 'Best forecast month' : `Best month (${year})`}
              value={bestMonth}
              tone="blue"
              detail={`Highest monthly index: ${fmt(bestWqi, 2)} WQI`}
            />
            <StatCard
              label={isForecast ? 'Lowest forecast month' : `Lowest month (${year})`}
              value={lowestMonth}
              tone="orange"
              detail={`Lowest monthly index: ${fmt(lowestWqi, 2)} WQI`}
            />
            <StatCard
              label="Seasonal variation"
              value={seasonalSpan}
              unit=" pts"
              tone="ink"
              detail="Spread between peak & trough"
            />
          </div>

          {allYears.length > 0 && (
            <section className="panel" style={{ marginBottom: '20px' }}>
              <SectionHeader
                eyebrow="Historical & forecast horizon"
                title="Best month for all years (2014–2026)"
                link={<Badge type="forecast">Peak index per year</Badge>}
              />
              <div className="wqi-years-grid">
                {allYears.map((yr) => {
                  const isSelected = String(yr.year) === String(year);
                  return (
                    <button
                      key={yr.year}
                      className={`wqi-year-card ${isSelected ? 'active' : ''}`}
                      onClick={() => setYear(String(yr.year))}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <strong style={{ fontSize: '13px', color: isSelected ? '#168c8c' : 'var(--deep)' }}>
                          {yr.year}
                        </strong>
                        {yr.is_forecast && <Badge type="forecast">Forecast</Badge>}
                      </div>
                      <div style={{ fontSize: '11px', fontWeight: '700', color: '#2875a5' }}>
                        {yr.best_month}
                      </div>
                      <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '2px' }}>
                        Peak: <strong>{fmt(yr.best_wqi, 1)}</strong> · Avg: {fmt(yr.average_wqi, 1)}
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>
          )}

          <section className="panel" style={{ marginBottom: '20px' }}>
            <SectionHeader
              eyebrow="Monthly signal"
              title={`${year} predicted & observed WQI trend`}
              link={
                <Badge type={isForecast ? 'forecast' : 'historical'}>
                  {isForecast ? '2026 forecast trajectory' : `${year} monthly observations`}
                </Badge>
              }
            />

            <div style={{ height: '320px', width: '100%', marginTop: '10px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={monthlyData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="wqiGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#168c8c" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#168c8c" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#dfe9e7" />
                  <XAxis
                    dataKey="month"
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(m) => m.slice(0, 3)}
                  />
                  <YAxis
                    domain={[minWqi, maxWqi]}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v) => Number(v).toFixed(0)}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const item = payload[0].payload;
                      return (
                        <div
                          style={{
                            background: '#fff',
                            border: '1px solid var(--line)',
                            borderRadius: '8px',
                            padding: '10px 14px',
                            boxShadow: '0 8px 25px rgba(7,59,76,0.12)',
                            fontSize: '11px'
                          }}
                        >
                          <strong style={{ fontSize: '13px', color: 'var(--deep)', display: 'block', marginBottom: '4px' }}>
                            {item.month} {year}
                          </strong>
                          <div style={{ color: '#168c8c', fontWeight: '800', fontSize: '14px', marginBottom: '6px' }}>
                            WQI: {fmt(item.WQI, 2)}
                          </div>
                          <div style={{ color: 'var(--muted)', display: 'grid', gap: '2px', fontSize: '10px' }}>
                            <span>DO: <b>{fmt(item.DO, 2)} mg/L</b></span>
                            <span>pH: <b>{fmt(item.pH, 2)}</b></span>
                            <span>BOD: <b>{fmt(item.BOD, 2)} mg/L</b></span>
                          </div>
                        </div>
                      );
                    }}
                  />
                  <Area
                    dataKey="WQI"
                    type="monotone"
                    stroke="#168c8c"
                    strokeWidth={3}
                    fill="url(#wqiGradient)"
                    dot={{ fill: '#168c8c', r: 4, strokeWidth: 2, stroke: '#fff' }}
                    activeDot={{ r: 6, fill: '#073b4c', stroke: '#168c8c', strokeWidth: 2 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="wqi-monthly-grid">
              {monthlyData.map((m) => {
                const isBest = m.month === bestMonth;
                const isLowest = m.month === lowestMonth;
                return (
                  <div
                    key={m.month_no}
                    style={{
                      background: isBest ? '#e5f6f2' : isLowest ? '#fbeee9' : '#f9fbfa',
                      border: isBest ? '1px solid #168c8c' : isLowest ? '1px solid #cf5b4f' : '1px solid var(--line)',
                      borderRadius: '8px',
                      padding: '10px 8px',
                      textAlign: 'center'
                    }}
                  >
                    <span style={{ fontSize: '10px', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {m.month.slice(0, 3)}
                    </span>
                    <strong
                      style={{
                        display: 'block',
                        font: '800 15px Manrope',
                        color: isBest ? '#168c8c' : isLowest ? '#cf5b4f' : 'var(--deep)',
                        marginTop: '2px'
                      }}
                    >
                      {fmt(m.WQI, 2)}
                    </strong>
                    <div style={{ fontSize: '9px', color: 'var(--muted)', marginTop: '4px', lineHeight: '1.4' }}>
                      DO {fmt(m.DO, 1)}<br />
                      BOD {fmt(m.BOD, 1)}
                    </div>
                    {isBest && (
                      <span style={{ display: 'inline-block', marginTop: '5px', fontSize: '9px', fontWeight: '700', color: '#168c8c' }}>
                        Peak ★
                      </span>
                    )}
                    {isLowest && (
                      <span style={{ display: 'inline-block', marginTop: '5px', fontSize: '9px', fontWeight: '700', color: '#cf5b4f' }}>
                        Lowest
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        </>
      )}
    </>
  );
}

function HotspotPage() { const { data, loading, error } = useApi('/hotspots'); const [query, setQuery] = useState(''); const filtered = data.filter((row) => `${row['Station Name']} ${row['Station Code']} ${row.State}`.toLowerCase().includes(query.toLowerCase())); const columns = [['Station Name', 'Station'], ['Station Code', 'Code'], ['State', 'State'], ['Mean_WQI', 'Mean WQI'], ['Min_WQI', 'Min WQI'], ['Mean_BOD', 'Mean BOD'], ['BOD_Exceed_Percent', 'BOD exceed.'], ['CPCB_Violation_Percent', 'Overall violation'], ['Hotspot_Level', 'Project level']]; return <><PageHeading eyebrow="Risk screening / 05" title="Hotspot analysis" description="Potential future risk conditions identified by the project's forecast classification logic." action={<div className="classification-tag"><AlertTriangle size={15} /> Project Forecast Classification</div>} /><div className="stats-grid compact"><StatCard label="High hotspot" value={data.filter((r) => r.Hotspot_Level === 'High Hotspot').length} unit=" stations" tone="orange" /><StatCard label="Moderate hotspot" value={data.filter((r) => r.Hotspot_Level === 'Moderate Hotspot').length} unit=" stations" tone="gold" /><StatCard label="Low / no hotspot" value={data.filter((r) => r.Hotspot_Level === 'Low/No Hotspot').length} unit=" stations" tone="teal" /></div>{error && <ErrorBox message={error} />}{loading ? <Loading /> : <section className="panel table-panel"><div className="table-toolbar"><div><span className="eyebrow">Sortable-ready station inventory</span><h2>Potential pollution hotspots</h2></div><div className="search-box small"><Search size={16} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter stations" /></div></div><DataTable columns={columns} rows={filtered} onRow={(row) => window.location.href = `/stations/${row['Station Code']}`} /><div className="table-foot"><span>{filtered.length} stations shown</span><span>High: WQI &lt; 85 and violations ≥ 75% · Moderate: WQI &lt; 90 and violations ≥ 25%</span></div></section>}</> }

function CompliancePage() { const { data, loading, error } = useApi('/cpcb-compliance'); const [parameter, setParameter] = useState('overall'); const rows = data.map((row) => ({ ...row, status: Number(row.CPCB_Violation_Percent) > 0 ? 'Criterion Exceeded' : 'Within Criterion' })); return <><PageHeading eyebrow="Reference criteria / 06" title="CPCB compliance view" description="Station-wise screening against CPCB Class B reference criteria. Status here is analytical and does not represent certification." /><div className="criteria-grid"><div><span className="criteria-key">DO</span><strong>≥ 5 mg/L</strong><span>Dissolved oxygen</span></div><div><span className="criteria-key">pH</span><strong>6.5–8.5</strong><span>Hydrogen ion concentration</span></div><div><span className="criteria-key">BOD</span><strong>≤ 3 mg/L</strong><span>Biochemical oxygen demand</span></div></div><div className="filter-tabs"><button className={parameter === 'overall' ? 'selected' : ''} onClick={() => setParameter('overall')}>Overall status</button><button className={parameter === 'bod' ? 'selected' : ''} onClick={() => setParameter('bod')}>BOD exceedance</button><button className={parameter === 'do' ? 'selected' : ''} onClick={() => setParameter('do')}>DO violation</button><button className={parameter === 'ph' ? 'selected' : ''} onClick={() => setParameter('ph')}>pH violation</button></div>{error && <ErrorBox message={error} />}{loading ? <Loading /> : <section className="panel table-panel"><DataTable columns={[["Station Name", "Station"], ["State", "State"], ["Mean_BOD", "Mean BOD"], ["BOD_Exceed_Percent", "BOD exceed."], ["DO_Violation_Percent", "DO violation"], ["pH_Violation_Percent", "pH violation"], ["CPCB_Violation_Percent", "Overall violation"], ["status", "Status"]]} rows={rows} /></section>}<div className="callout neutral"><ShieldCheck size={21} /><div><strong>Interpretation</strong><span>“Within Criterion” and “Criterion Exceeded” describe comparison with the supplied reference thresholds for forecast values. They are not official regulatory declarations.</span></div></div></> }

function BiologicalPage() { const { data, loading, error } = useApi('/biological'); const quality = data.reduce((acc, row) => { const name = row.Biological_Quality || 'Unknown'; acc[name] = (acc[name] || 0) + 1; return acc; }, {}); return <><PageHeading eyebrow="Ecological context / 07" title="Biological assessment" description="Historical Saprobic Score observations provide a complementary ecological lens alongside chemical forecasting." action={<Badge type="historical">Historical observations only</Badge>} />{error && <ErrorBox message={error} />}{loading ? <Loading /> : <><div className="bio-banner"><div className="bio-icon"><Leaf size={25} /></div><div><strong>Separate biological branch</strong><p>Saprobic assessment is not another ML model and is not used as direct validation of chemical WQI. No biological observations are extended into the 2026 forecast.</p></div></div><div className="dashboard-grid"><section className="panel chart-panel"><SectionHeader eyebrow="Observed quality distribution" title="Biological quality classes" /><div className="bio-bars">{Object.entries(quality).map(([key, value]) => <div className="bio-bar" key={key}><div><span>{key}</span><strong>{value}</strong></div><div className="bar-track"><span style={{ width: `${value / data.length * 100}%` }} /></div></div>)}</div></section><section className="panel"><SectionHeader eyebrow="Available records" title="Seasonal observations" /><div className="season-pills"><span>Pre-monsoon</span><strong>{data.filter((r) => r.Season === 'Pre').length}</strong><span>Post-monsoon</span><strong>{data.filter((r) => r.Season === 'Post').length}</strong></div><p className="panel-note">Recorded zero scores are treated as Unknown because they fall outside the project classification range.</p></section></div><section className="panel table-panel"><SectionHeader eyebrow={`${data.length} observations`} title="Station-wise biological records" /><DataTable columns={[["Location", "Location"], ["State", "State"], ["Year", "Year"], ["Season", "Season"], ["Saprobic_Score", "Saprobic score"], ["Biological_Quality", "Biological quality"]]} rows={data.slice(0, 50)} /></section></>}</> }

function StatePage() { const { data, loading, error } = useApi('/state-summary'); return <><PageHeading eyebrow="Comparative lens / 08" title="State-wise analysis" description="Compare predicted signals and criterion-exceedance percentages across the five monitored Ganga states." />{error && <ErrorBox message={error} />}{loading ? <Loading /> : <section className="panel table-panel"><DataTable columns={[["State", "State"], ["station_count", "Stations"], ["average_wqi", "Avg predicted WQI"], ["average_bod", "Avg BOD"], ["average_do", "Avg DO"], ["average_ph", "Avg pH"], ["predicted_hotspots", "Predicted hotspots"], ["criterion_exceedance", "Criterion exceed."]]} rows={data.map((row) => ({ ...row, average_wqi: fmt(row.average_wqi), average_bod: fmt(row.average_bod), average_do: fmt(row.average_do), average_ph: fmt(row.average_ph, 2), criterion_exceedance: `${fmt(row.criterion_exceedance)}%` }))} /></section>}</> }

function EarlyWarning() { const { data, loading, error } = useApi('/early-warning'); const counts = data.reduce((acc, row) => { acc[row.Warning_Level] = (acc[row.Warning_Level] || 0) + 1; return acc; }, {}); return <><PageHeading eyebrow="Action lens / 09" title="Early warning center" description="Project-based analytical indicators that combine forecast quality, CPCB reference comparisons, and hotspot classification." action={<div className="classification-tag"><Waves size={15} /> Analytical project warnings</div>} /><div className="warning-grid">{['Normal', 'Watch', 'Warning', 'High Warning'].map((level) => <div className={`warning-card ${warningClass(level)}`} key={level}><span className="warning-icon">{level === 'Normal' ? <ShieldCheck size={19} /> : <AlertTriangle size={19} />}</span><span>{level}</span><strong>{counts[level] || 0}</strong><small>stations</small></div>)}</div>{error && <ErrorBox message={error} />}{loading ? <Loading /> : <section className="panel table-panel"><SectionHeader eyebrow="Prioritised stations" title="Forecast warning indicators" /><DataTable columns={[["Station Name", "Station"], ["State", "State"], ["Mean_WQI", "Mean WQI"], ["Mean_BOD", "Mean BOD"], ["CPCB_Violation_Percent", "Overall violation"], ["Hotspot_Level", "Hotspot"], ["Warning_Level", "Warning"]]} rows={data.sort((a, b) => ['High Warning', 'Warning', 'Watch', 'Normal'].indexOf(a.Warning_Level) - ['High Warning', 'Warning', 'Watch', 'Normal'].indexOf(b.Warning_Level))} /></section>}<div className="callout orange"><AlertTriangle size={21} /><div><strong>Important context</strong><span>Warnings are model-based/project indicators for research communication. A condition such as Varanasi D/S with predicted BOD around 3.46 mg/L is a high-risk forecast condition, not confirmed pollution.</span></div></div></> }

function StationDetails() { const { code } = useParams(); const { data: station, loading: stationLoading, error } = useApi(`/stations/${code}`, {}); const { data: forecast } = useApi(`/forecast/${code}`); const { data: hotspot } = useApi(`/hotspots/${code}`, {}); const { data: bio } = useApi(`/biological/${code}`); if (stationLoading) return <Loading />; if (error) return <ErrorBox message={error} />; const chart = forecast.map((row) => ({ month: row.Forecast_Month?.slice(0, 3), DO: row.Pred_DO, pH: row.Pred_pH, BOD: row.Pred_BOD, WQI: row.Pred_WQI })); return <><PageHeading eyebrow={`Station detail / ${code}`} title={station.station_name} description={`${station.state} · Complete station intelligence across forecast, WQI, compliance, hotspot, and biological context.`} action={<Badge>{station.hotspot_level}</Badge>} /><div className="station-identity"><div className="identity-code">{code}</div><div><span className="eyebrow">Average predicted WQI</span><strong>{fmt(station.average_wqi)} <small>/ 100</small></strong></div><div><span className="eyebrow">Mean BOD</span><strong>{fmt(station.average_bod)} <small>mg/L</small></strong></div><div><span className="eyebrow">Forecast horizon</span><strong>{station.forecast_months} <small>months</small></strong></div></div><div className="dashboard-grid"><section className="panel chart-panel"><SectionHeader eyebrow="Forecast" title="Parameter trends" link={<Badge type="forecast">2026 forecast</Badge>} /><div className="chart-medium"><ResponsiveContainer width="100%" height="100%"><LineChart data={chart}><CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#dfe9e7" /><XAxis dataKey="month" tickLine={false} axisLine={false} /><YAxis tickLine={false} axisLine={false} /><Tooltip /><Line dataKey="DO" stroke="#168c8c" strokeWidth={3} dot={false} /><Line dataKey="pH" stroke="#d38b35" strokeWidth={3} dot={false} /><Line dataKey="BOD" stroke="#cf5b4f" strokeWidth={3} dot={false} /></LineChart></ResponsiveContainer></div></section><section className="panel detail-side"><SectionHeader eyebrow="Hotspot analysis" title="Project classification" /><Badge>{hotspot.Hotspot_Level}</Badge><div className="detail-list"><div><span>Mean WQI</span><strong>{fmt(hotspot.Mean_WQI)}</strong></div><div><span>BOD exceedance</span><strong>{fmt(hotspot.BOD_Exceed_Percent)}%</strong></div><div><span>DO violations</span><strong>{fmt(hotspot.DO_Violation_Percent)}%</strong></div><div><span>pH violations</span><strong>{fmt(hotspot.pH_Violation_Percent)}%</strong></div></div><p className="panel-note">A project forecast classification, not an official hotspot designation.</p></section></div><section className="panel table-panel"><SectionHeader eyebrow="Biological context" title="Available Saprobic observations" link={<Badge type="historical">Historical only</Badge>} />{bio.length ? <DataTable columns={[["Year", "Year"], ["Season", "Season"], ["Saprobic_Score", "Score"], ["Biological_Quality", "Quality"]]} rows={bio} /> : <p className="empty-state">No Saprobic observations are available for this station in the supplied datasets.</p>}</section></> }

function About() {
  const objectives = [
    {
      title: 'Monitor',
      icon: <Activity size={22} />,
      bg: '#e8f5f1',
      color: '#168c8c',
      desc: 'Continuously track vital chemical indicators (DO, pH, BOD) across all Ganga basin monitoring stations.',
    },
    {
      title: 'Forecast',
      icon: <Droplets size={22} />,
      bg: '#e6f0f7',
      color: '#2875a5',
      desc: 'Generate monthly parameter predictions and continuous WQI trajectories across the full forecast horizon.',
    },
    {
      title: 'Assess',
      icon: <ShieldCheck size={22} />,
      bg: '#fbf0e4',
      color: '#d38b35',
      desc: 'Evaluate river health and compliance against designated CPCB Class B reference standards.',
    },
    {
      title: 'Identify',
      icon: <Search size={22} />,
      bg: '#f2edf8',
      color: '#7b5294',
      desc: 'Detect vulnerable river stretches and classify potential pollution hotspots for targeted intervention.',
    },
    {
      title: 'Warn',
      icon: <AlertTriangle size={22} />,
      bg: '#fae8e5',
      color: '#cf5b4f',
      desc: 'Provide multi-tier early warnings to alert water and hydrology authorities before water quality deteriorates.',
    },
  ];

  return (
    <>
      <PageHeading
        eyebrow="System Overview / 10"
        title="About the Ganga Watch project"
        description="A specialized decision-support platform for hydrological analysis, forecasting, and ecological protection."
      />

      <div className="about-hero" style={{ marginBottom: '24px' }}>
        <div className="about-water">
          <Waves size={44} />
          <span>GANGA RIVER</span>
          <strong>Forecast the current.<br />Protect the next.</strong>
        </div>
        <div>
          <span className="eyebrow">Decision-Support System</span>
          <h2>Ganga River Intelligence</h2>
          <p>
            An advanced platform uniting historical observations, predictive modeling, and early warning analytics to protect India's most vital river ecosystem.
          </p>
          <Link className="button primary" to="/dashboard">
            Enter dashboard <ArrowRight size={16} />
          </Link>
        </div>
      </div>

      <section className="panel" style={{ marginBottom: '24px' }}>
        <div className="eyebrow" style={{ color: 'var(--teal)', marginBottom: '8px', fontWeight: '700', letterSpacing: '0.1em' }}>
          CORE MISSION
        </div>
        <h2 style={{ font: '800 24px Manrope', color: 'var(--deep)', margin: '0 0 14px' }}>Purpose</h2>
        <p style={{ fontSize: '15px', lineHeight: '1.75', color: '#2d4d50', margin: 0, maxWidth: '980px' }}>
          The Ganga River Water Quality Forecasting and Early Warning System is designed to support authorized Water and Hydrology Department personnel in monitoring river water quality, forecasting future conditions, identifying potential pollution hotspots, and receiving early warnings for locations that may require attention.
        </p>
      </section>

      <section className="panel" style={{ marginBottom: '24px' }}>
        <SectionHeader
          eyebrow="Strategic Pillars"
          title="Project Objectives"
        />
        <div className="about-objectives-grid">
          {objectives.map((obj) => (
            <div key={obj.title} className="objective-card">
              <div className="objective-icon" style={{ background: obj.bg, color: obj.color }}>
                {obj.icon}
              </div>
              <h3>{obj.title}</h3>
              <p>{obj.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
function AuthModal({ mode, onClose, onSuccess }) { const [form, setForm] = useState({ full_name: '', email: '', password: '' }); const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const signup = mode === 'signup'; const submit = async (event) => { event.preventDefault(); setBusy(true); setError(''); try { const response = await fetch(`${API}/auth/${signup ? 'signup' : 'login'}`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) }); const body = await response.json(); if (!response.ok) throw new Error(body.error || 'Authentication failed.'); onSuccess(body.user); } catch (requestError) { setError(requestError.message); } finally { setBusy(false); } }; return <div className="auth-backdrop" onClick={onClose}><div className="auth-modal" onClick={(event) => event.stopPropagation()}><button className="auth-close" onClick={onClose}><X size={18} /></button><div className="brand-mark"><Waves size={20} /></div><span className="eyebrow">Ganga Watch access</span><h2>{signup ? 'Create your account' : 'Welcome back'}</h2><p>{signup ? 'Save your place in the river intelligence workspace.' : 'Log in to continue to the dashboard.'}</p><form onSubmit={submit}>{signup && <label>Full name<input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} required /></label>}<label>Email address<input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required /></label><label>Password<input type="password" minLength="8" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required /></label>{error && <div className="auth-error"><AlertTriangle size={15} />{error}</div>}<button className="button primary auth-submit" disabled={busy}>{busy ? 'Connecting...' : signup ? 'Create account' : 'Log in'}</button></form><button className="auth-switch" onClick={() => onClose(signup ? 'login' : 'signup')}>{signup ? 'Already have an account? Log in' : 'New to Ganga Watch? Sign up'}</button></div></div> }
function Landing() { const navigate = useNavigate(); const [authMode, setAuthMode] = useState(''); const [user, setUser] = useState(null); const [destination, setDestination] = useState('/dashboard'); useEffect(() => { getApi('/auth/me').then((body) => setUser(body.user)).catch(() => setUser(null)); }, []); const openDestination = (path) => { setDestination(path); if (user) navigate(path); else setAuthMode('login'); }; const authSuccess = (signedInUser) => { setUser(signedInUser); setAuthMode(''); navigate(destination); }; return <div className="landing"><nav className="landing-nav"><Link to="/" className="landing-brand"><span className="brand-mark"><Waves size={21} /></span><strong>Ganga Watch</strong></Link><div><button className="landing-auth-link" onClick={() => setAuthMode('login')}><LogIn size={15} /> Login</button><button className="button primary" onClick={() => setAuthMode('signup')}><UserPlus size={15} /> Sign up</button></div></nav><div className="landing-hero"><div className="hero-copy"><h1>Read the river<br /><em>before it changes.</em></h1><p>Ganga River Water Quality Forecasting & Early Warning System. A transparent decision-support platform for predicting water quality, revealing potential hotspots, and bringing ecological context into focus.</p><div className="hero-actions"><button className="button primary" onClick={() => openDestination('/dashboard')}>Explore dashboard <ArrowRight size={16} /></button><button className="button light" onClick={() => openDestination('/river-map')}>Explore river <MapPin size={16} /></button></div><div className="hero-meta"><span><i className="live-dot" /> Existing model outputs</span><span>DO · pH · BOD</span><span>12-month horizon</span></div></div></div>{authMode && <AuthModal mode={authMode} onClose={(nextMode) => setAuthMode(nextMode || '')} onSuccess={authSuccess} />}</div> }

function RequireAuth({ children }) { const [status, setStatus] = useState('loading'); useEffect(() => { getApi('/auth/me').then((body) => setStatus(body.authenticated ? 'authenticated' : 'anonymous')).catch(() => setStatus('anonymous')); }, []); if (status === 'loading') return <Loading />; return status === 'authenticated' ? children : <Navigate to="/" replace />; }

function App() { return <Routes><Route path="/" element={<Landing />} /><Route element={<Layout />}><Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} /><Route path="/river-map" element={<RequireAuth><HistoricalRiverMap /></RequireAuth>} /><Route path="/forecast" element={<ForecastPage />} /><Route path="/wqi" element={<WQIPage />} /><Route path="/hotspots" element={<HotspotPage />} /><Route path="/compliance" element={<CompliancePage />} /><Route path="/biological" element={<BiologicalPage />} /><Route path="/state-analysis" element={<StatePage />} /><Route path="/early-warning" element={<EarlyWarning />} /><Route path="/live-prediction" element={<LivePrediction />} /><Route path="/notifications" element={<NotificationsPage />} /><Route path="/stations/:code" element={<StationDetails />} /><Route path="/about" element={<About />} /></Route></Routes> }
createRoot(document.getElementById('root')).render(<BrowserRouter><App /></BrowserRouter>);
