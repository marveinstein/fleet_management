import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Truck,
  MapPin,
  Fuel,
  Route,
  Wrench,
  ShieldAlert,
  BarChart,
  FileText,
  Users,
  LogOut,
  Play,
  Pause,
  Plus,
  Download,
  CheckCircle,
  Search,
  Gauge,
  X,
  Menu
} from 'lucide-react';

const API_BASE = '/api';

const getAuthToken = () => localStorage.getItem('fleet_token');
const setAuthToken = (t) => t ? localStorage.setItem('fleet_token', t) : localStorage.removeItem('fleet_token');

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [liveTelemetry, setLiveTelemetry] = useState([]);
  const [maintenanceAlerts, setMaintenanceAlerts] = useState([]);
  const [toastMessage, setToastMessage] = useState(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  const fetchUserProfile = async () => {
    const token = getAuthToken();
    if (!token) {
      setIsInitialLoading(false);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/auth/me/`, {
        headers: { Authorization: `Token ${token}` },
      });
      if (res.ok) {
        const profile = await res.json();
        setCurrentUser(profile);
        if (profile.role === 'driver') setActiveTab('driver_cockpit');
      } else {
        setAuthToken(null);
        setCurrentUser(null);
      }
    } catch (e) {
      setAuthToken(null);
    } finally {
      setIsInitialLoading(false);
    }
  };

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const refreshTelemetry = useCallback(async () => {
    const token = getAuthToken();
    if (!token) return;
    try {
      const [tRes, aRes] = await Promise.all([
        fetch(`${API_BASE}/telemetry/live/`, { headers: { Authorization: `Token ${token}` } }),
        fetch(`${API_BASE}/maintenance/alerts/?status=open`, { headers: { Authorization: `Token ${token}` } })
      ]);
      if (tRes.ok) setLiveTelemetry(await tRes.json());
      if (aRes.ok) setMaintenanceAlerts(await aRes.json());
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    if (currentUser) {
      refreshTelemetry();
      const interval = setInterval(refreshTelemetry, 8000);
      return () => clearInterval(interval);
    }
  }, [currentUser, refreshTelemetry]);

  // Simulation tick
  useEffect(() => {
    let timer = null;
    if (isSimulating && currentUser) {
      timer = setInterval(async () => {
        const token = getAuthToken();
        await fetch(`${API_BASE}/telemetry/simulate-step/`, {
          method: 'POST',
          headers: { Authorization: `Token ${token}` }
        });
        refreshTelemetry();
      }, 3500);
    }
    return () => clearInterval(timer);
  }, [isSimulating, currentUser, refreshTelemetry]);

  const handleDemoLogin = async (username, password) => {
    try {
      const res = await fetch(`${API_BASE}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      if (!res.ok) throw new Error('Invalid credentials');
      const data = await res.json();
      setAuthToken(data.token);
      setCurrentUser(data.user);
      if (data.user.role === 'driver') setActiveTab('driver_cockpit');
      else setActiveTab('dashboard');
    } catch (err) {
      alert(err.message);
    }
  };

  const handleLogout = () => {
    setAuthToken(null);
    setCurrentUser(null);
    setIsSimulating(false);
  };

  if (isInitialLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950 text-white">
        <div className="animate-spin w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950 text-white">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl">
          <div className="text-center mb-6">
            <div className="inline-flex p-3 bg-indigo-600 rounded-2xl mb-2">
              <Truck className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-2xl font-bold">FleetTrack Pro</h2>
            <p className="text-sm text-slate-400">Enterprise Fleet Telematics</p>
          </div>
          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center">Quick One-Click Logins</p>
            <div className="grid grid-cols-3 gap-2">
              <button onClick={() => handleDemoLogin('admin', 'admin123')} className="p-3 bg-slate-800 hover:bg-slate-700 rounded-xl text-xs font-bold">Admin</button>
              <button onClick={() => handleDemoLogin('manager', 'manager123')} className="p-3 bg-slate-800 hover:bg-slate-700 rounded-xl text-xs font-bold">Manager</button>
              <button onClick={() => handleDemoLogin('driver1', 'driver123')} className="p-3 bg-slate-800 hover:bg-slate-700 rounded-xl text-xs font-bold">Driver</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className="hidden md:flex flex-col w-64 bg-slate-900 border-r border-slate-800 p-4 shrink-0">
        <div className="flex items-center space-x-3 px-3 py-4 mb-4 border-b border-slate-800">
          <div className="p-2.5 bg-indigo-600 text-white rounded-xl">
            <Truck className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white">FleetTrack Pro</h1>
            <p className="text-xs text-slate-400">Intelligent Telematics</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1.5 text-sm">
          {currentUser.role === 'driver' ? (
            <button onClick={() => setActiveTab('driver_cockpit')} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl bg-indigo-600 text-white font-medium">
              <Gauge className="w-5 h-5" /> Driver Cockpit
            </button>
          ) : (
            <>
              <button onClick={() => setActiveTab('dashboard')} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl ${activeTab === 'dashboard' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>
                <BarChart className="w-5 h-5" /> Overview
              </button>
              <button onClick={() => setActiveTab('live_map')} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl ${activeTab === 'live_map' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>
                <MapPin className="w-5 h-5" /> Live GPS Map
              </button>
            </>
          )}
          <button onClick={() => setActiveTab('trips')} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl ${activeTab === 'trips' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>
            <Route className="w-5 h-5" /> Trip Tickets
          </button>
          <button onClick={() => setActiveTab('fuel')} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl ${activeTab === 'fuel' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>
            <Fuel className="w-5 h-5" /> Fuel Logs
          </button>
          {currentUser.role !== 'driver' && (
            <>
              <button onClick={() => setActiveTab('maintenance')} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl ${activeTab === 'maintenance' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>
                <Wrench className="w-5 h-5" /> Maintenance ({maintenanceAlerts.length})
              </button>
              <button onClick={() => setActiveTab('analytics')} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl ${activeTab === 'analytics' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>
                <ShieldAlert className="w-5 h-5" /> Driver Analytics
              </button>
              <button onClick={() => setActiveTab('reports')} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl ${activeTab === 'reports' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>
                <FileText className="w-5 h-5" /> Monthly Reports
              </button>
            </>
          )}
        </nav>

        <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs">
          <div>
            <div className="font-bold text-white">{currentUser.username}</div>
            <div className="text-slate-500 uppercase">{currentUser.role}</div>
          </div>
          <button onClick={handleLogout} className="text-rose-400 hover:text-rose-300">
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-2xl font-bold capitalize mb-4">{activeTab.replace('_', ' ')}</h2>
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <p className="text-slate-400 text-sm">
            FleetTrack Pro is serving live telemetry over SQLite WAL mode. Switch roles or launch simulation to test real-time functionality.
          </p>
        </div>
      </main>
    </div>
  );
}

