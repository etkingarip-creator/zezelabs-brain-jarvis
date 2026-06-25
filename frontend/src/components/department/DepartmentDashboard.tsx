import { useState, useEffect } from 'react';
import { Activity, Users, Clock, AlertCircle, FileText, X } from 'lucide-react';
import KPICard from './KPICard';
import AgentCard from './AgentCard';
import LiveFeed from './LiveFeed';
import MorphicCanvas from './MorphicCanvas';
import { API_BASE } from '../../lib/config';
import type { FloorMeta } from '../../types/department';
import type { DepartmentStatus } from '../../types/department';

interface DepartmentDashboardProps {
  floor: FloorMeta;
  dept?: DepartmentStatus;
}

interface DeptDetails {
  name: string;
  status: string;
  kpis: {
    active_agents: number;
    success_rate: number;
    queue_depth: number;
    avg_response_time: string;
  };
  agents: Array<{
    name: string;
    status: string;
    tasks_completed: number;
    last_active: string;
  }>;
  recent_workflows: Array<{
    id: string;
    action: string;
    status: string;
    timestamp: string;
  }>;
}

export default function DepartmentDashboard({ floor, dept }: DepartmentDashboardProps) {
  const [details, setDetails] = useState<DeptDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [reports, setReports] = useState<any[]>([]);
  const [loadingReports, setLoadingReports] = useState(false);
  const [selectedReport, setSelectedReport] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    const fetchDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/api/ecosystem/departments/${floor.departmentId}/details`);
        if (!res.ok) throw new Error('Veri alınamadı');
        const data = await res.json();
        setDetails(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Bilinmeyen hata');
        // Fallback to dept data
        if (dept) {
          setDetails({
            name: floor.departmentId,
            status: dept.status,
            kpis: {
              active_agents: dept.agents_list?.length || 0,
              success_rate: 98.5,
              queue_depth: dept.queue_depth || 0,
              avg_response_time: '1.2s',
            },
            agents: (dept.agents_list || []).map(a => ({
              name: a.name,
              status: a.status,
              tasks_completed: 0,
              last_active: ''
            })),
            recent_workflows: [],
          });
        }
      } finally {
        setLoading(false);
      }
    };

    const fetchReports = async () => {
      setLoadingReports(true);
      try {
        const res = await fetch(`${API_BASE}/api/ecosystem/departments/${floor.departmentId}/reports`);
        if (!res.ok) throw new Error('Raporlar alınamadı');
        const data = await res.json();
        setReports(data.reports || []);
      } catch (err) {
        console.warn('Failed to fetch department reports:', err);
        setReports([]);
      } finally {
        setLoadingReports(false);
      }
    };

    fetchDetails();
    fetchReports();
  }, [floor.departmentId, dept]);

  const handleOpenReport = async (taskId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/ecosystem/departments/${floor.departmentId}/reports/${taskId}`);
      if (!res.ok) throw new Error('Rapor detayları alınamadı');
      const data = await res.json();
      setSelectedReport(data);
      setIsModalOpen(true);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Hata oluştu');
    }
  };

  const statusConfig = {
    active: { color: 'text-green-400', bg: 'bg-green-500', label: 'Aktif' },
    idle: { color: 'text-blue-400', bg: 'bg-blue-500', label: 'Beklemede' },
    error: { color: 'text-red-400', bg: 'bg-red-500', label: 'Hata' },
    unknown: { color: 'text-slate-400', bg: 'bg-slate-500', label: 'Bilinmiyor' },
  };

  const status = statusConfig[(details?.status || 'unknown') as keyof typeof statusConfig] || statusConfig.unknown;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">{floor.name}</h2>
          <p className="text-xs text-slate-500">{floor.departmentId} · Kat {floor.id}</p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${status.color} border-current/20`}>
          <div className={`w-2 h-2 rounded-full ${status.bg}`} />
          <span className={`text-sm font-medium ${status.color}`}>{status.label}</span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-3">
        <KPICard
          title="Aktif Ajan"
          value={details?.kpis.active_agents ?? dept?.agents_list?.length ?? 0}
          color="green"
        />
        <KPICard
          title="Başarı Oranı"
          value={`${details?.kpis.success_rate ?? 98.5}%`}
          trend="up"
          color="blue"
        />
        <KPICard
          title="Kuyruk"
          value={details?.kpis.queue_depth ?? dept?.queue_depth ?? 0}
          color={details?.kpis.queue_depth ? 'yellow' : 'blue'}
        />
      </div>

      {/* Morphic Canvas Card */}
      <MorphicCanvas departmentId={floor.departmentId} />

      {/* Agent Grid */}
      <div>
        <h3 className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2">
          <Users className="w-4 h-4" />
          Aktif Ajanlar
        </h3>
        {loading ? (
          <div className="grid grid-cols-2 gap-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-slate-800/50 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : details?.agents && details.agents.length > 0 ? (
          <div className="grid grid-cols-2 gap-2">
            {details.agents.map((agent, i) => (
              <AgentCard key={i} agent={agent} />
            ))}
          </div>
        ) : dept?.agents_list && dept.agents_list.length > 0 ? (
          <div className="grid grid-cols-2 gap-2">
            {dept.agents_list.map((agent, i) => (
              <AgentCard key={i} agent={agent} />
            ))}
          </div>
        ) : (
          <div className="text-center py-4 text-slate-500 text-sm">
            Aktif ajan yok
          </div>
        )}
      </div>

      {/* Live Feed */}
      <div>
        <h3 className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2">
          <Activity className="w-4 h-4" />
          Son İşlemler
        </h3>
        <LiveFeed workflows={details?.recent_workflows || []} loading={loading} />
      </div>

      {/* Agent Reports Section */}
      <div>
        <h3 className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2">
          <FileText className="w-4 h-4 text-cyan-400" />
          Ajan Raporları
        </h3>
        {loadingReports ? (
          <div className="space-y-2">
            {[1, 2].map((i) => (
              <div key={i} className="h-10 bg-slate-800/50 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : reports.length > 0 ? (
          <div className="max-h-56 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {reports.map((rep) => (
              <div
                key={rep.task_id}
                className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/20 border border-slate-800 hover:border-cyan-500/30 transition-all group"
              >
                <div className="min-w-0 flex-1 mr-3">
                  <p className="text-xs font-medium text-slate-200 truncate group-hover:text-cyan-400 transition-colors">
                    {rep.query || 'Görev Çıktısı'}
                  </p>
                  <p className="text-[10px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                    <span>ID: {rep.task_id.slice(0, 8)}...</span>
                    <span>•</span>
                    <span>{rep.timestamp ? new Date(rep.timestamp).toLocaleString('tr-TR') : 'Bilinmeyen Zaman'}</span>
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleOpenReport(rep.task_id)}
                  className="px-2.5 py-0.5 text-[10px] font-semibold bg-cyan-950/40 hover:bg-cyan-900 border border-cyan-800/50 hover:border-cyan-700 rounded text-cyan-300 transition-all shrink-0"
                >
                  Oku
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-4 text-slate-500 text-xs">
            Bu departmana ait henüz bir rapor bulunmuyor.
          </div>
        )}
      </div>

      {/* Error State */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-950/30 border border-red-500/30 text-sm text-red-200">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Report Details Modal */}
      {isModalOpen && selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-800 p-4 shrink-0 bg-slate-900/90 bg-slate-900/90">
              <div className="min-w-0">
                <h3 className="text-sm font-semibold text-slate-100 truncate">
                  Rapor Detayı
                </h3>
                <p className="text-[10px] text-slate-500 truncate mt-0.5">
                  Task ID: {selectedReport.task_id} · {selectedReport.timestamp ? new Date(selectedReport.timestamp).toLocaleString('tr-TR') : ''}
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setIsModalOpen(false);
                  setSelectedReport(null);
                }}
                className="p-1 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700/50"
                aria-label="Kapat"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
              <div>
                <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Kullanıcı Talebi</h4>
                <p className="text-xs text-slate-300 mt-1 bg-slate-950/40 p-3 rounded-lg border border-slate-800">
                  {selectedReport.query || 'Talep detayı belirtilmemiş.'}
                </p>
              </div>
              
              <div>
                <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Rapor Çıktısı</h4>
                <div className="text-xs text-slate-300 bg-slate-950/40 p-4 rounded-lg border border-slate-800 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto custom-scrollbar font-mono">
                  {selectedReport.output || 'Rapor çıktısı bulunmuyor.'}
                </div>
              </div>
              
              <div className="flex gap-4 text-[10px] text-slate-500 border-t border-slate-800 pt-3 flex-wrap">
                <div>
                  <span>Departman:</span> <span className="text-cyan-400 font-semibold">{selectedReport.department}</span>
                </div>
                <div>
                  <span>Durum:</span> <span className="text-emerald-400 font-semibold">{selectedReport.status}</span>
                </div>
                {selectedReport.trace_id && (
                  <div className="truncate max-w-[200px]">
                    <span>Trace ID:</span> <span className="text-slate-400 font-mono">{selectedReport.trace_id}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
