import { Play, CheckCircle, Database } from 'lucide-react';
import { useJarvisConnection } from '../../hooks/useJarvisConnection';
import { AVAILABLE_MODELS, isActiveModel } from '../../lib/models';

// Model seçim/yönetim paneli — tek kaynak (lib/models).
// Sahte indirme simülasyonu ve yanıltıcı "Ollama: Aktif" rozeti kaldırıldı;
// listelenen modeller buluttur (model_change WS kontrolü ile GERÇEK olarak değiştirilir).
export default function ModelStore() {
  const jarvis = useJarvisConnection();
  const serverModel = jarvis.brainStatus.model || '';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          Model Seçimi & Yönetimi
        </h3>
        <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full border border-slate-700">
          {AVAILABLE_MODELS.length} model
        </span>
      </div>

      <div className="space-y-2">
        {AVAILABLE_MODELS.map((model) => {
          const isActive = isActiveModel(serverModel, model.id);
          return (
            <div
              key={model.id}
              className={`p-3 rounded-xl transition-all border ${
                isActive
                  ? 'bg-cyan-950/20 border-cyan-500/40 shadow-lg shadow-cyan-500/5'
                  : 'bg-slate-900/40 border-slate-800/80 hover:border-slate-700/80'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-100 truncate">{model.label}</span>
                    <span className="px-1.5 py-0.5 rounded text-[8px] font-extrabold uppercase bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      Bulut
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                    {model.description}
                  </p>
                </div>

                <div className="shrink-0 flex items-center gap-1.5">
                  {isActive ? (
                    <span className="text-emerald-400 flex items-center gap-1 text-[10px] font-bold uppercase">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Aktif
                    </span>
                  ) : (
                    <button
                      onClick={() => jarvis.sendWsControl('model_change', model.id)}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-cyan-950/40 text-slate-400 hover:text-cyan-400 border border-slate-700 transition-all"
                      title="Bu modeli seç"
                    >
                      <Play className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3 mt-2 text-[9px] text-slate-500 font-mono">
                <span>Tür: Paylaşımlı API</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
