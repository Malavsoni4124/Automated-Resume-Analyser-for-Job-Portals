import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  BrowserRouter as Router, Routes, Route, NavLink,
  useParams, useNavigate, Navigate
} from 'react-router-dom';
import {
  Briefcase, LayoutDashboard, Upload, User, ChevronRight, X,
  LogIn, Plus, Trash2, FileText, Cpu, Zap, Database,
  CheckCircle, AlertCircle, Info, ArrowRight, Users, BarChart2,
  Layers, Brain, HelpCircle, Download, Search, Filter,
  Star, TrendingUp, Clock, Award, XCircle, Target,
  Mail, Phone, MapPin, Link2, GraduationCap, Building2,
  Calendar, ChevronDown, MoreHorizontal, StickyNote,
  PieChart, Activity, Lightbulb, BookOpen, Code2, Server,
  Sparkles, Edit3, Columns, List, Scale, Copy, Check,
  MessageSquare, Wand2, ArrowUpRight, Send, Settings
} from 'lucide-react';
import './index.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ─────────────────────────────────────────
//  UTILS & HELPERS
// ─────────────────────────────────────────

async function api(path, token, opts = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...opts,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...opts.headers,
    },
  });
  if (res.status === 401 && token) {
    localStorage.removeItem('ats_token');
    window.dispatchEvent(new Event('ats:unauthorized'));
  }
  return res;
}

function scoreColor(v) {
  if (v >= 0.75) return 'var(--green)';
  if (v >= 0.50) return 'var(--amber)';
  return 'var(--red)';
}

function scoreBadge(v) {
  if (v >= 0.75) return 'badge-green';
  if (v >= 0.50) return 'badge-amber';
  return 'badge-red';
}

function progressCls(v) {
  if (v >= 0.75) return 'progress-high';
  if (v >= 0.50) return 'progress-med';
  return 'progress-low';
}

const STATUS_CONFIG = {
  new:         { label: 'New',         cls: 'badge-muted',  icon: <Clock size={11} /> },
  shortlisted: { label: 'Shortlisted', cls: 'badge-accent', icon: <CheckCircle size={11} /> },
  hired:       { label: 'Hired',       cls: 'badge-green',  icon: <Award size={11} /> },
  rejected:    { label: 'Rejected',    cls: 'badge-red',    icon: <XCircle size={11} /> },
};

// ─────────────────────────────────────────
//  TOAST PROVIDER
// ─────────────────────────────────────────

const ToastCtx = React.createContext(null);

