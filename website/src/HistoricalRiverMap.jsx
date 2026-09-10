import React, { useEffect, useState } from 'react';
import { ArrowRight, MapPin, Search } from 'lucide-react';
import { Link } from 'react-router-dom';

const API = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:5000/api`;
const YEARS = Array.from({ length: 13 }, (_, index) => 2014 + index);

export default function HistoricalRiverMap() {
  const [year, setYear] = useState('2025');
  const [state, setState] = useState('');
  const [search, setSearch] = useState('');
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const query = new URLSearchParams({ year });
    if (state) query.set('state', state);
    fetch(`${API}/stations?${query}`, { credentials: 'include' })
      .then((response) => {
        if (!response.ok) throw new Error('Failed to load stations');
        return response.json();
      })
      .then((data) => setStations(Array.isArray(data) ? data : []))
      .catch((err) => {
        console.error('Failed to load stations:', err);
        setStations([]);
      })
      .finally(() => setLoading(false));
  }, [year, state]);


  const filtered = stations.filter((station) =>
    `${station.station_name} ${station.station_code}`.toLowerCase().includes(search.toLowerCase())
  );
  const states = ['Uttarakhand', 'Uttar Pradesh', 'Bihar', 'Jharkhand', 'West Bengal'];

  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">Historical monitoring network</div>
          <h1>Ganga River map</h1>
          <p>Focused Ganga River flow corridor with station-wise project WQI calculated from the selected historical year.</p>
        </div>
        <Link className="button ghost" to="/hotspots">
          Open hotspot table <ArrowRight size={16} />
        </Link>
      </div>
      <div className="filter-bar historical-map-filters">
        <label>
          Year
          <select value={year} onChange={(event) => setYear(event.target.value)}>
            {YEARS.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          State
          <select value={state} onChange={(event) => setState(event.target.value)}>
            <option value="">All states</option>
            {states.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <div className="search-box">
          <Search size={16} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search station or code"
          />
        </div>
      </div>
      <div className="map-layout historical-map-layout">
        <section className="river-map panel">
          <div className="map-top">
            <div>
              <span className="eyebrow">Ganga River flow map</span>
              <h2>Focused Ganga corridor · {year}</h2>
            </div>
            <span className="map-note">
              <MapPin size={14} /> Station coordinates unavailable
            </span>
          </div>
          <div className="real-river-map">
            <iframe
              title="Focused Ganga River corridor map"
              src="https://www.openstreetmap.org/export/embed.html?bbox=77.8%2C25.0%2C89.8%2C31.5&amp;layer=mapnik"
              loading="lazy"
            />
            <div className="map-disclaimer">
              Focused Ganga River corridor from Uttarakhand through West Bengal. The supplied project CSV files do not include latitude/longitude, so station markers are not fabricated.
            </div>
          </div>
        </section>
        <section className="panel station-list-panel">
          <div className="section-header">
            <div>
              <div className="eyebrow">{filtered.length} stations</div>
              <h2>Predicted WQI by year</h2>
            </div>
            <span className="badge historical">
              {year === '2026' ? '2026 forecast' : `${year} observations`}
            </span>
          </div>
          <div className="station-cards">
            {loading ? (
              <div className="loading">Loading station WQI...</div>
            ) : filtered.length === 0 ? (
              <div className="empty-state">No stations found for this selection.</div>
            ) : (
              filtered.map((station) => (
                <Link
                  className="station-card"
                  key={station.station_code}
                  to={`/stations/${station.station_code}`}
                >
                  <div>
                    <span className="station-code">{station.station_code}</span>
                    <h3>{station.station_name}</h3>
                    <span className="muted">{station.state}</span>
                  </div>
                  <div className="station-card-right">
                    <strong>{Number(station.average_wqi).toFixed(1)}</strong>
                    <span>project WQI</span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </section>
      </div>
    </>
  );
}

