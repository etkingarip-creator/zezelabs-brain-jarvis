# ⚙️ ZezeLabs Betting: Operasyonel Matris ve Entegrasyon

## 1. Departmanlar Arası Senkronizasyon (Workflow)

### **Senaryo: Yeni Bir Bahis Türü (Örn: E-spor Turnuvası) Lansmanı**

1.  **[zeze_business]** pazar fırsatını tespit eder (Trend analizi) $\rightarrow$ **İş Planı Hazırlar.**
2.  **[zeze_compliance]** bölge regülasyonlarını kontrol eder $\rightarrow$ **Yasal Onay/Lisans Kontrolü Yapar.**
3.  **[zeze_dev]** veri sağlayıcıları ile entegrasyonu ve AI motorunu kurar $\rightarrow$ **Teknik Uygulama.**
4.  **[zeze_compliance]** son kontrolü yapar (RNG & KYC) $\rightarrow$ **Lansman Onayı.**

## 2. Risk Yönetimi Protokolü

| Risk Tipi | Tespit Yöntemi | Müdahale Birimi | Aksiyon |
| :--- | :--- | :--- | :--- |
| **Finansal (Fraud)** | Anormal bahis hacmi/pattern | `dev` + `compliance` | Hesap dondurma & Manuel inceleme |
| **Yasal (Compliance)** | Yeni regülasyon değişikliği | `compliance` | Yazılımın güncellenmesi (Compliance-as-Code) |
| **Teknik (Latency)** | Sunucu yanıt sürelerinde artış | `dev` | Otomatik ölçeklendirme (Auto-scaling) |

## 3. KPI Takip Listesi

- **LTV/CAC:** Müşteri ömrü değeri / Edinme maliyeti (Hedef: >3x).
- **GGR Margin:** Kasa kar marjı optimizasyonu.
- **System Uptime:** %99.99 erişilebilirlik.
- **KYC Pass Rate:** Kullanıcı kayıt hızı ve başarı oranı.