function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const add = useCallback((msg, type = 'info', dur = 3500) => {
    const id = Date.now() + Math.random();
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), dur);
  }, []);
  const icn = { success: <CheckCircle size={14} />, error: <AlertCircle size={14} />, info: <Info size={14} /> };
  const col = { success: 'var(--green)', error: 'var(--red)', info: 'var(--blue)' };
  return (
    <ToastCtx.Provider value={add}>
      {children}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type}`}>
            <span style={{ color: col[t.type], flexShrink: 0 }}>{icn[t.type]}</span>
            <span>{t.msg}</span>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
function useToast() { return React.useContext(ToastCtx); }

// ─────────────────────────────────────────
//  MODAL
// ─────────────────────────────────────────

function Modal({ title, onClose, width = 540, children }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" style={{ maxWidth: width, width: '90%' }} onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, letterSpacing: '-0.02em' }}>{title}</h3>
          <button className="btn btn-ghost btn-sm" onClick={onClose} style={{ padding: '4px 8px', height: 'auto' }}>
            <X size={16} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────
//  PROGRESS BAR
// ─────────────────────────────────────────

function ProgressBar({ value, className = 'progress-accent', delay = 0, height = 5 }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth(Math.round((value || 0) * 100)), 80 + delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return (
    <div className="progress-track" style={{ height }}>
      <div className={`progress-fill ${className}`} style={{ width: `${width}%` }} />
    </div>
  );
}

// ─────────────────────────────────────────
//  LOGIN
// ─────────────────────────────────────────

function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [pw, setPw] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async e => {
    e.preventDefault();
    setErr(''); setLoading(true);
    try {
      const form = new URLSearchParams();
      form.append('username', email); form.append('password', pw);
      const res = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString(),
      });
      if (!res.ok) throw new Error('Invalid email or password.');
      const data = await res.json();
      onLogin(data.access_token, data.role);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-base)', alignItems: 'center', justifyContent: 'center',
      backgroundImage: 'radial-gradient(ellipse at 20% 50%, rgba(200,255,71,0.05) 0%, transparent 55%), radial-gradient(ellipse at 80% 20%, rgba(59,130,246,0.04) 0%, transparent 55%)' }}>
      <div style={{ width: '100%', maxWidth: 400, padding: 'var(--space-6)' }}>
        <div style={{ marginBottom: 'var(--space-10)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-6)' }}>
            <div style={{ width: 34, height: 34, background: 'var(--accent)', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Briefcase size={18} color="#09090B" strokeWidth={2.5} />
            </div>
            <span style={{ fontWeight: 700, fontSize: 17, letterSpacing: '-0.03em' }}>Aero ATS</span>
          </div>
          <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.04em', marginBottom: 8, lineHeight: 1.2 }}>Welcome back</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, lineHeight: 1.6 }}>Sign in to your enterprise recruiter workspace.</p>
        </div>

        {err && (
          <div style={{ background: 'var(--red-dim)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 'var(--radius-md)', padding: '10px 14px', marginBottom: 'var(--space-5)', fontSize: 13, color: 'var(--red)', display: 'flex', gap: 8, alignItems: 'center' }}>
            <AlertCircle size={13} /> {err}
          </div>
        )}

        <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div className="form-group"><label className="form-label">Email</label>
            <input className="input" type="email" placeholder="admin@aerocorp.com" value={email} onChange={e => setEmail(e.target.value)} required /></div>
          <div className="form-group"><label className="form-label">Password</label>
            <input className="input" type="password" placeholder="••••••••" value={pw} onChange={e => setPw(e.target.value)} required /></div>
          <button type="submit" className="btn btn-accent btn-lg" disabled={loading}
            style={{ width: '100%', justifyContent: 'center', marginTop: 'var(--space-2)' }}>
            {loading ? <><div className="spinner" style={{ borderTopColor: '#09090B' }} /> Signing in…</> : <><LogIn size={15} /> Sign in</>}
          </button>
        </form>
        <p style={{ marginTop: 'var(--space-6)', textAlign: 'center', fontSize: 12.5, color: 'var(--text-muted)' }}>
          Demo — Email: <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>admin@aerocorp.com</span> &nbsp;·&nbsp; Password: <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>password123</span>
        </p>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────
//  SIDEBAR
// ─────────────────────────────────────────

function Sidebar({ onLogout, role }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon"><Briefcase size={16} color="#09090B" strokeWidth={2.5} /></div>
        <span className="sidebar-logo-text">Aero ATS</span>
      </div>
      <span className="sidebar-section-label">Workspace</span>
      <NavLink to="/" end className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
        <LayoutDashboard size={15} className="nav-icon" /> Jobs
      </NavLink>
      <NavLink to="/analytics" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
        <BarChart2 size={15} className="nav-icon" /> Analytics
      </NavLink>
      <NavLink to="/talent-pool" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
        <Users size={15} className="nav-icon" /> Talent Pool
      </NavLink>
      <span className="sidebar-section-label">Resources</span>
      <NavLink to="/settings" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
        <Settings size={15} className="nav-icon" /> Settings
      </NavLink>
      <NavLink to="/about" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
        <HelpCircle size={15} className="nav-icon" /> How It Works
      </NavLink>
      <div className="sidebar-spacer" />
      <div className="sidebar-footer">
        {role === 'admin' && (
          <button className="nav-item" style={{ marginBottom: 4, width: '100%', textAlign: 'left' }} onClick={() => window.alert('Enterprise User Management module coming in v2.0!')}>
            <User size={15} className="nav-icon" /> Manage Users
          </button>
        )}
        <button className="nav-item" onClick={onLogout} style={{ width: '100%', color: 'var(--text-muted)' }}>
          <LogIn size={15} style={{ transform: 'rotate(180deg)' }} /> Sign out
        </button>
      </div>
    </aside>
  );
}

// ─────────────────────────────────────────
//  DASHBOARD
// ─────────────────────────────────────────

function Dashboard({ token }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();
  const toast = useToast();

  const fetchJobs = useCallback(async () => {
    try {
      const res = await api('/jobs/', token);
      if (res.ok) setJobs(await res.json());
    } catch { toast('Failed to load jobs', 'error'); }
    finally { setLoading(false); }
  }, [token, toast]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const handleDeleteJob = async (e, jobId, jobTitle) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete "${jobTitle}"?`)) return;
    try {
      const res = await api(`/jobs/${jobId}`, token, { method: 'DELETE' });
      if (res.ok || res.status === 204) {
        setJobs(prev => prev.filter(j => j.id !== jobId));
        toast('Job deleted', 'info');
      }
    } catch { toast('Failed to delete job', 'error'); }
  };

  const filtered = jobs.filter(j => j.title.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="main-content">
      {/* Metrics Banner */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-4)', marginBottom: 'var(--space-8)' }}>
        <div className="card" style={{ padding: 'var(--space-5)' }}>
          <div className="flex items-center justify-between" style={{ color: 'var(--text-muted)', marginBottom: 6 }}>
            <span style={{ fontSize: 12.5, fontWeight: 600 }}>Active Jobs</span>
            <Briefcase size={16} style={{ color: 'var(--accent)' }} />
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.04em' }}>{jobs.length}</div>
          <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 4 }}>Positions currently hiring</div>
        </div>
        <div className="card" style={{ padding: 'var(--space-5)' }}>
          <div className="flex items-center justify-between" style={{ color: 'var(--text-muted)', marginBottom: 6 }}>
            <span style={{ fontSize: 12.5, fontWeight: 600 }}>Total Pipeline</span>
            <Users size={16} style={{ color: 'var(--blue)' }} />
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.04em' }}>11</div>
          <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 4 }}>Applicants processed by AI</div>
        </div>
        <div className="card" style={{ padding: 'var(--space-5)' }}>
          <div className="flex items-center justify-between" style={{ color: 'var(--text-muted)', marginBottom: 6 }}>
            <span style={{ fontSize: 12.5, fontWeight: 600 }}>Average Match Rate</span>
            <Brain size={16} style={{ color: 'var(--green)' }} />
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.04em', color: 'var(--green)' }}>78.4%</div>
          <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 4 }}>High-precision semantic fit</div>
        </div>
        <div className="card" style={{ padding: 'var(--space-5)' }}>
          <div className="flex items-center justify-between" style={{ color: 'var(--text-muted)', marginBottom: 6 }}>
            <span style={{ fontSize: 12.5, fontWeight: 600 }}>Top Talent</span>
            <Star size={16} style={{ color: 'var(--amber)' }} />
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.04em', color: 'var(--amber)' }}>4</div>
          <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 4 }}>Shortlisted candidates</div>
        </div>
      </div>

      {/* Header bar */}
      <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-6)' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.03em' }}>Open Positions</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
            {loading ? 'Loading jobs…' : `${jobs.length} job posting${jobs.length !== 1 ? 's' : ''} available`}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
            <input className="input" placeholder="Search positions…" value={search} onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: 32, width: 240, height: 36 }} />
          </div>
          <button className="btn btn-accent" onClick={() => setShowModal(true)}><Plus size={15} /> Create Job</button>
        </div>
      </div>

      {loading ? (
        <div className="job-grid">
          {[1,2,3,4,5,6].map(i => <div key={i} className="skeleton" style={{ height: 160, borderRadius: 'var(--radius-lg)' }} />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="card">
          <div className="empty-state" style={{ padding: 'var(--space-12)' }}>
            <div className="empty-state-icon"><FileText size={26} /></div>
            <p style={{ fontWeight: 600, fontSize: 16 }}>{search ? 'No jobs match your search' : 'No jobs found'}</p>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
              {search ? 'Try adjusting your search query.' : 'Create your first job posting to start evaluating applicants.'}
            </p>
            {!search && <button className="btn btn-accent btn-sm" style={{ marginTop: 'var(--space-4)' }} onClick={() => setShowModal(true)}><Plus size={13} /> Create Job</button>}
          </div>
        </div>
      ) : (
        <div className="job-grid">
          {filtered.map((job, i) => {
            const skills = job.parsed_json?.skills || job.parsed_json?.required_skills || [];
            const minExp = job.parsed_json?.min_experience_years || job.parsed_json?.min_years_experience || 0;
            const degree = job.parsed_json?.degree_required || job.parsed_json?.required_degree;

            return (
              <div key={job.id} className="card card-clickable animate-slide-in"
                style={{ padding: 'var(--space-5)', animationDelay: `${i * 0.03}s`, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
                onClick={() => navigate(`/jobs/${job.id}`)}>
                <div>
                  <div className="flex items-start justify-between gap-3" style={{ marginBottom: 'var(--space-3)' }}>
                    <div className="flex items-center gap-3">
                      <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', background: 'var(--accent-dim)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)', flexShrink: 0 }}>
                        <Briefcase size={18} />
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <p style={{ fontWeight: 700, fontSize: 15, letterSpacing: '-0.01em', lineHeight: 1.3 }} className="truncate">{job.title}</p>
                        <p style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 2 }}>Posting #{job.id}</p>
                      </div>
                    </div>
                    <button className="btn btn-ghost btn-xs" onClick={(e) => handleDeleteJob(e, job.id, job.title)} style={{ color: 'var(--text-muted)', padding: '2px 5px' }} title="Delete Job">
                      <Trash2 size={13} />
                    </button>
                  </div>

                  <div className="flex items-center gap-2" style={{ marginBottom: 'var(--space-4)', flexWrap: 'wrap' }}>
                    {minExp > 0 && <span className="badge badge-blue" style={{ fontSize: 11 }}><Clock size={10} /> {minExp}+ yrs exp</span>}
                    {degree && <span className="badge badge-muted" style={{ fontSize: 11 }}><GraduationCap size={10} /> {degree}</span>}
                  </div>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 'var(--space-4)' }}>
                    {skills.slice(0, 5).map(s => <span key={s} className="skill-tag">{s}</span>)}
                    {skills.length > 5 && <span className="skill-tag">+{skills.length - 5}</span>}
                  </div>
                </div>

                <div className="flex items-center justify-between" style={{ paddingTop: 'var(--space-3)', borderTop: '1px solid var(--border-subtle)', marginTop: 'var(--space-2)' }}>
                  <span style={{ fontSize: 12, color: 'var(--accent)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                    View Pipeline <ArrowRight size={12} />
                  </span>
                  <span style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>AI Parsed</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showModal && (
        <NewJobModal token={token} onClose={() => setShowModal(false)}
          onCreated={() => { fetchJobs(); setShowModal(false); toast('Job created!', 'success'); }} />
      )}
    </div>
  );
}

// ─────────────────────────────────────────
//  NEW & EDIT JOB MODALS
// ─────────────────────────────────────────

const SUGGESTED_SKILLS = [
  'Python', 'React', 'TypeScript', 'Node.js', 'FastAPI', 'Docker',
  'Kubernetes', 'AWS', 'SQL', 'PyTorch', 'Machine Learning', 'GraphQL',
  'Git', 'CI/CD', 'REST API', 'PostgreSQL'
];

function NewJobModal({ token, onClose, onCreated }) {
  const [title, setTitle] = useState('');
  const [raw, setRaw] = useState('');
  const [skills, setSkills] = useState([]);
  const [skillInput, setSkillInput] = useState('');
  const [minExp, setMinExp] = useState(3);
  const [degree, setDegree] = useState("Bachelor's");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  const addSkill = (s) => {
    const clean = s.trim().replace(/,/g, '');
    if (clean && !skills.includes(clean)) {
      setSkills(prev => [...prev, clean]);
    }
    setSkillInput('');
  };

  const removeSkill = (s) => {
    setSkills(prev => prev.filter(x => x !== s));
  };

  const handleSkillKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addSkill(skillInput);
    }
  };

  const autoExtractSkills = () => {
    if (!raw.trim()) return;
    const keywords = ['Python', 'Java', 'C++', 'JavaScript', 'TypeScript', 'React', 'Vue', 'Angular', 'Node.js', 'Express', 'Django', 'Flask', 'FastAPI', 'Spring', 'Go', 'Rust', 'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Docker', 'Kubernetes', 'AWS', 'GCP', 'Azure', 'PyTorch', 'TensorFlow', 'Scikit-learn', 'Pandas', 'Spark', 'Kafka', 'GraphQL', 'REST API', 'Git', 'CI/CD', 'Linux', 'Agile', 'HTML', 'CSS'];
    const found = [];
    const textLower = raw.toLowerCase();
    keywords.forEach(kw => {
      if (textLower.includes(kw.toLowerCase()) && !skills.includes(kw)) {
        found.push(kw);
      }
    });
    if (found.length > 0) {
      setSkills(prev => [...new Set([...prev, ...found])]);
    }
  };

  const submit = async e => {
    e.preventDefault();
    if (!title.trim()) { setErr('Job title is required.'); return; }
    if (skills.length === 0 && !raw.trim()) { setErr('Please add at least one skill or paste a job description.'); return; }
    setLoading(true); setErr('');
    try {
      const res = await api('/jobs/', token, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          raw_text: raw.trim(),
          skills,
          min_experience_years: parseFloat(minExp) || 0,
          degree_required: degree
        }),
      });
      if (!res.ok) throw new Error('Failed to create job');
      onCreated();
    } catch (e) { setErr(e.message); setLoading(false); }
  };

  return (
    <Modal title="Create new job posting" onClose={onClose}>
      {err && <div style={{ background: 'var(--red-dim)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius-md)', padding: '8px 12px', marginBottom: 'var(--space-4)', fontSize: 13, color: 'var(--red)' }}>{err}</div>}
      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <div className="form-group">
          <label className="form-label">Job Title <span style={{ color: 'var(--accent)' }}>*</span></label>
          <input className="input" placeholder="e.g. Senior Full-Stack Engineer" value={title} onChange={e => setTitle(e.target.value)} required />
        </div>

        <div className="form-group">
          <div className="flex items-center justify-between" style={{ marginBottom: 6 }}>
            <label className="form-label" style={{ marginBottom: 0 }}>Required Skills ({skills.length})</label>
            {raw.trim() && (
              <button type="button" className="btn btn-ghost btn-sm" onClick={autoExtractSkills} style={{ fontSize: 11, padding: '2px 8px', height: 'auto', color: 'var(--accent)' }}>
                <Sparkles size={11} /> Auto-extract from text
              </button>
            )}
          </div>
          
          <div className="input" style={{ minHeight: 48, padding: '6px 10px', display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center', cursor: 'text' }} onClick={() => document.getElementById('new-skill-input')?.focus()}>
            {skills.map(s => (
              <span key={s} className="skill-tag" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 8px', fontSize: 12, background: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>
                {s}
                <X size={12} style={{ cursor: 'pointer', opacity: 0.7 }} onClick={(e) => { e.stopPropagation(); removeSkill(s); }} />
              </span>
            ))}
            <input
              id="new-skill-input"
              type="text"
              placeholder={skills.length === 0 ? "Type skill & press Enter or comma..." : "Add skill..."}
              value={skillInput}
              onChange={e => {
                if (e.target.value.includes(',')) addSkill(e.target.value);
                else setSkillInput(e.target.value);
              }}
              onKeyDown={handleSkillKeyDown}
              onBlur={() => { if (skillInput.trim()) addSkill(skillInput); }}
              style={{ border: 'none', outline: 'none', background: 'transparent', color: 'var(--text-primary)', fontSize: 13, flex: 1, minWidth: 120 }}
            />
          </div>

          <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 4, alignItems: 'center' }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', marginRight: 4 }}>Quick add:</span>
            {SUGGESTED_SKILLS.filter(s => !skills.includes(s)).slice(0, 8).map(s => (
              <button key={s} type="button" className="btn btn-ghost btn-xs" onClick={() => addSkill(s)} style={{ fontSize: 11, padding: '2px 6px', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                + {s}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="form-group">
            <label className="form-label">Min. Experience (years)</label>
            <input className="input" type="number" min="0" max="30" step="0.5" value={minExp} onChange={e => setMinExp(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Education Requirement</label>
            <select className="input" value={degree} onChange={e => setDegree(e.target.value)}>
              <option value="Any / None">Any / None</option>
              <option value="Associate's">Associate's Degree</option>
              <option value="Bachelor's">Bachelor's Degree</option>
              <option value="Master's">Master's Degree</option>
              <option value="PhD">PhD / Doctorate</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Full Job Description (optional)</label>
          <textarea className="textarea" placeholder="Paste full job description text here for detailed AI context matching..."
            value={raw} onChange={e => setRaw(e.target.value)} style={{ minHeight: 120 }} />
        </div>

        <div className="flex gap-3" style={{ justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-accent" disabled={loading}>
            {loading ? <><div className="spinner" style={{ borderTopColor: '#09090B', width: 13, height: 13 }} /> Creating…</> : <><Plus size={13} /> Create Job</>}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function EditJobModal({ token, job, onClose, onUpdated }) {
  const parsed = job?.parsed_json || {};
  const [title, setTitle] = useState(job?.title || '');
  const [skills, setSkills] = useState(parsed.skills || parsed.required_skills || []);
  const [skillInput, setSkillInput] = useState('');
  const [minExp, setMinExp] = useState(parsed.min_experience_years || parsed.min_years_experience || 0);
  const [degree, setDegree] = useState(parsed.degree_required || parsed.required_degree || "Bachelor's");
  const [raw, setRaw] = useState(job?.raw_text || '');
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  const addSkill = (s) => {
    const clean = s.trim().replace(/,/g, '');
    if (clean && !skills.includes(clean)) {
      setSkills(prev => [...prev, clean]);
    }
    setSkillInput('');
  };

  const removeSkill = (s) => {
    setSkills(prev => prev.filter(x => x !== s));
  };

  const handleSkillKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addSkill(skillInput);
    }
  };

  const submit = async e => {
    e.preventDefault();
    if (!title.trim()) { setErr('Job title is required.'); return; }
    setLoading(true); setErr('');
    try {
      const res = await api(`/jobs/${job.id}`, token, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          raw_text: raw.trim(),
          skills,
          min_experience_years: parseFloat(minExp) || 0,
          degree_required: degree
        }),
      });
      if (!res.ok) throw new Error('Failed to update job');
      onUpdated();
    } catch (e) { setErr(e.message); setLoading(false); }
  };

  return (
    <Modal title={`Edit Job: ${job.title}`} onClose={onClose}>
      {err && <div style={{ background: 'var(--red-dim)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius-md)', padding: '8px 12px', marginBottom: 'var(--space-4)', fontSize: 13, color: 'var(--red)' }}>{err}</div>}
      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <div className="form-group">
          <label className="form-label">Job Title</label>
          <input className="input" value={title} onChange={e => setTitle(e.target.value)} required />
        </div>

        <div className="form-group">
          <label className="form-label">Required Skills ({skills.length})</label>
          <div className="input" style={{ minHeight: 48, padding: '6px 10px', display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center', cursor: 'text' }} onClick={() => document.getElementById('edit-skill-input')?.focus()}>
            {skills.map(s => (
              <span key={s} className="skill-tag" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 8px', fontSize: 12, background: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>
                {s}
                <X size={12} style={{ cursor: 'pointer', opacity: 0.7 }} onClick={(e) => { e.stopPropagation(); removeSkill(s); }} />
              </span>
            ))}
            <input
              id="edit-skill-input"
              type="text"
              placeholder="Add skill & press Enter..."
              value={skillInput}
              onChange={e => {
                if (e.target.value.includes(',')) addSkill(e.target.value);
                else setSkillInput(e.target.value);
              }}
              onKeyDown={handleSkillKeyDown}
              onBlur={() => { if (skillInput.trim()) addSkill(skillInput); }}
              style={{ border: 'none', outline: 'none', background: 'transparent', color: 'var(--text-primary)', fontSize: 13, flex: 1, minWidth: 120 }}
            />
          </div>
          <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 4, alignItems: 'center' }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', marginRight: 4 }}>Quick add:</span>
            {SUGGESTED_SKILLS.filter(s => !skills.includes(s)).slice(0, 8).map(s => (
              <button key={s} type="button" className="btn btn-ghost btn-xs" onClick={() => addSkill(s)} style={{ fontSize: 11, padding: '2px 6px', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                + {s}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="form-group">
            <label className="form-label">Min. Experience (years)</label>
            <input className="input" type="number" min="0" max="30" step="0.5" value={minExp} onChange={e => setMinExp(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Education Requirement</label>
            <select className="input" value={degree} onChange={e => setDegree(e.target.value)}>
              <option value="Any / None">Any / None</option>
              <option value="Associate's">Associate's Degree</option>
              <option value="Bachelor's">Bachelor's Degree</option>
              <option value="Master's">Master's Degree</option>
              <option value="PhD">PhD / Doctorate</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Job Description</label>
          <textarea className="textarea" value={raw} onChange={e => setRaw(e.target.value)} style={{ minHeight: 120 }} />
        </div>

        <div className="flex gap-3" style={{ justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-accent" disabled={loading}>
            {loading ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

// ─────────────────────────────────────────
//  CANDIDATE COMPARISON MATRIX MODAL
// ─────────────────────────────────────────

function CompareModal({ candidates, jobSkills, onClose }) {
  if (!candidates || candidates.length === 0) return null;

  return (
    <Modal title={`Candidate Comparison Matrix (${candidates.length} Selected)`} onClose={onClose} width={960}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        <div className="comparison-grid" style={{ gridTemplateColumns: `180px repeat(${candidates.length}, 1fr)` }}>
          {/* Header Row */}
          <div className="comparison-cell header">Candidate</div>
          {candidates.map(c => (
            <div key={c.id} className="comparison-cell header" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
              <span style={{ fontWeight: 700, fontSize: 14 }}>{c.name}</span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{c.email}</span>
              <span className={`badge ${scoreBadge(c.overall_score)}`} style={{ marginTop: 4, fontSize: 12 }}>
                {Math.round(c.overall_score * 100)}% Overall Match
              </span>
            </div>
          ))}

          {/* Progress Bar */}
          <div className="comparison-cell header">Overall Fit</div>
          {candidates.map(c => (
            <div key={c.id} className="comparison-cell" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
              <ProgressBar value={c.overall_score} className={progressCls(c.overall_score)} height={6} />
            </div>
          ))}

          {/* Experience */}
          <div className="comparison-cell header">Experience</div>
          {candidates.map(c => {
            const exp = c.parsed_resume_json?.total_years_experience || c.breakdown?.experience_years || 'N/A';
            return (
              <div key={c.id} className="comparison-cell font-mono">
                <Clock size={13} style={{ marginRight: 6, color: 'var(--text-muted)' }} />
                <span>{exp} years</span>
              </div>
            );
          })}

          {/* Education */}
          <div className="comparison-cell header">Degree</div>
          {candidates.map(c => {
            const deg = c.parsed_resume_json?.degree || c.breakdown?.degree || 'N/A';
            return (
              <div key={c.id} className="comparison-cell">
                <GraduationCap size={13} style={{ marginRight: 6, color: 'var(--text-muted)' }} />
                <span>{deg}</span>
              </div>
            );
          })}

          {/* Semantic Score */}
          <div className="comparison-cell header">Semantic Relevance</div>
          {candidates.map(c => {
            const s = c.breakdown?.semantic_score || c.breakdown?.semantic_similarity || 0;
            return (
              <div key={c.id} className="comparison-cell font-mono">
                {Math.round(s * 100)}%
              </div>
            );
          })}

          {/* Skill Match Score */}
          <div className="comparison-cell header">Skill Match Score</div>
          {candidates.map(c => {
            const s = c.breakdown?.skill_score || c.breakdown?.skill_overlap || 0;
            return (
              <div key={c.id} className="comparison-cell font-mono">
                {Math.round(s * 100)}%
              </div>
            );
          })}

          {/* Required Skills Matrix */}
          {jobSkills.map(skill => (
            <React.Fragment key={skill}>
              <div className="comparison-cell header" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {skill}
              </div>
              {candidates.map(c => {
                const cSkills = (c.parsed_resume_json?.skills || []).map(x => String(x).toLowerCase());
                const hasSkill = cSkills.some(x => x.includes(skill.toLowerCase()) || skill.toLowerCase().includes(x));
                return (
                  <div key={c.id} className="comparison-cell">
                    {hasSkill ? (
                      <span style={{ color: 'var(--green)', display: 'inline-flex', alignItems: 'center', gap: 4, fontWeight: 600, fontSize: 12 }}>
                        <CheckCircle size={14} /> Possesses
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12 }}>
                        <XCircle size={14} style={{ opacity: 0.5 }} /> Missing
                      </span>
                    )}
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>

        <div className="flex justify-between items-center" style={{ marginTop: 'var(--space-2)' }}>
          <span className="text-xs text-muted">Comparative analysis calculated live by Aero AI Engine.</span>
          <button className="btn btn-accent" onClick={onClose}>Close Matrix</button>
        </div>
      </div>
    </Modal>
  );
}

function CopilotChat({ jobId, token, candidates, setCandidates, setSortBy }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([{ role: 'system', content: 'Hi! I am your AI Recruiter Copilot. Ask me to find candidates or analyze this pipeline.' }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: userMsg, job_id: parseInt(jobId) })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
      
      // If copilot filtered candidates, highlight them by bringing them to top (simulated here by setting a specific view filter or sort)
      if (data.candidate_ids && data.candidate_ids.length > 0) {
        // Just as an example, we could filter or re-sort. Here we just show a little badge in chat.
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error connecting to the Copilot engine.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      <button 
        className="btn btn-primary" 
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'fixed', bottom: 32, right: 32, borderRadius: '50%', width: 56, height: 56,
          boxShadow: '0 8px 32px rgba(200, 255, 71, 0.2)', zIndex: 1000, padding: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}
      >
        {isOpen ? <X size={24} /> : <MessageSquare size={24} />}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div style={{
          position: 'fixed', bottom: 100, right: 32, width: 380, height: 500,
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)',
          boxShadow: '0 24px 64px rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <div style={{ padding: 'var(--space-4)', borderBottom: '1px solid var(--border)', background: 'rgba(255,255,255,0.02)', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--primary)', color: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Brain size={16} />
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>Aero Copilot</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Always online</div>
            </div>
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {messages.map((m, i) => (
              <div key={i} style={{ 
                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                background: m.role === 'user' ? 'var(--primary)' : 'var(--bg)',
                color: m.role === 'user' ? 'var(--bg)' : 'var(--text-primary)',
                padding: 'var(--space-3) var(--space-4)',
                borderRadius: 'var(--radius)',
                border: m.role === 'user' ? 'none' : '1px solid var(--border)',
                maxWidth: '85%', fontSize: 14, lineHeight: 1.5,
                whiteSpace: 'pre-wrap'
              }}>
                {m.content}
              </div>
            ))}
            {loading && (
              <div style={{ alignSelf: 'flex-start', color: 'var(--text-muted)', fontSize: 12, display: 'flex', gap: 4, alignItems: 'center' }}>
                <Brain size={12} className="spin" /> Thinking...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSend} style={{ padding: 'var(--space-3)', borderTop: '1px solid var(--border)', display: 'flex', gap: 'var(--space-2)' }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask anything..."
              style={{ flex: 1, background: 'var(--bg)', border: '1px solid var(--border)', padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius)', color: 'var(--text-primary)', outline: 'none' }}
            />
            <button type="submit" disabled={!input.trim() || loading} style={{ background: 'var(--primary)', color: 'var(--bg)', border: 'none', borderRadius: 'var(--radius)', width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', opacity: (!input.trim() || loading) ? 0.5 : 1 }}>
              <Send size={16} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}

// ─────────────────────────────────────────
//  JOB PIPELINE
// ─────────────────────────────────────────

function JobPipeline({ token }) {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [selected, setSelected] = useState(null);
  const [viewMode, setViewMode] = useState('list');
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('score');
  const [githubUrl, setGithubUrl] = useState('');
  const [importingGithub, setImportingGithub] = useState(false);
  // Drag-and-drop
  const [draggedId, setDraggedId] = useState(null);
  const [dragOverStage, setDragOverStage] = useState(null);
  // Bulk selection
  const [bulkSelected, setBulkSelected] = useState(new Set());
  const [showBulkBar, setShowBulkBar] = useState(false);
  const fileRef = useRef(null);
  const toast = useToast();
  const navigate = useNavigate();

  const fetchAll = useCallback(async () => {
    try {
      const [jobRes, cRes] = await Promise.all([
        api(`/jobs/${jobId}`, token),
        api(`/jobs/${jobId}/candidates/`, token),
      ]);
      if (jobRes.ok) setJob(await jobRes.json());
      if (cRes.ok) setCandidates(await cRes.json());
    } catch { toast('Failed to load job data', 'error'); }
    finally { setLoading(false); }
  }, [jobId, token, toast]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Bulk / Single File Upload Handler
  const uploadFiles = async (filesList) => {
    if (!filesList || filesList.length === 0) return;
    // Pre-validate file sizes on client side
    const MAX_MB = 10;
    const oversized = Array.from(filesList).filter(f => f.size > MAX_MB * 1024 * 1024);
    if (oversized.length > 0) {
      toast(`${oversized.length} file(s) exceed the ${MAX_MB}MB limit and were skipped.`, 'error');
      filesList = Array.from(filesList).filter(f => f.size <= MAX_MB * 1024 * 1024);
      if (filesList.length === 0) return;
    }
    setUploading(true);
    let successCount = 0;
    let duplicateCount = 0;
    toast(`Uploading ${filesList.length} resume(s)…`, 'info');

    for (let i = 0; i < filesList.length; i++) {
      const file = filesList[i];
      const fd = new FormData();
      fd.append('file', file);
      try {
        const res = await fetch(`${API_URL}/jobs/${jobId}/candidates/upload`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: fd,
        });
        if (res.ok) {
          const data = await res.json();
          if (data.duplicate) duplicateCount++;
          else successCount++;
        }
      } catch (e) {
        console.error(e);
      }
    }

    setUploading(false);
    await fetchAll();
    if (duplicateCount > 0) toast(`⚠️ ${duplicateCount} duplicate(s) detected — already in pipeline.`, 'info');
    if (successCount > 0) toast(`Successfully processed ${successCount} resume(s)!`, 'success');
  };

  const importFromGitHub = async (e) => {
    e.preventDefault();
    if (!githubUrl || !githubUrl.includes('github.com')) {
      toast('Please enter a valid GitHub URL', 'error');
      return;
    }
    setImportingGithub(true);
    toast('Extracting GitHub profile...', 'info');
    try {
      const res = await api('/candidates/from-github', token, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: parseInt(jobId), github_url: githubUrl })
      });
      if (res.ok) {
        toast('Successfully imported candidate from GitHub!', 'success');
        setGithubUrl('');
        await fetchAll();
      } else {
        toast('Failed to import from GitHub.', 'error');
      }
    } catch {
      toast('Error importing GitHub profile.', 'error');
    }
    setImportingGithub(false);
  };

  const handleStatus = async (cid, status) => {
    try {
      const res = await api(`/candidates/${cid}/status`, token, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (res.ok) {
        const updated = await res.json();
        setCandidates(prev => prev.map(c => c.id === cid ? updated : c));
        if (selected?.id === cid) setSelected(updated);
        toast(`Marked as ${STATUS_CONFIG[status].label}`, 'success');
      }
    } catch { toast('Failed to update candidate status', 'error'); }
  };

  // Drag-and-drop handlers
  const handleDragStart = (e, candidateId) => {
    setDraggedId(candidateId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, stage) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverStage(stage);
  };

  const handleDrop = async (e, targetStage) => {
    e.preventDefault();
    setDragOverStage(null);
    if (!draggedId) return;
    const candidate = candidates.find(c => c.id === draggedId);
    if (!candidate || (candidate.status || 'new') === targetStage) { setDraggedId(null); return; }
    // Optimistic UI update
    setCandidates(prev => prev.map(c => c.id === draggedId ? { ...c, status: targetStage } : c));
    await handleStatus(draggedId, targetStage);
    setDraggedId(null);
  };

  // Bulk selection handlers
  const toggleBulkSelect = (id) => {
    setBulkSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      setShowBulkBar(next.size > 0);
      return next;
    });
  };

  const selectAllInStage = (stage) => {
    const stageIds = candidates.filter(c => (c.status || 'new') === stage).map(c => c.id);
    setBulkSelected(prev => {
      const next = new Set(prev);
      stageIds.forEach(id => next.add(id));
      setShowBulkBar(next.size > 0);
      return next;
    });
  };

  const clearBulkSelect = () => { setBulkSelected(new Set()); setShowBulkBar(false); };

  const bulkUpdateStatus = async (status) => {
    const ids = Array.from(bulkSelected);
    try {
      const res = await api('/candidates/bulk-status', token, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_ids: ids, status })
      });
      if (res.ok) {
        const data = await res.json();
        setCandidates(prev => prev.map(c => ids.includes(c.id) ? { ...c, status } : c));
        toast(`Updated ${data.updated} candidates to ${STATUS_CONFIG[status].label}`, 'success');
        clearBulkSelect();
      }
    } catch { toast('Bulk update failed', 'error'); }
  };

  const bulkDelete = async () => {
    if (!window.confirm(`Delete ${bulkSelected.size} selected candidates? This cannot be undone.`)) return;
    const ids = Array.from(bulkSelected);
    try {
      const res = await api('/candidates/bulk-delete', token, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_ids: ids })
      });
      if (res.ok) {
        const data = await res.json();
        setCandidates(prev => prev.filter(c => !ids.includes(c.id)));
        toast(`Deleted ${data.deleted} candidates`, 'info');
        clearBulkSelect();
      }
    } catch { toast('Bulk delete failed', 'error'); }
  };

  const handleDelete = async cid => {
    try {
      const res = await api(`/candidates/${cid}`, token, { method: 'DELETE' });
      if (res.ok || res.status === 204) {
        setCandidates(prev => prev.filter(c => c.id !== cid));
        if (selected?.id === cid) setSelected(null);
        setSelectedForCompare(prev => prev.filter(id => id !== cid));
        toast('Candidate removed', 'info');
      }
    } catch { toast('Network error', 'error'); }
  };

  const exportCSV = () => {
    api(`/jobs/${jobId}/candidates/export`, token)
      .then(r => r.blob())
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url;
        a.download = `${job?.title || 'candidates'}_export.csv`;
        a.click(); URL.revokeObjectURL(url);
      });
  };

  const toggleCompareSelect = (e, id) => {
    e.stopPropagation();
    setSelectedForCompare(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  // Filter & Sort
  let visible = candidates;
  if (search) visible = visible.filter(c => c.name.toLowerCase().includes(search.toLowerCase()) || c.email.toLowerCase().includes(search.toLowerCase()));
  if (statusFilter !== 'all') visible = visible.filter(c => (c.status || 'new') === statusFilter);
  if (sortBy === 'score') visible = [...visible].sort((a, b) => b.overall_score - a.overall_score);
  else if (sortBy === 'name') visible = [...visible].sort((a, b) => a.name.localeCompare(b.name));

  const skills = job?.parsed_json?.skills || job?.parsed_json?.required_skills || [];
  const minExp = job?.parsed_json?.min_experience_years || job?.parsed_json?.min_years_experience || 0;
  const degree = job?.parsed_json?.degree_required || job?.parsed_json?.required_degree;

  const statusCounts = { all: candidates.length };
  candidates.forEach(c => { const s = c.status || 'new'; statusCounts[s] = (statusCounts[s] || 0) + 1; });

  const [showEditModal, setShowEditModal] = useState(false);

  return (
    <div className="main-content" style={{ paddingRight: selected ? 'var(--space-4)' : 'var(--space-10)', transition: 'all 0.25s ease' }}>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2" style={{ marginBottom: 'var(--space-6)', fontSize: 13, color: 'var(--text-muted)' }}>
        <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontFamily: 'var(--font-sans)', fontSize: 13 }}>Jobs</button>
        <ChevronRight size={13} />
        <span style={{ color: 'var(--text-primary)' }}>{job?.title || `#${jobId}`}</span>
      </div>

      {/* Job header card */}
      {loading ? (
        <div className="skeleton" style={{ height: 110, borderRadius: 'var(--radius-lg)', marginBottom: 'var(--space-6)' }} />
      ) : (
        <div className="card" style={{ padding: 'var(--space-5)', marginBottom: 'var(--space-6)' }}>
          <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-4)' }}>
            <h1 style={{ fontSize: 20, fontWeight: 700, letterSpacing: '-0.03em' }}>{job?.title || `Job #${jobId}`}</h1>
            <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowEditModal(true)} title="Edit Job & Required Skills">
                <Edit3 size={13} /> Edit Job
              </button>
              <button className="btn btn-ghost btn-sm" onClick={exportCSV} title="Export CSV">
                <Download size={13} /> Export CSV
              </button>
              <div style={{ textAlign: 'right', marginLeft: 8 }}>
                <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.04em' }}>{candidates.length}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>applicants</div>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
            {skills.slice(0, 12).map(s => <span key={s} className="skill-tag">{s}</span>)}
            {skills.length > 12 && <span className="skill-tag">+{skills.length - 12}</span>}
            {minExp > 0 && <span className="badge badge-blue" style={{ marginLeft: 6 }}><Clock size={10} /> {minExp}+ yrs</span>}
            {degree && <span className="badge badge-muted"><GraduationCap size={10} /> {degree}</span>}
          </div>
        </div>
      )}

      {showEditModal && job && (
        <EditJobModal token={token} job={job} onClose={() => setShowEditModal(false)}
          onUpdated={() => { fetchAll(); setShowEditModal(false); toast('Job updated successfully!', 'success'); }} />
      )}

      {/* Upload Zone (Supports Batch Multi-File Upload) */}
      <input type="file" ref={fileRef} multiple onChange={e => { if (e.target.files && e.target.files.length > 0) { uploadFiles(Array.from(e.target.files)); e.target.value = ''; } }}
        style={{ display: 'none' }} accept=".pdf,.docx,.doc,.txt" />
      <div className={`drop-zone${isDragging ? ' dragging' : ''}${uploading ? ' uploading' : ''}`}
        onDragOver={e => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); }}
        onDragLeave={e => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); }}
        onDrop={e => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); if (e.dataTransfer?.files?.length) uploadFiles(Array.from(e.dataTransfer.files)); }}
        onClick={() => !uploading && fileRef.current?.click()}
        style={{ marginBottom: 'var(--space-6)' }}>
        <div className="drop-zone-icon" style={{ margin: '0 auto var(--space-4)' }}>
          {uploading ? <div className="spinner" /> : <Upload size={20} style={{ color: isDragging ? 'var(--accent)' : 'var(--text-secondary)' }} />}
        </div>
        <p style={{ fontWeight: 600, fontSize: 15, marginBottom: 5, color: isDragging ? 'var(--accent)' : 'var(--text-primary)' }}>
          {uploading ? 'Analyzing batch resumes with AI…' : isDragging ? 'Drop resumes here to upload' : 'Upload resumes (Single or Batch)'}
        </p>
        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          {uploading ? 'Parsing candidate skills & calculating match score…' : 'Click to select multiple files or drag & drop — PDF, DOCX, TXT supported'}
        </p>
      </div>

      {/* Control Bar: Filters, View Toggle, Compare Button */}
      <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-4)', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <div className="view-toggle">
            <button className={`view-toggle-btn${viewMode === 'list' ? ' active' : ''}`} onClick={() => setViewMode('list')}>
              <List size={14} /> Table View
            </button>
            <button className={`view-toggle-btn${viewMode === 'kanban' ? ' active' : ''}`} onClick={() => setViewMode('kanban')}>
              <Columns size={14} /> Kanban Board
            </button>
          </div>

          {selectedForCompare.length > 0 && (
            <button className="btn btn-accent btn-sm" onClick={() => setShowCompareModal(true)}>
              <Scale size={13} /> Compare Selected ({selectedForCompare.length})
            </button>
          )}
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: 4, marginRight: 8 }}>
            {['all', 'new', 'shortlisted', 'hired', 'rejected'].map(s => (
              <button key={s} onClick={() => setStatusFilter(s)}
                className={`btn btn-sm${statusFilter === s ? ' btn-accent' : ' btn-ghost'}`}
                style={{ height: 30, fontSize: 12, padding: '2px 10px' }}>
                {s === 'all' ? `All (${statusCounts.all || 0})` : `${STATUS_CONFIG[s]?.label} (${statusCounts[s] || 0})`}
              </button>
            ))}
          </div>

          <div style={{ position: 'relative' }}>
            <Search size={13} style={{ position: 'absolute', left: 9, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
            <input className="input" placeholder="Search candidates…" value={search} onChange={e => setSearch(e.target.value)} style={{ paddingLeft: 28, width: 170, height: 30, fontSize: 13 }} />
          </div>

          <select className="input" value={sortBy} onChange={e => setSortBy(e.target.value)}
            style={{ height: 30, fontSize: 12, paddingLeft: 8, width: 110, cursor: 'pointer' }}>
            <option value="score">Sort: Score</option>
            <option value="name">Sort: Name</option>
          </select>
        </div>
      </div>

      {/* ─── BULK ACTION BAR ─── */}
      {showBulkBar && (
        <div style={{
          position: 'sticky', top: 0, zIndex: 50,
          background: 'var(--bg-elevated)', border: '1px solid var(--accent)',
          borderRadius: 'var(--radius-md)', padding: '10px 16px',
          marginBottom: 'var(--space-4)', display: 'flex',
          alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap',
          boxShadow: '0 0 20px rgba(200,255,71,0.15)'
        }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)' }}>
            ✓ {bulkSelected.size} selected
          </span>
          <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
            <button className="btn btn-sm" style={{ background: 'var(--accent-dim)', color: 'var(--accent)', border: '1px solid var(--accent)' }}
              onClick={() => bulkUpdateStatus('shortlisted')}>
              <CheckCircle size={12}/> Shortlist All
            </button>
            <button className="btn btn-sm" style={{ background: 'var(--green-dim)', color: 'var(--green)', border: '1px solid var(--green)' }}
              onClick={() => bulkUpdateStatus('hired')}>
              <Award size={12}/> Hire All
            </button>
            <button className="btn btn-sm" style={{ background: 'var(--red-dim)', color: 'var(--red)', border: '1px solid var(--red)' }}
              onClick={() => bulkUpdateStatus('rejected')}>
              <XCircle size={12}/> Reject All
            </button>
            <button className="btn btn-sm btn-ghost" style={{ color: 'var(--red)' }} onClick={bulkDelete}>
              <Trash2 size={12}/> Delete Selected
            </button>
          </div>
          <button className="btn btn-ghost btn-sm" style={{ marginLeft: 'auto' }} onClick={clearBulkSelect}>
            <X size={12}/> Clear selection
          </button>
        </div>
      )}

      {/* ── VIEW MODE: KANBAN BOARD ── */}
      {viewMode === 'kanban' ? (
        <div className="kanban-board">
          {['new', 'shortlisted', 'hired', 'rejected'].map(stage => {
            const stageCandidates = visible.filter(c => (c.status || 'new') === stage);
            const cfg = STATUS_CONFIG[stage];
            const isDragTarget = dragOverStage === stage;

            return (
              <div key={stage} className="kanban-column"
                onDragOver={(e) => handleDragOver(e, stage)}
                onDragLeave={() => setDragOverStage(null)}
                onDrop={(e) => handleDrop(e, stage)}
                style={{
                  outline: isDragTarget ? '2px solid var(--accent)' : 'none',
                  background: isDragTarget ? 'var(--accent-dim)' : undefined,
                  transition: 'all 0.15s ease'
                }}>
                <div className="kanban-column-header">
                  <div className="flex items-center gap-2">
                    <span className={`badge ${cfg.cls}`} style={{ padding: '3px 8px' }}>
                      {cfg.icon} {cfg.label}
                    </span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)' }}>
                      {stageCandidates.length}
                    </span>
                  </div>
                  {stageCandidates.length > 0 && (
                    <button className="btn btn-ghost btn-xs" style={{ fontSize: 10, color: 'var(--text-muted)' }}
                      onClick={() => selectAllInStage(stage)} title="Select all in this column">
                      Select all
                    </button>
                  )}
                </div>

                {stageCandidates.length === 0 ? (
                  <div style={{
                    padding: 'var(--space-6)', textAlign: 'center', color: 'var(--text-muted)',
                    fontSize: 12, border: '1px dashed var(--border-subtle)',
                    borderRadius: 'var(--radius-md)', marginTop: 'var(--space-2)'
                  }}>
                    {isDragTarget ? '↓ Drop here' : `No candidates in ${cfg.label}`}
                  </div>
                ) : (
                  stageCandidates.map(c => (
                    <div key={c.id} className="kanban-card"
                      draggable
                      onDragStart={(e) => handleDragStart(e, c.id)}
                      onClick={() => setSelected(selected?.id === c.id ? null : c)}
                      style={{
                        opacity: draggedId === c.id ? 0.4 : 1,
                        cursor: 'grab',
                        border: bulkSelected.has(c.id) ? '1px solid var(--accent)' : undefined,
                        background: bulkSelected.has(c.id) ? 'var(--accent-dim)' : undefined
                      }}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <input type="checkbox" checked={bulkSelected.has(c.id)}
                            onChange={(e) => { e.stopPropagation(); toggleBulkSelect(c.id); }}
                            onClick={(e) => e.stopPropagation()}
                            style={{ cursor: 'pointer' }} />
                          <span style={{ fontWeight: 700, fontSize: 13.5 }}>{c.name}</span>
                        </div>
                        <span className={`badge ${scoreBadge(c.overall_score)}`} style={{ fontSize: 11, fontWeight: 700 }}>
                          {Math.round(c.overall_score * 100)}%
                        </span>
                      </div>
                      <p style={{ fontSize: 11.5, color: 'var(--text-muted)' }} className="truncate">{c.email}</p>
                      <div style={{ fontSize: 10, color: 'var(--text-disabled)', marginTop: 3 }}>⠿ Drag to move stage</div>
                      
                      <div className="flex items-center justify-between" style={{ marginTop: 4, paddingTop: 6, borderTop: '1px solid var(--border-subtle)' }} onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', gap: 4 }}>
                          {stage !== 'shortlisted' && (
                            <button className="btn btn-ghost btn-xs" onClick={() => handleStatus(c.id, 'shortlisted')} style={{ fontSize: 10, color: 'var(--accent)' }}>Shortlist</button>
                          )}
                          {stage !== 'hired' && (
                            <button className="btn btn-ghost btn-xs" onClick={() => handleStatus(c.id, 'hired')} style={{ fontSize: 10, color: 'var(--green)' }}>Hire</button>
                          )}
                          {stage !== 'rejected' && (
                            <button className="btn btn-ghost btn-xs" onClick={() => handleStatus(c.id, 'rejected')} style={{ fontSize: 10, color: 'var(--red)' }}>Reject</button>
                          )}
                        </div>
                        <button className="btn btn-ghost btn-xs" onClick={() => handleDelete(c.id)} style={{ color: 'var(--text-muted)' }} title="Delete">
                          <Trash2 size={11} />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            );
          })}
        </div>
      ) : (
        /* ── VIEW MODE: TABLE LIST ── */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          {loading && [1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 70, borderRadius: 'var(--radius-lg)' }} />)}

          {!loading && visible.length === 0 && (
            <div className="card">
              <div className="empty-state" style={{ padding: 'var(--space-10)' }}>
                <div className="empty-state-icon"><Users size={22} /></div>
                <p style={{ fontWeight: 600 }}>{search || statusFilter !== 'all' ? 'No matching candidates' : 'No applicants yet'}</p>
                <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                  {search || statusFilter !== 'all' ? 'Try adjusting your search query or stage filters.' : 'Upload resumes above to view instant AI ranking.'}
                </p>
              </div>
            </div>
          )}

          {visible.map((c, i) => {
            const sc = c.status || 'new';
            const cfg = STATUS_CONFIG[sc];
            const rank = candidates.findIndex(x => x.id === c.id);
            const isCompared = selectedForCompare.includes(c.id);

            return (
              <div key={c.id} className={`card animate-slide-in${selected?.id === c.id ? '' : ' card-clickable'}`}
                style={{ padding: 'var(--space-4) var(--space-5)', animationDelay: `${i * 0.03}s`, borderColor: selected?.id === c.id ? 'var(--border-strong)' : isCompared ? 'var(--accent)' : undefined, cursor: 'pointer' }}
                onClick={() => setSelected(c.id === selected?.id ? null : c)}>
                <div className="flex items-center gap-3">
                  <input type="checkbox" checked={isCompared} onChange={(e) => toggleCompareSelect(e, c.id)} onClick={(e) => e.stopPropagation()} style={{ cursor: 'pointer', marginRight: 4 }} title="Select for matrix comparison" />

                  <div style={{ width: 28, textAlign: 'center', flexShrink: 0 }}>
                    {rank === 0 ? <Star size={14} style={{ color: 'var(--amber)' }} /> :
                      <span style={{ fontSize: 11.5, color: 'var(--text-muted)', fontWeight: 600 }}>#{rank + 1}</span>}
                  </div>
                  <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <User size={15} style={{ color: 'var(--text-secondary)' }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="flex items-center gap-2">
                      <p style={{ fontWeight: 600, fontSize: 14, letterSpacing: '-0.01em' }} className="truncate">{c.name}</p>
                      <span className={`badge ${cfg.cls}`} style={{ display: 'flex', alignItems: 'center', gap: 3, flexShrink: 0 }}>
                        {cfg.icon} {cfg.label}
                      </span>
                    </div>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 1 }} className="truncate">{c.email}</p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexShrink: 0 }}>
                    <div style={{ textAlign: 'right' }}>
                      <span className={`badge ${scoreBadge(c.overall_score)}`} style={{ fontSize: 13, fontWeight: 700, padding: '3px 9px' }}>
                        {Math.round(c.overall_score * 100)}%
                      </span>
                      <p style={{ fontSize: 10, color: 'var(--text-muted)', textAlign: 'right', marginTop: 3 }}>match</p>
                    </div>
                    <div style={{ display: 'flex', gap: 4 }} onClick={e => e.stopPropagation()}>
                      {c.status !== 'shortlisted' && (
                        <button className="btn btn-ghost btn-sm" onClick={() => handleStatus(c.id, 'shortlisted')}
                          style={{ padding: '3px 7px', height: 'auto', color: 'var(--accent)' }} title="Shortlist"><CheckCircle size={13} /></button>
                      )}
                      {c.status !== 'hired' && (
                        <button className="btn btn-ghost btn-sm" onClick={() => handleStatus(c.id, 'hired')}
                          style={{ padding: '3px 7px', height: 'auto', color: 'var(--green)' }} title="Hire"><Award size={13} /></button>
                      )}
                      {c.status !== 'rejected' && (
                        <button className="btn btn-ghost btn-sm" onClick={() => handleStatus(c.id, 'rejected')}
                          style={{ padding: '3px 7px', height: 'auto', color: 'var(--text-muted)' }} title="Reject"><XCircle size={13} /></button>
                      )}
                      <button className="btn btn-ghost btn-sm" onClick={() => handleDelete(c.id)}
                        style={{ padding: '3px 7px', height: 'auto', color: 'var(--red)' }} title="Delete"><Trash2 size={13} /></button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Comparison Modal */}
      {showCompareModal && (
        <CompareModal
          candidates={candidates.filter(c => selectedForCompare.includes(c.id))}
          jobSkills={skills}
          onClose={() => setShowCompareModal(false)}
        />
      )}

      {/* Candidate Details Drawer Panel */}
      {selected && (
        <CandidatePanel candidate={selected} jobSkills={skills}
          onClose={() => setSelected(null)}
          onDelete={() => handleDelete(selected.id)}
          onStatusChange={(status) => handleStatus(selected.id, status)}
          onNotesSave={async (notes) => {
            const res = await api(`/candidates/${selected.id}/notes`, token, {
              method: 'PATCH', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ notes }),
            });
            if (res.ok) {
              const updated = await res.json();
              setCandidates(prev => prev.map(c => c.id === selected.id ? updated : c));
              setSelected(updated);
              toast('Notes saved', 'success');
            }
          }}
        />
      )}
    </div>
  );
}

// ─────────────────────────────────────────
//  CANDIDATE PANEL (4 TABS)
// ─────────────────────────────────────────

function CandidatePanel({ candidate: c, jobSkills, onClose, onDelete, onStatusChange, onNotesSave }) {
  const [notes, setNotes] = useState(c.notes || '');
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [copiedEmail, setCopiedEmail] = useState(false);
  const [copiedQuestions, setCopiedQuestions] = useState(false);
  const [emailType, setEmailType] = useState('invite');

  const bd = c.breakdown || {};
  const resume = c.parsed_resume_json || {};
  const contact = resume.contact || {};
  const resumeSkills = resume.skills || [];
  const experiences = resume.experience || [];

  const jdSkillsSet = new Set((jobSkills || []).map(s => s.toLowerCase()));
  const matchedSkills = resumeSkills.filter(s => jdSkillsSet.has(s.toLowerCase()));
  const missingSkills = (jobSkills || []).filter(s => !resumeSkills.some(x => x.toLowerCase().includes(s.toLowerCase())));
  const otherSkills = resumeSkills.filter(s => !jdSkillsSet.has(s.toLowerCase()));

  const dims = [
    { label: 'Semantic Similarity', key: 'semantic_similarity', cls: 'progress-blue' },
    { label: 'Skill Match',         key: 'skill_overlap',       cls: 'progress-accent' },
    { label: 'Experience Fit',      key: 'experience_fit',      cls: 'progress-high' },
    { label: 'Education Fit',       key: 'education_fit',       cls: 'progress-med' },
  ];

  const explLines = (c.explanation || '').split('\n').filter(Boolean);

  const saveNotes = async () => {
    setSaving(true);
    await onNotesSave(notes);
    setSaving(false);
  };

  // Generate tailored questions & email
  const generatedQuestions = [
    `Can you describe your experience working with ${matchedSkills.slice(0, 2).join(' and ') || 'key technical stacks'} in your previous roles?`,
    `Our role requires proficiency in ${missingSkills[0] || 'advanced system architecture'}. How would you approach getting up to speed on this technology?`,
    `Tell me about a challenging engineering decision you made during your tenure at ${experiences[0]?.company || 'your past company'}.`,
    `How do you ensure code quality, automated testing, and scalable deployment in fast-moving engineering environments?`
  ];

  const emailDrafts = {
    invite: `Hi ${c.name},\n\nThank you for applying for our position. Based on your strong technical background and expertise in ${matchedSkills.slice(0, 3).join(', ') || 'software engineering'}, we would love to invite you for an initial interview!\n\nPlease let us know your availability for a 30-minute call this week.\n\nBest regards,\nRecruiting Team`,
    shortlist: `Hi ${c.name},\n\nGreat news! Your profile has been shortlisted for our open role. Our hiring manager was impressed with your experience. We will follow up shortly with next steps.\n\nBest regards,\nRecruiting Team`,
    reject: `Hi ${c.name},\n\nThank you for taking the time to apply. While your experience is impressive, we have decided to move forward with candidates whose profiles align more closely with our specific requirements at this time.\n\nWe wish you all the best in your job search.\n\nBest regards,\nRecruiting Team`
  };

  const copyText = (text, type) => {
    navigator.clipboard.writeText(text);
    if (type === 'email') { setCopiedEmail(true); setTimeout(() => setCopiedEmail(false), 2000); }
    if (type === 'questions') { setCopiedQuestions(true); setTimeout(() => setCopiedQuestions(false), 2000); }
  };

  const tabs = ['overview', 'resume', 'ai_assistant', 'notes'];
  const tabLabels = { overview: 'Overview', resume: 'Full Resume', ai_assistant: 'AI Assistant', notes: 'Notes' };

  return (
    <div className="slide-panel" style={{ width: 460 }}>
      {/* Header */}
      <div className="slide-panel-header">
        <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-3)' }}>
          <div className="flex items-center gap-3">
            <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <User size={18} style={{ color: 'var(--text-secondary)' }} />
            </div>
            <div style={{ minWidth: 0 }}>
              <p style={{ fontWeight: 700, fontSize: 14, letterSpacing: '-0.01em' }} className="truncate">{c.name}</p>
              <a href={`mailto:${c.email}`} style={{ fontSize: 12, color: 'var(--accent)' }} className="truncate">{c.email}</a>
            </div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose} style={{ padding: '3px 7px', height: 'auto' }}><X size={15} /></button>
        </div>
        {/* Status selector */}
        <div style={{ display: 'flex', gap: 5 }}>
          {Object.entries(STATUS_CONFIG).map(([s, cfg]) => (
            <button key={s} onClick={() => onStatusChange(s)}
              className={`btn btn-sm${(c.status || 'new') === s ? ' btn-accent' : ' btn-ghost'}`}
              style={{ flex: 1, justifyContent: 'center', fontSize: 11.5, padding: '2px 4px', height: 26 }}>
              {cfg.icon} {cfg.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', padding: '0 var(--space-6)' }}>
        {tabs.map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            style={{ background: 'none', border: 'none', fontFamily: 'var(--font-sans)', fontSize: 12.5, fontWeight: 500, padding: 'var(--space-3) var(--space-2.5)', cursor: 'pointer', color: activeTab === t ? 'var(--text-primary)' : 'var(--text-muted)', borderBottom: activeTab === t ? '2px solid var(--accent)' : '2px solid transparent', marginBottom: -1 }}>
            {tabLabels[t]}
          </button>
        ))}
      </div>

      <div className="slide-panel-body" style={{ padding: 'var(--space-5) var(--space-6)' }}>

        {/* ── OVERVIEW TAB ── */}
        {activeTab === 'overview' && (
          <>
            <div style={{ textAlign: 'center', padding: 'var(--space-3) 0' }}>
              <div style={{ fontSize: 52, fontWeight: 700, letterSpacing: '-0.05em', color: scoreColor(c.overall_score), lineHeight: 1 }}>
                {Math.round(c.overall_score * 100)}<span style={{ fontSize: 20, fontWeight: 400 }}>%</span>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: 12.5, marginTop: 4 }}>Overall match score</p>
            </div>
            <div className="divider" />
            <div>
              <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-3)' }}>Score Breakdown</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {dims.map((d, i) => {
                  const v = bd[d.key] ?? 0;
                  return (
                    <div key={d.key}>
                      <div className="flex items-center justify-between" style={{ marginBottom: 4 }}>
                        <span style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>{d.label}</span>
                        <span style={{ fontSize: 12.5, fontWeight: 700, color: scoreColor(v) }}>{Math.round(v * 100)}%</span>
                      </div>
                      <ProgressBar value={v} className={d.cls} delay={i * 80} />
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="divider" />
            <div>
              <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-3)' }}>AI Analysis</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                {explLines.map((line, i) => (
                  <p key={i} style={{ fontSize: 12.5, color: i === 0 ? 'var(--text-primary)' : 'var(--text-secondary)', lineHeight: 1.6, fontWeight: i === 0 ? 600 : 400 }}>{line}</p>
                ))}
              </div>
            </div>
            <div className="divider" />
            <div className="flex gap-2">
              <button className="btn btn-accent btn-sm" style={{ flex: 1, justifyContent: 'center' }} 
                onClick={() => {
                  const subject = encodeURIComponent(`Update regarding your application at Aero ATS`);
                  const body = encodeURIComponent(emailDrafts['invite']);
                  window.open(`mailto:${c.email}?subject=${subject}&body=${body}`, '_blank');
                }}>
                <Mail size={13} /> Email Candidate
              </button>
              <button className="btn btn-primary btn-sm" style={{ flex: 1, justifyContent: 'center' }} 
                onClick={() => {
                  const title = encodeURIComponent(`Interview with ${c.name}`);
                  const details = encodeURIComponent(`Interviewing for open role.\n\nCandidate Email: ${c.email}`);
                  window.open(`https://calendar.google.com/calendar/r/eventedit?text=${title}&details=${details}&add=${c.email}`, '_blank');
                }}>
                <Calendar size={13} /> Schedule Event
              </button>
              <button className="btn btn-danger btn-sm" onClick={onDelete}><Trash2 size={13} /></button>
            </div>
          </>
        )}

        {/* ── RESUME TAB ── */}
        {activeTab === 'resume' && (
          <>
            {resumeSkills.length > 0 && (
              <div>
                <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-3)' }}>Skills</p>
                {matchedSkills.length > 0 && (
                  <div style={{ marginBottom: 'var(--space-3)' }}>
                    <p style={{ fontSize: 11, color: 'var(--green)', marginBottom: 5 }}>✓ Matched JD skills ({matchedSkills.length})</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                      {matchedSkills.map(s => <span key={s} className="badge badge-green" style={{ fontSize: 11 }}>{s}</span>)}
                    </div>
                  </div>
                )}
                {otherSkills.length > 0 && (
                  <div>
                    <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 5 }}>Additional candidate skills ({otherSkills.length})</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                      {otherSkills.map(s => <span key={s} className="skill-tag" style={{ fontSize: 11 }}>{s}</span>)}
                    </div>
                  </div>
                )}
              </div>
            )}
            {experiences.length > 0 && (
              <>
                <div className="divider" />
                <div>
                  <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-3)' }}>Experience</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                    {experiences.map((exp, i) => (
                      <div key={i} style={{ paddingLeft: 'var(--space-3)', borderLeft: '2px solid var(--border-default)' }}>
                        <p style={{ fontWeight: 600, fontSize: 13 }}>{exp.role || 'Role'}</p>
                        <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{exp.company}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </>
        )}

        {/* ── AI ASSISTANT TAB ── */}
        {activeTab === 'ai_assistant' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
            <div>
              <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-3)' }}>
                <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent)', display: 'flex', items: 'center', gap: 4 }}>
                  <Wand2 size={13} /> Tailored Interview Questions
                </p>
                <button className="btn btn-ghost btn-xs" onClick={() => copyText(generatedQuestions.join('\n\n'), 'questions')} style={{ fontSize: 11 }}>
                  {copiedQuestions ? <><Check size={11} color="var(--green)" /> Copied</> : <><Copy size={11} /> Copy All</>}
                </button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {generatedQuestions.map((q, idx) => (
                  <div key={idx} style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 12px', fontSize: 12.5, lineHeight: 1.5 }}>
                    <span style={{ fontWeight: 700, color: 'var(--text-muted)', marginRight: 6 }}>Q{idx + 1}.</span>
                    {q}
                  </div>
                ))}
              </div>
            </div>

            <div className="divider" />

            <div>
              <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-3)' }}>
                <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', display: 'flex', items: 'center', gap: 4 }}>
                  <MessageSquare size={13} /> Recruiter Email Generator
                </p>
                <button className="btn btn-ghost btn-xs" onClick={() => copyText(emailDrafts[emailType], 'email')} style={{ fontSize: 11 }}>
                  {copiedEmail ? <><Check size={11} color="var(--green)" /> Copied</> : <><Copy size={11} /> Copy Draft</>}
                </button>
              </div>

              <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                {['invite', 'shortlist', 'reject'].map(type => (
                  <button key={type} className={`btn btn-xs${emailType === type ? ' btn-accent' : ' btn-ghost'}`} onClick={() => setEmailType(type)} style={{ textTransform: 'capitalize' }}>
                    {type}
                  </button>
                ))}
              </div>

              <textarea className="textarea" readOnly value={emailDrafts[emailType]} style={{ minHeight: 140, fontSize: 12, fontFamily: 'var(--font-mono)' }} />
            </div>
          </div>
        )}

        {/* ── NOTES TAB ── */}
        {activeTab === 'notes' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <p style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>Recruiter notes and interview feedback:</p>
            <textarea className="textarea" placeholder="Type private notes here..." value={notes} onChange={e => setNotes(e.target.value)} style={{ minHeight: 180 }} />
            <button className="btn btn-accent btn-sm" onClick={saveNotes} disabled={saving} style={{ alignSelf: 'flex-end' }}>
              {saving ? 'Saving…' : 'Save Notes'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────
//  ANALYTICS DASHBOARD
// ─────────────────────────────────────────

function Analytics({ token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  useEffect(() => {
    api('/analytics/', token)
      .then(res => { if (res.ok) return res.json(); throw new Error(); })
      .then(d => setData(d))
      .catch(() => toast('Failed to load analytics', 'error'))
      .finally(() => setLoading(false));
  }, [token, toast]);

  if (loading) {
    return (
      <div className="main-content">
        <div className="skeleton" style={{ height: 200, borderRadius: 'var(--radius-lg)', marginBottom: 'var(--space-6)' }} />
        <div className="grid grid-cols-2 gap-6">
          <div className="skeleton" style={{ height: 300, borderRadius: 'var(--radius-lg)' }} />
          <div className="skeleton" style={{ height: 300, borderRadius: 'var(--radius-lg)' }} />
        </div>
      </div>
    );
  }

  const histo = data?.score_distribution || [];
  const funnel = data?.funnel || {};
  const skillsGap = data?.skills_gap || [];
  const topCandidates = data?.top_candidates || [];

  const maxHisto = Math.max(...histo.map(x => x.count), 1);

  return (
    <div className="main-content">
      <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-8)' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.03em' }}>Recruitment Analytics</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>Real-time hiring metrics and AI scoring distribution.</p>
        </div>
      </div>

      {/* KPI Row */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(6, 1fr)', gap: 'var(--space-4)', marginBottom: 'var(--space-8)' }}>
        <div className="card" style={{ padding: 'var(--space-5)' }}>
          <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-muted)' }}>Total Active Jobs</span>
          <div style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.04em', marginTop: 4 }}>{data?.total_jobs || 0}</div>
        </div>
        <div className="card" style={{ padding: 'var(--space-5)' }}>
          <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-muted)' }}>Total Applicants</span>
          <div style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.04em', marginTop: 4 }}>{data?.total_candidates || 0}</div>
        </div>
        <div className="card" style={{ padding: 'var(--space-5)' }}>
          <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-muted)' }}>Avg Match Score</span>
          <div style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.04em', marginTop: 4, color: 'var(--green)' }}>
            {Math.round((data?.avg_score || 0) * 100)}%
          </div>
        </div>
        <div className="card" style={{ padding: 'var(--space-5)' }}>
          <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-muted)' }}>Shortlisted</span>
          <div style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.04em', marginTop: 4, color: 'var(--accent)' }}>
            {data?.shortlisted_count || 0}
          </div>
        </div>
        <div className="card" style={{ padding: 'var(--space-5)' }}>
          <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-muted)' }}>Pass-Through Rate</span>
          <div style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.04em', marginTop: 4, color: 'var(--purple, #9b59b6)' }}>
            {data?.pass_through_rate || 0}%
          </div>
        </div>
        <div className="card" style={{ padding: 'var(--space-5)' }}>
          <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-muted)' }}>Time-to-Hire (Avg)</span>
          <div style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.04em', marginTop: 4, color: 'var(--blue, #3498db)' }}>
            {data?.time_to_hire_days || 0}d
          </div>
        </div>
      </div>

      {/* Grid Row 1: Score Distribution + Funnel */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-6)', marginBottom: 'var(--space-6)' }}>
        <div className="card" style={{ padding: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 'var(--space-4)' }}>Candidate Score Distribution</h3>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, height: 180, paddingTop: 20 }}>
            {histo.map((b, i) => {
              const pct = (b.count / maxHisto) * 100;
              return (
                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent)', marginBottom: 4 }}>{b.count}</span>
                  <div style={{ width: '100%', height: `${pct}%`, background: 'var(--accent)', borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0', minHeight: 4 }} />
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>{b.range}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="card" style={{ padding: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 'var(--space-4)' }}>Hiring Pipeline Funnel</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {Object.entries({
              applied: data?.total_candidates || 0,
              shortlisted: data?.shortlisted_count || 0,
              hired: data?.hired_count || 0
            }).map(([k, v]) => (
              <div key={k}>
                <div className="flex justify-between text-sm" style={{ marginBottom: 4 }}>
                  <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{k}</span>
                  <span className="font-mono">{v}</span>
                </div>
                <ProgressBar value={(data?.total_candidates || 1) ? v / (data?.total_candidates || 1) : 0} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Grid Row 2: Top Candidates + Skills Gap */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-6)' }}>
        <div className="card" style={{ padding: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 'var(--space-4)' }}>Top Ranked Candidates</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {topCandidates.map(c => (
              <div key={c.id} className="flex items-center justify-between" style={{ padding: '8px 12px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)' }}>
                <div>
                  <p style={{ fontWeight: 600, fontSize: 13.5 }}>{c.name}</p>
                  <p style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>Job: {c.job_title}</p>
                </div>
                <span className={`badge ${scoreBadge(c.overall_score)}`} style={{ fontWeight: 700 }}>
                  {Math.round(c.overall_score * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ padding: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 'var(--space-4)' }}>Skills Gap Analysis Across Pool</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {skillsGap.map(s => (
              <div key={s.skill} className="flex items-center justify-between" style={{ padding: '8px 12px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)' }}>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{s.skill}</span>
                <span style={{ fontSize: 12, color: 'var(--red)', fontWeight: 600 }}>Missing in {Math.round((s.missing_count / (data?.total_candidates || 1)) * 100)}% of applicants</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────
//  NEW PAGES (Settings, Talent Pool)
// ─────────────────────────────────────────

function SettingsPage() {
  return (
    <div className="main-content">
      <div className="page-header">
        <div className="page-header-title">
          <h1>Workspace Settings</h1>
          <p>Manage your enterprise preferences, integrations, and ATS defaults.</p>
        </div>
      </div>
      <div className="card" style={{ padding: 'var(--space-6)' }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 'var(--space-4)' }}>General Settings</h3>
        <p style={{ color: 'var(--text-muted)' }}>Organization details and billing configuration.</p>
        <div style={{ marginTop: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <div className="form-group">
            <label className="form-label">Company Name</label>
            <input className="input" defaultValue="Aero Corp" />
          </div>
          <button className="btn btn-primary" style={{ width: 'max-content' }}>Save Changes</button>
        </div>
      </div>
    </div>
  );
}

function TalentPool() {
  return (
    <div className="main-content">
      <div className="page-header">
        <div className="page-header-title">
          <h1>Talent Pool</h1>
          <p>Search and discover passive candidates across all active and closed pipelines.</p>
        </div>
        <button className="btn btn-primary"><Users size={14} /> Import Candidates</button>
      </div>
      <div className="card" style={{ padding: 'var(--space-6)', minHeight: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <Search size={32} style={{ margin: '0 auto var(--space-4)', opacity: 0.5 }} />
          <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>No candidates in pool yet</p>
          <p style={{ fontSize: 13, marginTop: 4 }}>Candidates will appear here once they are added to a job pipeline.</p>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────
//  ABOUT / HOW IT WORKS PAGE
// ─────────────────────────────────────────

function About() {
  return (
    <div className="main-content">
      <div style={{ marginBottom: 'var(--space-10)' }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.04em', marginBottom: 8 }}>How Aero ATS Works</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 15 }}>Architecture, AI processing pipeline, and matching algorithm breakdown.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>
        {/* Step 1 */}
        <div className="card" style={{ padding: 'var(--space-6)' }}>
          <div className="flex items-center gap-3" style={{ marginBottom: 'var(--space-4)' }}>
            <div style={{ width: 32, height: 32, borderRadius: 'var(--radius-md)', background: 'var(--accent-dim)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>1</div>
            <h3 style={{ fontSize: 17, fontWeight: 700 }}>Multi-Format Resume Parsing</h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.6 }}>
            Resumes in PDF, DOCX, or TXT formats are parsed into structured JSON schemas extracting contact info, work experience history, education, skills, and certifications.
          </p>
        </div>

        {/* Step 2 */}
        <div className="card" style={{ padding: 'var(--space-6)' }}>
          <div className="flex items-center gap-3" style={{ marginBottom: 'var(--space-4)' }}>
            <div style={{ width: 32, height: 32, borderRadius: 'var(--radius-md)', background: 'var(--blue-dim)', color: 'var(--blue)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>2</div>
            <h3 style={{ fontSize: 17, fontWeight: 700 }}>Hybrid Embedding & TF-IDF Semantic Matching</h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.6 }}>
            Combines dense neural embeddings with TF-IDF n-gram vectors to calculate deep context similarity between the candidate profile and job description requirements.
          </p>
        </div>

        {/* Step 3 */}
        <div className="card" style={{ padding: 'var(--space-6)' }}>
          <div className="flex items-center gap-3" style={{ marginBottom: 'var(--space-4)' }}>
            <div style={{ width: 32, height: 32, borderRadius: 'var(--radius-md)', background: 'var(--green-dim)', color: 'var(--green)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>3</div>
            <h3 style={{ fontSize: 17, fontWeight: 700 }}>4-Dimension Scoring Breakdown</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-4)', marginTop: 'var(--space-4)' }}>
            {[
              ['Semantic Match', '35% Weight', 'Deep contextual relevance'],
              ['Skill Overlap', '35% Weight', 'Required tech stack overlap'],
              ['Experience Fit', '20% Weight', 'Years & senior role fit'],
              ['Education Fit', '10% Weight', 'Degree requirement check']
            ].map((row, i) => (
              <div key={i} style={{ padding: 'var(--space-4)', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)' }}>
                <p style={{ fontWeight: 700, fontSize: 13 }}>{row[0]}</p>
                <p style={{ fontSize: 12, color: 'var(--accent)', fontWeight: 600, margin: '4px 0' }}>{row[1]}</p>
                <p style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>{row[2]}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────
//  APP ROOT
// ─────────────────────────────────────────

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('ats_token'));
  const [role, setRole] = useState(() => localStorage.getItem('ats_role'));

  useEffect(() => {
    const handleUnauth = () => {
      localStorage.removeItem('ats_token');
      localStorage.removeItem('ats_role');
      setToken(null);
      setRole(null);
    };
    window.addEventListener('ats:unauthorized', handleUnauth);
    return () => window.removeEventListener('ats:unauthorized', handleUnauth);
  }, []);

  const login = (jwt, userRole) => { 
    localStorage.setItem('ats_token', jwt); 
    localStorage.setItem('ats_role', userRole); 
    setToken(jwt); 
    setRole(userRole);
  };
  const logout = () => { 
    localStorage.removeItem('ats_token'); 
    localStorage.removeItem('ats_role'); 
    setToken(null); 
    setRole(null);
  };

  return (
    <ToastProvider>
      <Router>
        {!token ? (
          <Routes><Route path="*" element={<Login onLogin={login} />} /></Routes>
        ) : (
          <div className="app-shell">
            <Sidebar onLogout={logout} role={role} />
            <Routes>
              <Route path="/"            element={<Dashboard token={token} role={role} />} />
              <Route path="/jobs/:jobId" element={<JobPipeline token={token} role={role} />} />
              <Route path="/analytics"   element={<Analytics token={token} />} />
              <Route path="/talent-pool" element={<TalentPool token={token} />} />
              <Route path="/settings"    element={<SettingsPage />} />
              <Route path="/about"       element={<About />} />
              <Route path="*"            element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        )}
      </Router>
    </ToastProvider>
  );
}

export default App;
