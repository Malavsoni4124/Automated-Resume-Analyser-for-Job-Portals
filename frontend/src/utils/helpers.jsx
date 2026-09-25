import React from 'react';
import { Clock, CheckCircle, Award, XCircle } from 'lucide-react';

export const API_URL = 'http://localhost:8000';

export async function api(path, token, opts = {}) {
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

export function scoreColor(v) {
  if (v >= 0.75) return 'var(--green)';
  if (v >= 0.50) return 'var(--amber)';
  return 'var(--red)';
}

export function scoreBadge(v) {
  if (v >= 0.75) return 'badge-green';
  if (v >= 0.50) return 'badge-amber';
  return 'badge-red';
}

export function progressCls(v) {
  if (v >= 0.75) return 'progress-high';
  if (v >= 0.50) return 'progress-med';
  return 'progress-low';
}

export const STATUS_CONFIG = {
  new: { label: 'New', cls: 'badge-muted', icon: <Clock size={11} /> },
  shortlisted: { label: 'Shortlisted', cls: 'badge-accent', icon: <CheckCircle size={11} /> },
  hired: { label: 'Hired', cls: 'badge-green', icon: <Award size={11} /> },
  rejected: { label: 'Rejected', cls: 'badge-red', icon: <XCircle size={11} /> },
};
