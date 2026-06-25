import React, { useState, useEffect } from 'react';
import { Settings, Sliders, Volume2, Database, ShieldAlert, Check } from 'lucide-react';
import { API_BASE } from '../lib/config';
import { AVAILABLE_MODELS, isActiveModel } from '../lib/models';
import { useJarvisConnection } from '../hooks/useJarvisConnection';

interface Props {
  voiceEnabled: boolean;
  onToggleVoice: () => void;
}

export default function SettingsPanel({ voiceEnabled, onToggleVoice }: Props) {
  const jarvis = useJarvisConnection();
  const serverModel = jarvis.brainStatus.model || 'gemma_2b';
  // Ham sunucu modelini select için bir model ID'sine çöz (yanlış seçili gösterimi önler)
  const activeModelId = AVAILABLE_MODELS.find(m => isActiveModel(serverModel, m.id))?.id || 'antigravity';

  const [voiceGender, setVoiceGender] = useState(() => localStorage.getItem('zom_settings_voice_gender') || 'robot');
  const [telemetryDelay, setTelemetryDelay] = useState(() => localStorage.getItem('zom_settings_telemetry_delay') || '3');
  const [clearing, setClearing] = useState(false);
  const [clearSuccess, setClearSuccess] = useState(false);

  useEffect(() => {
    localStorage.setItem('zom_settings_voice_gender', voiceGender);
  }, [voiceGender]);

  useEffect(() => {
    localStorage.setItem('zom_settings_telemetry_delay', telemetryDelay);
  }, [telemetryDelay]);

  const [clearError, setClearError] = useState(false);
  const handleClearCache = async () => {
    setClearing(true);
    setClearSuccess(false);
    setClearError(false);
    try {
      const res = await fetch(`${API_BASE}/api/ecosystem/clear-cache`, { method: 'POST' });
      const data = res.ok ? await res.json() : null;
      // Sadece backend gerçekten başardıysa başarı göster (sahte başarı yok)
      if (data?.success) {
        setClearSuccess(true);
        setTimeout(() => setClearSuccess(false), 2000);
      } else {
        setClearError(true);
        setTimeout(() => setClearError(false), 2500);
      }
    } catch {
      setClearError(true);
      setTimeout(() => setClearError(false), 2500);
    } finally {
      setClearing(false);
    }
  };

  return (
    <div 
      className="w-full max-w-xl p-6 mx-auto animate-fade-in-up"
      style={{ fontFamily: "'Inter', sans-serif", color: '#e8ecf4' }}
    >
      <div 
        className="rounded-2xl p-6 border space-y-6"
        style={{
          background: 'rgba(22, 29, 46, 0.52)',
          borderColor: 'rgba(255, 255, 255, 0.07)',
          backdropFilter: 'blur(18px)',
          WebkitBackdropFilter: 'blur(18px)',
        }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 pb-4 border-b border-white/5">
          <Settings className="w-5 h-5 text-[#58e5c9]" />
          <div>
            <h2 
              className="font-semibold"
              style={{ 
                fontFamily: "'Space Grotesk', sans-serif", 
                fontSize: '0.94rem', 
                letterSpacing: '0.06em', 
                textTransform: 'uppercase', 
                color: '#e8ecf4' 
              }}
            >
              Holding Yönetim Ayarları
            </h2>
            <p 
              className="mono mt-0.5"
              style={{ 
                fontFamily: "'JetBrains Mono', monospace", 
                fontSize: '0.72rem', 
                letterSpacing: '0.14em', 
                textTransform: 'uppercase', 
                color: '#6e7893' 
              }}
            >
              CORE SYSTEM CONFIGURATION
            </p>
          </div>
        </div>

        {/* 1. Yapay Zeka Modeli */}
        <div className="space-y-2.5">
          <label 
            className="font-semibold flex items-center gap-1.5"
            style={{ fontSize: '0.82rem', color: '#e8ecf4' }}
          >
            <Sliders className="w-4 h-4 text-[#58e5c9]" />
            Aktif Yapay Zeka Modeli
          </label>
          <select
            value={activeModelId}
            onChange={(e) => {
              const val = e.target.value;
              jarvis.sendWsControl('model_change', val);
            }}
            className="w-full border outline-none py-2 px-3 focus:border-[#9d7bff] transition-all"
            style={{
              background: 'rgba(10, 14, 26, 0.6)',
              borderColor: 'rgba(255, 255, 255, 0.16)',
              borderRadius: '10px',
              color: '#e8ecf4',
              fontSize: '0.86rem'
            }}
          >
            {AVAILABLE_MODELS.map(m => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </select>
          <p className="text-[10px] text-slate-500 font-mono">
            Kritik işlemler ve kodlama talepleri için global modeller önerilir.
          </p>
        </div>

        {/* 2. Ses Desteği ve Konuşma */}
        <div className="space-y-3 pt-2">
          <label 
            className="font-semibold flex items-center gap-1.5"
            style={{ fontSize: '0.82rem', color: '#e8ecf4' }}
          >
            <Volume2 className="w-4 h-4 text-[#58e5c9]" />
            Sesli Yanıt & Sentezleyici
          </label>
          
          <div 
            className="flex items-center justify-between p-3 rounded-xl border"
            style={{
              background: 'rgba(255, 255, 255, 0.01)',
              borderColor: 'rgba(255, 255, 255, 0.07)'
            }}
          >
            <span className="text-xs text-slate-300">Sesli Yanıt Özelliği</span>
            <button
              type="button"
              onClick={onToggleVoice}
              className="px-3.5 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer"
              style={{
                background: voiceEnabled ? 'rgba(88, 229, 201, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                borderColor: voiceEnabled ? '#58e5c9' : 'rgba(255, 255, 255, 0.07)',
                color: voiceEnabled ? '#58e5c9' : '#9aa4bd',
              }}
            >
              {voiceEnabled ? 'AÇIK' : 'KAPALI'}
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'male', label: 'Erkek Sesi' },
              { id: 'female', label: 'Kadın Sesi' },
              { id: 'robot', label: 'Robotik Ton' },
            ].map((voice) => (
              <button
                key={voice.id}
                type="button"
                onClick={() => setVoiceGender(voice.id)}
                className="py-2.5 rounded-lg text-xs font-medium border transition-all cursor-pointer"
                style={{
                  background: voiceGender === voice.id ? 'rgba(88, 229, 201, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                  borderColor: voiceGender === voice.id ? '#58e5c9' : 'rgba(255, 255, 255, 0.07)',
                  color: voiceGender === voice.id ? '#58e5c9' : '#9aa4bd',
                }}
              >
                {voice.label}
              </button>
            ))}
          </div>
        </div>

        {/* 3. Telemetri Sıklığı */}
        <div className="space-y-3 pt-2">
          <label 
            className="font-semibold flex items-center gap-1.5"
            style={{ fontSize: '0.82rem', color: '#e8ecf4' }}
          >
            <Database className="w-4 h-4 text-[#58e5c9]" />
            Canlı Telemetri Sıklığı
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { val: '1', label: '1 Saniye' },
              { val: '3', label: '3 Saniye' },
              { val: '5', label: '5 Saniye' },
            ].map((t) => (
              <button
                key={t.val}
                type="button"
                onClick={() => setTelemetryDelay(t.val)}
                className="py-2 rounded-lg text-xs font-medium border transition-all cursor-pointer"
                style={{
                  background: telemetryDelay === t.val ? 'rgba(88, 229, 201, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                  borderColor: telemetryDelay === t.val ? '#58e5c9' : 'rgba(255, 255, 255, 0.07)',
                  color: telemetryDelay === t.val ? '#58e5c9' : '#9aa4bd',
                }}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* 4. Geliştirici Seçenekleri */}
        <div className="space-y-3 pt-4 border-t border-white/5">
          <label 
            className="font-semibold flex items-center gap-1.5"
            style={{ fontSize: '0.82rem', color: '#e8ecf4' }}
          >
            <ShieldAlert className="w-4 h-4 text-rose-500" />
            Geliştirici Seçenekleri
          </label>

          <div 
            className="flex items-center justify-between p-3 rounded-xl border"
            style={{
              background: 'rgba(255, 255, 255, 0.01)',
              borderColor: 'rgba(255, 255, 255, 0.07)'
            }}
          >
            <div>
              <span className="block text-xs text-slate-300 font-semibold">SQLite FTS5 Bellek Ön Belleği</span>
              <span className="text-[10px] text-slate-500 block font-mono">RAG arama ön belleğini sıfırlar</span>
            </div>
            <button
              type="button"
              onClick={handleClearCache}
              disabled={clearing}
              className="px-3.5 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer"
              style={{
                background: clearSuccess
                  ? 'rgba(74, 222, 128, 0.1)'
                  : clearing
                  ? 'rgba(255, 255, 255, 0.03)'
                  : 'rgba(248, 113, 113, 0.05)',
                borderColor: clearSuccess
                  ? '#4ade80'
                  : clearing
                  ? 'rgba(255, 255, 255, 0.16)'
                  : '#f87171',
                color: clearSuccess ? '#4ade80' : clearing ? '#9aa4bd' : '#f87171',
              }}
            >
              {clearing ? (
                'Temizleniyor…'
              ) : clearSuccess ? (
                'Temizlendi ✓'
              ) : clearError ? (
                'Başarısız ✕'
              ) : (
                'Belleği Temizle'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
