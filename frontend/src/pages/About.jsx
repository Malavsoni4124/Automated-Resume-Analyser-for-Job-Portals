import React, { useState, useEffect, useCallback, useRef } from 'react';
import { NavLink, useNavigate, useParams, Link } from 'react-router-dom';
import * as LucideIcons from 'lucide-react';
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
import { api, scoreColor, scoreBadge, progressCls, STATUS_CONFIG } from '../utils/helpers';
import { useToast } from '../context/ToastContext';

import Modal from '../components/Modal';
import ProgressBar from '../components/ProgressBar';
import EditJobModal from '../components/EditJobModal';
import CompareModal from '../components/CompareModal';
import CopilotChat from '../components/CopilotChat';
import CandidatePanel from '../components/CandidatePanel';

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

export default About;
