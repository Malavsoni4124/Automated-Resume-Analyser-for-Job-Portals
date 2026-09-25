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

export default TalentPool;
