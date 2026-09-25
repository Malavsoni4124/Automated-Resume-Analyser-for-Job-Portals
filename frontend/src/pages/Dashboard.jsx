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

function Dashboard({ token }

export default Dashboard;
