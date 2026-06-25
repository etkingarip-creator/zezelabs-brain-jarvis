// Model kayıt defteri — TEK DOĞRULUK KAYNAĞI.
// ChatPanel, SettingsPanel, ModelStore ve chatHelpers buradan tüketir.
// Backend ID eşlemesi: backend/jarvis.py model_change handler (antigravity/glm-5.2/openrouter_free/claude_35).

export interface ModelDef {
  id: string;
  label: string;
  description: string;
  provider: 'cloud' | 'local';
}

export const AVAILABLE_MODELS: ModelDef[] = [
  {
    id: 'antigravity',
    label: 'Otomatik (Akıllı Yönlendirme)',
    description: 'Karmaşıklık skoruna göre GLM-5.2 veya OpenRouter free arasında dinamik, bütçe dostu yönlendirme.',
    provider: 'cloud',
  },
  {
    id: 'glm-5.2',
    label: 'Zenmux GLM-5.2 (Akıl Yürütme)',
    description: 'Derin kodlama, mimari analiz ve mantıksal hata ayıklama için üst düzey akıl yürütme.',
    provider: 'cloud',
  },
  {
    id: 'openrouter_free',
    label: 'OpenRouter Free Tier (Hızlı)',
    description: 'Birim test, özetleme ve basit veri işlemleri için hızlı bulut modeli.',
    provider: 'cloud',
  },
  {
    id: 'claude_35',
    label: 'Claude 3.5 Sonnet (Global)',
    description: 'Kritik kararlar ve karmaşık problem çözme için Anthropic tabanlı global model.',
    provider: 'cloud',
  },
];

// Sunucudan gelen ham model adının bir model ID'sine karşılık gelip gelmediğini çözer.
// Tek kopya — önceden ChatPanel ve ModelStore'da ayrı ayrı tekrarlanan kırılgan zincir.
export function isActiveModel(serverModel: string | undefined | null, modelId: string): boolean {
  if (!serverModel) return modelId === 'antigravity';
  const s = serverModel.toLowerCase();
  if (serverModel === modelId || s.endsWith(modelId.toLowerCase())) return true;
  switch (modelId) {
    case 'antigravity':
      return s.includes('gemma') || s.includes('antigravity');
    case 'glm-5.2':
      return s.includes('glm-5.2') || s.includes('glm_5.2') || s.includes('glm-4.5');
    case 'openrouter_free':
      return s.includes('openrouter_free') || s.includes('openrouter/free') || s.includes('free');
    case 'claude_35':
      return s.includes('claude-3.5') || s.includes('claude_35') || s.includes('claude-3-5');
    default:
      return false;
  }
}

// Aktif model etiketini döndürür (eşleşme yoksa ham değeri döner — dürüst).
export function resolveModelLabel(serverModel: string | undefined | null): string {
  const match = AVAILABLE_MODELS.find(m => isActiveModel(serverModel, m.id));
  return match?.label || serverModel || 'Bilinmeyen Model';
}
