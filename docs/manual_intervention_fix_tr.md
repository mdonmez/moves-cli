# Manuel Müdahale & Senkronizasyon Stratejisi

**Tarih:** 19.12.2025
**Durum:** Onaylanmış Tasarım
**Bağlam:** Sunum Kontrol Sistemi

## 1. Problemin Tanımı

Bir gözetmen manuel olarak müdahale ettiğinde (örneğin klavye ile slayt değiştirdiğinde), sistemin Konuşmadan Metne (STT) belleği (buffer) genellikle _önceki_ slayttan kalan kelimeleri barındırır. Bu "bayat buffer", sistemin hemen eski slayda geri dönme komutu vermesine ve gözetmenin eylemiyle çatışmasına neden olur.

### Senaryo

1.  **Bağlam:** Konuşmacı Slayt 14'te.
2.  **Eylem:** Gözetmen manuel olarak Slayt 12'ye geri dönüyor (örn. geçmiş bir konuyla ilgili soruyu yanıtlamak için).
3.  **Sistem Durumu:** `current_section` 12 olarak güncelleniyor.
4.  **Buffer Durumu:** STT buffer'ı hala Slayt 14'ten ~10 kelime içeriyor.
5.  **Çatışma:**
    - `CandidateChunkGenerator`, Slayt 12 etrafında adaylar oluşturuyor.
    - Ancak, geçiş chunk'ları (örn. 12-14 arası chunk'lar) nedeniyle, Slayt 14'ten kalan bayat kelimeler Slayt 14 için yüksek bir benzerlik skoru üretiyor.
    - **Sonuç:** Sistem gözetmeni ezerek Slayt 14'e geri dönüyor.

## 2. Kök Neden Analizi

- **Bayat Buffer:** STT buffer'ı son 12 kelimelik kayan bir penceredir. Yeni bağlamın eski kelimeleri temizlemesi zaman alır.
- **Aday Çakışması:** `CandidateChunkGenerator` uzak slaytları doğru şekilde filtrelese de (örn. Slayt 11'deyken Slayt 14'ün "saf" chunk'ları aday değildir), slaytlar arası köprü kuran "geçiş chunk'ları" (transition chunks) hala yanlış pozitiflere neden olabilir.
- **Otonom Otorite:** Sistem şu anda hesapladığı en iyi eşleşmenin her zaman "mutlak doğru" olduğunu varsayar ve gözetmenin manuel müdahalesindeki sinyali göz ardı eder.

## 3. Reddedilen Çözümler

Aşağıdaki çözümler değerlendirilmiş ve reddedilmiştir:

- **Hayalet Modu / Sistemi Devre Dışı Bırakma:** Sistemi X saniye devre dışı bırakmak. (Reddedildi: Keyfi zaman aşımları güvenilmezdir).
- **Buffer Temizleme:** Müdahale anında STT buffer'ını temizlemek. (Reddedildi: Kalibrasyon gecikmesine ve potansiyel olarak geçerli bağlamın kaybına neden olur).
- **Pencere Genişletme:** Müdahale sonrası arama penceresini genişletmek. (Reddedildi: Gerekli değil çünkü pencere zaten doğal olarak `current_section`'ı takip eder).
- **Top-N Tutarlılık Analizi:** En iyi 1. ve 2. sonuç arasındaki farkı analiz etmek. (Reddedildi: Etkisiz çünkü yanlış pozitif (Slayt 14) sonuçlarda genellikle baskındır).

## 4. Çözüm: "Sync Lock" (Senkronizasyon Kilidi)

### Temel Prensip

**"Eğer gözetmen bir konuma giderse, sistem o konumu ses verisiyle doğrulayana kadar başka bir yere gitmemelidir."**

Sistem ve gözetmen işbirlikçidir. Gözetmen müdahale ettiğinde, sistem "sürüş" modundan "doğrulama" moduna geçer.

### Mekanizma

1.  **Tetikleyici:** Manuel müdahale (klavye/API) `current_section`ı günceller.
2.  **Kilit Aktivasyonu:** Sistem `SYNC_LOCKED` durumuna girer.
    - `target_lock_section` = Yeni `current_section` (örn. Slayt 12).
3.  **Navigasyon Mantığı (`_navigator_task` içinde):**
    - Benzerlik skorlarını her zamanki gibi hesapla.
    - `top_result_section`ı (kazanan) belirle.
    - **KONTROL ET:**
      - EĞER `top_result_section` == `target_lock_section` (veya çok yakın/ardışık):
        - **KİLİDİ AÇ.** (Ses verisi Slayt 12'de olduğumuzu doğruladı).
        - Normal otonom navigasyona devam et.
      - EĞER `top_result_section` != `target_lock_section`:
        - **BEKLE.** (Navigasyon yapma).
        - Ses verisi Slayt 14 diyor ama Gözetmen bizi Slayt 12'ye koydu. Gözetmene güven. Ses verisinin yetişmesini bekle.

### Uç Durumlar ve Yönetimi

#### A. "Heyecanlı Konuşmacı" (12'den 20'ye Atlama)

- **Senaryo:** Konuşmacı Slayt 20'deki konuya atlıyor. Gözetmen manuel olarak Slayt 20'ye gidiyor.
- **Yönetim:**
  - `current_section` 20 olur.
  - `CandidateChunkGenerator` 20 etrafında ([18...22]) adaylar oluşturur.
  - Konuşmacı Slayt 20'yi okur.
  - Sistem sesi Slayt 20 adaylarıyla eşleştirir.
  - Sonuç: `top_result` (20) == `lock` (20). Kilit Aç & Devam Et. **Kusursuz çalışır.**

#### B. "Gözetmen Hatası" (Yanlış Slayt)

- **Senaryo:** Konuşmacı 14'te. Gözetmen yanlışlıkla 11'e tıkladı.
- **Yönetim:**
  - Sistem 14 için ses eşleşmesi görür.
  - Kilit 11 içindir.
  - Uyuşmazlık -> Sistem BEKLER.
  - **Sonuç:** Sistem gözetmenle savaşmaz. Gözetmenin hatasını fark edip düzeltmesine (14'e tıklamasına) izin verir.
  - **Felsefe:** "İşbirliği." Yanlış pozitifler (kullanıcıyla savaşmak), yanlış negatiflerden (beklemek) daha kötüdür.

#### C. "Kilitlenme (Deadlock)" Önleme

- **Risk:** Sistem Slayt 12 için asla iyi bir eşleşme bulamazsa ne olur (örn. çok kısa slayt, gürültü)?
- **Azaltma:** Bir `LOCK_TIMEOUT` (örn. 10 saniye) uygula. Eğer kilit X saniye içinde ses onayıyla açılmazsa, kalıcı felci önlemek için kilidi zorla aç.

## 5. Uygulama Planı

1.  **Sınıf Güncellemesi:** `PresentationController` sınıfına `self.sync_lock_active: bool` ve `self.sync_lock_target: int` ekle.
2.  **Girdi İşleyicisi:** Manuel tuşları (Sol/Sağ) işlerken `sync_lock_active = True` yap.
3.  **Navigatör Görevi:**
    - Karar döngüsü içinde `if self.sync_lock_active` kontrolü yap.
    - Mantığı uygula: `if top_match != current_section: continue (WAIT)`.
    - `else: self.sync_lock_active = False`.

## 6. Doğrulama

Bu mantık uygulandığında, çatışma senaryosunda sistemin `NAVIGATE -> 14` yerine `WAIT` döndürdüğünü doğrulamak için mevcut test senaryolarını (`tests/test_12_14_problem.py`) kullan.
