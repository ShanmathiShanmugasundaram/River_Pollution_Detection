import React, { useEffect, useState } from 'react';
import { 
  Users, UserCheck, AlertTriangle, UploadCloud, Plus, Edit2, 
  Trash2, ShieldCheck, UserX, CheckCircle, RefreshCw, X, 
  FileText, Bell, Send, CheckCheck, Info, Database, Folder, 
  FolderOpen, ChevronRight, ChevronDown, Calendar, Hash, Server, HardDrive
} from 'lucide-react';
import './admin.css';

const API = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:5000/api`;

async function fetchAdminApi(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.error || `Request failed with status ${response.status}`);
  }
  return body;
}

// ==============================================================================
// 1. ADMIN CONSOLE & USER MANAGEMENT PAGE (/admin)
// ==============================================================================
export function AdminConsolePage() {
  const [currentAdmin, setCurrentAdmin] = useState(null);
  const [summary, setSummary] = useState({ total_users: 0, active_users: 0, total_alerts: 0, recent_uploads: 0 });
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [feedback, setFeedback] = useState({ type: '', message: '' });
  const [busyAction, setBusyAction] = useState(false);

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'user', status: 'active' });

  const notify = (message, type = 'success') => {
    setFeedback({ type, message });
    setTimeout(() => setFeedback({ type: '', message: '' }), 5000);
  };

  const loadData = async () => {
    setSummaryLoading(true);
    setUsersLoading(true);
    try {
      const [sumData, usersData, authData] = await Promise.all([
        fetchAdminApi('/admin/summary'),
        fetchAdminApi('/admin/users'),
        fetchAdminApi('/auth/me')
      ]);
      setSummary(sumData);
      setUsers(usersData);
      if (authData.user) setCurrentAdmin(authData.user);
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setSummaryLoading(false);
      setUsersLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    if (form.password.length < 8) {
      notify('Password must be at least 8 characters long.', 'error');
      return;
    }
    setBusyAction(true);
    try {
      await fetchAdminApi('/admin/users', { method: 'POST', body: JSON.stringify(form) });
      notify('User created successfully.');
      setShowAddModal(false);
      loadData();
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setBusyAction(false);
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    setBusyAction(true);
    try {
      await fetchAdminApi(`/admin/users/${selectedUser.user_id}`, { method: 'PUT', body: JSON.stringify(form) });
      notify('User updated successfully.');
      setShowEditModal(false);
      loadData();
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setBusyAction(false);
    }
  };

  const handleToggleStatus = async (u) => {
    if (currentAdmin && currentAdmin.user_id === u.user_id) {
      notify('You cannot deactivate your own admin account.', 'error');
      return;
    }
    setBusyAction(true);
    const targetStatus = u.status === 'active' ? 'inactive' : 'active';
    try {
      await fetchAdminApi(`/admin/users/${u.user_id}/status`, { method: 'PUT', body: JSON.stringify({ status: targetStatus }) });
      notify(`User ${u.full_name} status updated to ${targetStatus}.`);
      loadData();
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setBusyAction(false);
    }
  };

  const executeDelete = async () => {
    if (!selectedUser) return;
    setBusyAction(true);
    try {
      await fetchAdminApi(`/admin/users/${selectedUser.user_id}`, { method: 'DELETE' });
      notify(`User ${selectedUser.full_name} deleted.`);
      setShowDeleteModal(false);
      setSelectedUser(null);
      loadData();
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setBusyAction(false);
    }
  };

  return (
    <div className="admin-container">
      <div className="page-heading">
        <div>
          <div className="eyebrow">Administration & Control</div>
          <h1>Admin Console & User Management</h1>
          <p>System overview, security roles, and user account management.</p>
        </div>
        <button className="button light" onClick={loadData} disabled={busyAction}>
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      {feedback.message && (
        <div className={`toast-message ${feedback.type}`}>
          <span>{feedback.message}</span>
          <button onClick={() => setFeedback({ type: '', message: '' })} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X size={14} /></button>
        </div>
      )}

      {/* Summary Cards */}
      <div className="stats-grid">
        <div className="stat-card blue">
          <div className="stat-top"><span>Total Users</span><Users size={16} /></div>
          <strong>{summaryLoading ? '—' : summary.total_users}</strong>
          <span className="stat-detail">Registered system accounts</span>
        </div>
        <div className="stat-card teal">
          <div className="stat-top"><span>Active Users</span><UserCheck size={16} /></div>
          <strong>{summaryLoading ? '—' : summary.active_users}</strong>
          <span className="stat-detail">Currently active credentials</span>
        </div>
        <div className="stat-card orange">
          <div className="stat-top"><span>Total Alerts</span><AlertTriangle size={16} /></div>
          <strong>{summaryLoading ? '—' : summary.total_alerts}</strong>
          <span className="stat-detail">Live early warnings</span>
        </div>
        <div className="stat-card ink">
          <div className="stat-top"><span>Recent Uploads</span><UploadCloud size={16} /></div>
          <strong>{summaryLoading ? '—' : summary.recent_uploads}</strong>
          <span className="stat-detail">Processed CSV datasets</span>
        </div>
      </div>

      {/* User Management Section */}
      <section className="panel">
        <div className="section-header" style={{ marginBottom: '16px' }}>
          <div>
            <div className="eyebrow">Directory</div>
            <h2>User Management</h2>
          </div>
          <button className="button primary" onClick={() => { setForm({ full_name: '', email: '', password: '', role: 'user', status: 'active' }); setShowAddModal(true); }}>
            <Plus size={15} /> Add User
          </button>
        </div>

        {usersLoading ? (
          <div className="loading"><span />Loading user directory...</div>
        ) : users.length === 0 ? (
          <p className="empty-state">No users registered.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Created At</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => {
                  const isSelf = currentAdmin && currentAdmin.user_id === u.user_id;
                  const isActive = (u.status || 'active').toLowerCase() === 'active';
                  return (
                    <tr key={u.user_id}>
                      <td><strong>{u.full_name}</strong>{isSelf && <small style={{ color: '#168c8c', marginLeft: '6px' }}>(You)</small>}</td>
                      <td>{u.email}</td>
                      <td><span className={`admin-badge-role ${u.role === 'admin' ? 'admin' : ''}`}>{u.role === 'admin' ? 'Admin' : 'User'}</span></td>
                      <td><span className={isActive ? 'admin-badge-active' : 'admin-badge-inactive'}>{isActive ? 'Active' : 'Inactive'}</span></td>
                      <td>{u.created_at ? new Date(u.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : '—'}</td>
                      <td>
                        <div className="admin-btn-group">
                          <button className="btn-action" title="Edit User" onClick={() => { setSelectedUser(u); setForm({ full_name: u.full_name, email: u.email, role: u.role, status: u.status || 'active', password: '' }); setShowEditModal(true); }}>
                            <Edit2 size={13} /> Edit
                          </button>
                          <button className={`btn-action ${isActive ? 'danger' : 'success'}`} disabled={isSelf || busyAction} onClick={() => handleToggleStatus(u)}>
                            {isActive ? <UserX size={13} /> : <UserCheck size={13} />}{isActive ? 'Deactivate' : 'Activate'}
                          </button>
                          <button className="btn-action danger" disabled={isSelf || busyAction} onClick={() => { setSelectedUser(u); setShowDeleteModal(true); }}>
                            <Trash2 size={13} /> Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="profile-modal-backdrop" onClick={() => setShowAddModal(false)}>
          <div className="profile-modal" onClick={(e) => e.stopPropagation()}>
            <button className="auth-close" onClick={() => setShowAddModal(false)}><X size={18} /></button>
            <span className="eyebrow">Account</span>
            <h2>Create New User</h2>
            <p>Assign credentials and role.</p>
            <form onSubmit={handleCreateUser}>
              <label>Full Name<input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required /></label>
              <label>Email Address<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></label>
              <label>Password <small>(min. 8 characters)</small><input type="password" minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></label>
              <label>Role
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #c9d8d4', marginTop: '4px' }}>
                  <option value="user">User (Standard Dashboard)</option>
                  <option value="admin">Admin (System Administrator)</option>
                </select>
              </label>
              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <button className="button primary" type="submit" disabled={busyAction}>{busyAction ? 'Creating...' : 'Create Account'}</button>
                <button className="button ghost" type="button" onClick={() => setShowAddModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="profile-modal-backdrop" onClick={() => setShowEditModal(false)}>
          <div className="profile-modal" onClick={(e) => e.stopPropagation()}>
            <button className="auth-close" onClick={() => setShowEditModal(false)}><X size={18} /></button>
            <span className="eyebrow">Account</span>
            <h2>Edit User</h2>
            <p>Update credentials for {selectedUser.full_name}.</p>
            <form onSubmit={handleUpdateUser}>
              <label>Full Name<input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required /></label>
              <label>Email Address<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></label>
              <label>Role
                <select value={form.role} disabled={currentAdmin && currentAdmin.user_id === selectedUser.user_id} onChange={(e) => setForm({ ...form, role: e.target.value })} style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #c9d8d4', marginTop: '4px' }}>
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </label>
              <label>Status
                <select value={form.status} disabled={currentAdmin && currentAdmin.user_id === selectedUser.user_id} onChange={(e) => setForm({ ...form, status: e.target.value })} style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #c9d8d4', marginTop: '4px' }}>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </label>
              <label>New Password <small>(leave blank to keep unchanged)</small><input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Optional" /></label>
              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <button className="button primary" type="submit" disabled={busyAction}>{busyAction ? 'Saving...' : 'Save Changes'}</button>
                <button className="button ghost" type="button" onClick={() => setShowEditModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete User Confirm Modal */}
      {showDeleteModal && selectedUser && (
        <div className="profile-modal-backdrop" onClick={() => setShowDeleteModal(false)}>
          <div className="profile-modal" onClick={(e) => e.stopPropagation()}>
            <button className="auth-close" onClick={() => setShowDeleteModal(false)}><X size={18} /></button>
            <span className="eyebrow" style={{ color: '#b52a2a' }}>Confirm Delete</span>
            <h2>Delete User Account?</h2>
            <p>Are you sure you want to delete user <strong>{selectedUser.full_name}</strong> ({selectedUser.email})? This action cannot be undone.</p>
            <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
              <button className="button primary" style={{ background: '#c0392b', borderColor: '#c0392b' }} onClick={executeDelete} disabled={busyAction}>{busyAction ? 'Deleting...' : 'Yes, Delete'}</button>
              <button className="button ghost" onClick={() => setShowDeleteModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==============================================================================
// 2. DATABASE MANAGEMENT PAGE (/admin/database)
// ==============================================================================
export function AdminDatabasePage() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [datasetToDelete, setDatasetToDelete] = useState(null);
  const [feedback, setFeedback] = useState({ type: '', message: '' });
  const [busy, setBusy] = useState(false);

  const notify = (message, type = 'success') => {
    setFeedback({ type, message });
    setTimeout(() => setFeedback({ type: '', message: '' }), 5000);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const sets = await fetchAdminApi('/admin/datasets');
      setDatasets(sets);
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const executeDeleteDataset = async () => {
    if (!datasetToDelete) return;
    setBusy(true);
    try {
      await fetchAdminApi(`/admin/datasets/${datasetToDelete.id}`, { method: 'DELETE' });
      notify(`Dataset ${datasetToDelete.file_name} removed from database.`);
      setDatasetToDelete(null);
      loadData();
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="admin-container">
      <div className="page-heading">
        <div>
          <div className="eyebrow">Catalog & Data Store</div>
          <h1>Database Management</h1>
          <p>Uploaded CSV datasets catalog and live prediction records.</p>
        </div>
        <button className="button light" onClick={loadData} disabled={busy}>
          <RefreshCw size={15} /> Refresh Datasets
        </button>
      </div>

      {feedback.message && (
        <div className={`toast-message ${feedback.type}`}>
          <span>{feedback.message}</span>
          <button onClick={() => setFeedback({ type: '', message: '' })} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X size={14} /></button>
        </div>
      )}

      {/* Table 2: Uploaded Datasets Management */}
      <section className="panel">
        <div className="section-header" style={{ marginBottom: '16px' }}>
          <div>
            <div className="eyebrow">Catalog</div>
            <h2>Uploaded Datasets Management</h2>
          </div>
          <span style={{ fontSize: '13px', color: '#68807b' }}>{datasets.length} Datasets Recorded</span>
        </div>

        {loading ? (
          <div className="loading"><span />Loading dataset catalog...</div>
        ) : datasets.length === 0 ? (
          <p className="empty-state">No uploaded datasets recorded in MySQL.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Dataset / File Name</th>
                  <th>Uploaded By</th>
                  <th>Upload Date</th>
                  <th>Record Count</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((ds) => (
                  <tr key={ds.id}>
                    <td>
                      <strong>{ds.file_name}</strong>
                      <small style={{ display: 'block', color: '#7a928c' }}>
                        Period: {ds.input_month} {ds.input_year} → {ds.forecast_month} {ds.forecast_year}
                      </small>
                    </td>
                    <td>{ds.uploaded_by || 'System'}</td>
                    <td>{ds.upload_date ? new Date(ds.upload_date).toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}</td>
                    <td><strong>{ds.record_count || ds.stations_processed || 0}</strong> records</td>
                    <td><span className="admin-badge-active">{ds.status || 'Completed'}</span></td>
                    <td>
                      <button className="btn-action danger" onClick={() => setDatasetToDelete(ds)} disabled={busy}>
                        <Trash2 size={13} /> Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Delete Dataset Confirmation Modal */}
      {datasetToDelete && (
        <div className="profile-modal-backdrop" onClick={() => setDatasetToDelete(null)}>
          <div className="profile-modal" onClick={(e) => e.stopPropagation()}>
            <button className="auth-close" onClick={() => setDatasetToDelete(null)}><X size={18} /></button>
            <span className="eyebrow" style={{ color: '#b52a2a' }}>Confirm Delete</span>
            <h2>Delete Dataset from Database?</h2>
            <p>Are you sure you want to delete <strong>{datasetToDelete.file_name}</strong>? All associated prediction records in MySQL will also be deleted.</p>
            <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
              <button className="button primary" style={{ background: '#c0392b', borderColor: '#c0392b' }} onClick={executeDeleteDataset} disabled={busy}>{busy ? 'Removing...' : 'Yes, Delete'}</button>
              <button className="button ghost" onClick={() => setDatasetToDelete(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==============================================================================
// 3. NOTIFICATIONS PAGE (/admin/notifications)
// ==============================================================================
export function AdminNotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all', 'unread', 'high_risk'
  const [feedback, setFeedback] = useState({ type: '', message: '' });

  const notify = (message, type = 'success') => {
    setFeedback({ type, message });
    setTimeout(() => setFeedback({ type: '', message: '' }), 5000);
  };

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await fetchAdminApi('/admin/notifications');
      setNotifications(data);
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadNotifications(); }, []);

  const handleMarkRead = async (notifId) => {
    try {
      await fetchAdminApi(`/admin/notifications/${notifId}/read`, { method: 'PUT' });
      setNotifications((prev) => prev.map((n) => (n.id === notifId || n.notification_id === notifId ? { ...n, is_read: 1 } : n)));
      notify('Notification marked as read.');
      window.dispatchEvent(new Event('notifications-updated'));
    } catch (err) {
      notify(err.message, 'error');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await fetchAdminApi('/admin/notifications/read-all', { method: 'PUT' });
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: 1 })));
      notify('All notifications marked as read.');
      window.dispatchEvent(new Event('notifications-updated'));
    } catch (err) {
      notify(err.message, 'error');
    }
  };

  const filteredList = notifications
    .filter((item) => item.notification_type !== 'USER_UPLOAD' && item.severity !== 'Warning' && !(item.message && item.message.includes('exceeds CPCB reference criteria')))
    .filter((item) => {
      if (filter === 'unread') return !item.is_read;
      if (filter === 'high_risk') return item.notification_type === 'HIGH_RISK_WARNING' || item.severity === 'High Risk';
      return true;
    });

  return (
    <div className="admin-container">
      <div className="page-heading">
        <div>
          <div className="eyebrow">Early Warning Stream</div>
          <h1>Notifications</h1>
          <p>Real-time water quality prediction alerts and administrative notifications.</p>
        </div>
        <div className="admin-actions">
          <button className="button light" onClick={loadNotifications}>
            <RefreshCw size={15} /> Refresh
          </button>
        </div>
      </div>

      {feedback.message && (
        <div className={`toast-message ${feedback.type}`}>
          <span>{feedback.message}</span>
          <button onClick={() => setFeedback({ type: '', message: '' })} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X size={14} /></button>
        </div>
      )}

      {/* 3 TABS ONLY: All, Unread, High-Risk Forecasts */}
      <div className="admin-tabs">
        <button className={`admin-tab-btn ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>
          All ({notifications.filter((item) => item.notification_type !== 'USER_UPLOAD' && item.severity !== 'Warning' && !(item.message && item.message.includes('exceeds CPCB reference criteria'))).length})
        </button>
        <button className={`admin-tab-btn ${filter === 'unread' ? 'active' : ''}`} onClick={() => setFilter('unread')}>
          Unread ({notifications.filter((item) => item.notification_type !== 'USER_UPLOAD' && item.severity !== 'Warning' && !(item.message && item.message.includes('exceeds CPCB reference criteria')) && !item.is_read).length})
        </button>
        <button className={`admin-tab-btn ${filter === 'high_risk' ? 'active' : ''}`} onClick={() => setFilter('high_risk')}>
          🔴 High-Risk Forecasts ({notifications.filter((n) => (n.notification_type === 'HIGH_RISK_WARNING' || n.severity === 'High Risk') && n.severity !== 'Warning' && n.notification_type !== 'USER_UPLOAD').length})
        </button>
      </div>

      <section className="panel">
        {loading ? (
          <div className="loading"><span />Loading notifications...</div>
        ) : filteredList.length === 0 ? (
          <p className="empty-state">No notifications matching "{filter}".</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Title & Notification Message</th>
                  <th>Station</th>
                  <th>Severity</th>
                  <th>Date / Time</th>
                </tr>
              </thead>
              <tbody>
                {filteredList.map((n) => {
                  const notifId = n.id || n.notification_id;
                  const isHighRisk = n.notification_type === 'HIGH_RISK_WARNING' || n.severity === 'High Risk';
                  return (
                    <tr key={notifId}>
                      <td>
                        {isHighRisk ? (
                          <span className="notification-type-tag type-high-risk">🔴 Forecast Alert</span>
                        ) : (
                          <span className="notification-type-tag type-system-msg">ℹ️ System Notice</span>
                        )}
                      </td>
                      <td style={{ maxWidth: '420px' }}>
                        <strong style={{ display: 'block', color: '#163832', marginBottom: '4px' }}>
                          {n.title || (isHighRisk ? 'High-Risk Water Quality Prediction' : 'Water Quality Notice')}
                        </strong>
                        <p style={{ margin: 0, fontSize: '13px', color: '#445b56', lineHeight: '1.4' }}>
                          {n.message}
                        </p>
                      </td>
                      <td>
                        {n.station_name ? (
                          <>
                            <strong>{n.station_name}</strong>
                            <small style={{ display: 'block', color: '#7a928c' }}>{n.station_code} · {n.state}</small>
                          </>
                        ) : '—'}
                      </td>
                      <td>
                        <span className={`badge ${n.severity === 'High Risk' ? 'high' : 'low'}`}>
                          {n.severity || 'Normal'}
                        </span>
                      </td>
                      <td>
                        <small style={{ color: '#68807b', whiteSpace: 'nowrap' }}>
                          {n.created_at ? new Date(n.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                        </small>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

// ==============================================================================
// 4. USER FOLDERS PAGE (/admin/user-folders)
// ==============================================================================
export function AdminUserFoldersPage() {
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedFolder, setExpandedFolder] = useState(null);
  const [feedback, setFeedback] = useState({ type: '', message: '' });

  const notify = (message, type = 'success') => {
    setFeedback({ type, message });
    setTimeout(() => setFeedback({ type: '', message: '' }), 5000);
  };

  const loadFolders = async () => {
    setLoading(true);
    try {
      const data = await fetchAdminApi('/admin/user-folders');
      setFolders(data);
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadFolders(); }, []);

  const toggleExpand = (userId) => {
    setExpandedFolder(expandedFolder === userId ? null : userId);
  };

  return (
    <div className="admin-container">
      <div className="page-heading">
        <div>
          <div className="eyebrow">Workspace Repository</div>
          <h1>User Folders</h1>
          <p>User-specific directory cataloging dataset uploads, file volumes, and records per user.</p>
        </div>
        <button className="button light" onClick={loadFolders}>
          <RefreshCw size={15} /> Refresh Folders
        </button>
      </div>

      {feedback.message && (
        <div className={`toast-message ${feedback.type}`}>
          <span>{feedback.message}</span>
          <button onClick={() => setFeedback({ type: '', message: '' })} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X size={14} /></button>
        </div>
      )}

      {loading ? (
        <div className="loading"><span />Loading user directories...</div>
      ) : folders.length === 0 ? (
        <p className="empty-state">No user directories found.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {folders.map((uf) => {
            const isExpanded = expandedFolder === uf.user_id;
            return (
              <section key={uf.user_id} className="panel" style={{ padding: '0', overflow: 'hidden' }}>
                <div 
                  onClick={() => toggleExpand(uf.user_id)}
                  style={{
                    padding: '16px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    background: isExpanded ? '#edf5f2' : '#ffffff',
                    borderBottom: isExpanded ? '1px solid #dce8e4' : 'none',
                    transition: 'background 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {isExpanded ? <FolderOpen size={22} color="#168c8c" /> : <Folder size={22} color="#168c8c" />}
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <strong style={{ fontSize: '15px', color: '#163832' }}>📁 {uf.folder_name}</strong>
                        <span className={`admin-badge-role ${uf.role === 'admin' ? 'admin' : ''}`}>{uf.role}</span>
                      </div>
                      <small style={{ color: '#68807b', display: 'block', marginTop: '2px' }}>
                        Owner: {uf.full_name} ({uf.email})
                      </small>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                    <div style={{ textAlign: 'right' }}>
                      <strong style={{ fontSize: '14px', color: '#163832' }}>{uf.file_count} {uf.file_count === 1 ? 'file' : 'files'}</strong>
                      <small style={{ display: 'block', color: '#7a928c' }}>{uf.total_records.toLocaleString()} total records</small>
                    </div>
                    {isExpanded ? <ChevronDown size={18} color="#68807b" /> : <ChevronRight size={18} color="#68807b" />}
                  </div>
                </div>

                {/* Expanded File List */}
                {isExpanded && (
                  <div style={{ padding: '16px 20px', background: '#fafcfb' }}>
                    {uf.files.length === 0 ? (
                      <p style={{ margin: 0, fontSize: '13px', color: '#889f9a', fontStyle: 'italic' }}>
                        This user folder contains no uploaded CSV datasets yet.
                      </p>
                    ) : (
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>File Name</th>
                              <th>Upload Timestamp</th>
                              <th>Records</th>
                              <th>Average WQI</th>
                              <th>Forecast Horizon</th>
                              <th>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {uf.files.map((file) => (
                              <tr key={file.upload_id}>
                                <td>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <FileText size={14} color="#168c8c" />
                                    <strong>{file.filename}</strong>
                                  </div>
                                </td>
                                <td>
                                  <small style={{ color: '#68807b' }}>
                                    {file.created_at ? new Date(file.created_at).toLocaleString() : '—'}
                                  </small>
                                </td>
                                <td><strong>{file.record_count || file.stations_processed || 0}</strong></td>
                                <td>{file.average_wqi ? `${file.average_wqi} / 100` : '—'}</td>
                                <td>{file.input_month ? `${file.input_month} ${file.input_year} → ${file.forecast_month} ${file.forecast_year}` : '—'}</td>
                                <td><span className="admin-badge-active">{file.status || 'Completed'}</span></td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ==============================================================================
// 5. SYSTEM MESSAGE PAGE (/admin/system-messages)
// ==============================================================================
export function AdminSystemMessagesPage() {
  const [form, setForm] = useState({ title: 'System Notice', message: '', severity: 'Info' });
  const [feedback, setFeedback] = useState({ type: '', message: '' });
  const [busy, setBusy] = useState(false);

  const notify = (message, type = 'success') => {
    setFeedback({ type, message });
    setTimeout(() => setFeedback({ type: '', message: '' }), 5000);
  };

  const handleBroadcast = async (e) => {
    e.preventDefault();
    if (!form.message.trim()) {
      notify('Message content cannot be empty.', 'error');
      return;
    }
    setBusy(true);
    try {
      await fetchAdminApi('/admin/notifications/system', { method: 'POST', body: JSON.stringify(form) });
      notify('System announcement broadcasted successfully.');
      setForm({ title: 'System Notice', message: '', severity: 'Info' });
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="admin-container">
      <div className="page-heading">
        <div>
          <div className="eyebrow">Administrative Notices</div>
          <h1>System Messages</h1>
          <p>Compose, publish, and manage system-wide announcements and operational notices.</p>
        </div>
      </div>

      {feedback.message && (
        <div className={`toast-message ${feedback.type}`}>
          <span>{feedback.message}</span>
          <button onClick={() => setFeedback({ type: '', message: '' })} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X size={14} /></button>
        </div>
      )}

      {/* Broadcast Form Panel */}
      <section className="panel" style={{ maxWidth: '820px' }}>
        <div className="section-header" style={{ marginBottom: '20px' }}>
          <div>
            <div className="eyebrow">Broadcast Console</div>
            <h2>Publish New System Message</h2>
          </div>
        </div>

        <form onSubmit={handleBroadcast} className="system-message-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="sys-title">Announcement Title</label>
              <input 
                id="sys-title"
                type="text" 
                value={form.title} 
                onChange={(e) => setForm({ ...form, title: e.target.value })} 
                placeholder="System Notice" 
                required 
              />
            </div>
            <div className="form-group">
              <label htmlFor="sys-severity">Severity Level</label>
              <select 
                id="sys-severity"
                value={form.severity} 
                onChange={(e) => setForm({ ...form, severity: e.target.value })}
              >
                <option value="Info">Information / Notice</option>
                <option value="Warning">Warning / Alert</option>
                <option value="Normal">General Notice</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="sys-message">Message Content</label>
            <textarea 
              id="sys-message"
              rows={5} 
              value={form.message} 
              onChange={(e) => setForm({ ...form, message: e.target.value })} 
              placeholder="Enter message details for authorities and researchers..."
              required 
            />
          </div>

          <div style={{ marginTop: '4px' }}>
            <button className="button primary" type="submit" disabled={busy}>
              <Send size={15} /> {busy ? 'Publishing...' : 'Publish System Announcement'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default AdminConsolePage;
