# Manual Intervention System - Tasarım Dokümanı

Bu doküman, sunum kontrol sistemine manuel müdahale desteği eklemek için tüm tasarım kararlarını içerir.

---

## 1. Genel Bakış

### Hedef

600 kişilik sunum için gözetmen müdahalesi desteği:

- Gözetmen istediği an sistemi durdurabilmeli
- Gözetmen manuel olarak slayt değiştirebilmeli
- Sistem, gözetmenin yaptığı değişikliği kabul etmeli ve uyum sağlamalı

### Kontrol Tuşları

- **M tuşu:** Sistemi durdur/devam ettir (case-insensitive, 'm' ve 'M' çalışır)
- **Sol/Sağ ok:** Manuel slayt değiştir

---

## 2. State Modeli

### ACTIVE (Yeşil)

- Varsayılan durum
- Otomatik slayt navigasyonu açık
- Tüm bileşenler çalışıyor
- Threshold geçildiğinde slayt değiştiriliyor

### PAUSED (Sarı)

- Gözetmen M tuşuna bastı
- Mikrofon ve STT çalışmaya devam ediyor
- Similarity hesaplanmıyor
- Navigasyon devre dışı
- TUI'da speech text güncelleniyor, match score donuk

### LOCKED (Kırmızı)

- Gözetmen ok tuşuyla manuel slayt değiştirdi (ACTIVE'den)
- Veya PAUSED'da slide değiştirip M ile devam etti
- Similarity hesaplanıyor (konsensüs için)
- Navigasyon devre dışı
- Konsensüs oluşunca ACTIVE'e döner

---

## 3. State Geçiş Tablosu

| #   | Mevcut State             | Event       | Yeni State | Slide | Açıklama                      |
| --- | ------------------------ | ----------- | ---------- | ----- | ----------------------------- |
| 1   | ACTIVE                   | M           | PAUSED     | =     | Sistem durduruldu             |
| 2   | ACTIVE                   | ←           | LOCKED     | -1    | Manuel geri, konsensüs bekle  |
| 3   | ACTIVE                   | →           | LOCKED     | +1    | Manuel ileri, konsensüs bekle |
| 4   | ACTIVE                   | Threshold ✓ | ACTIVE     | ±     | Otomatik navigasyon           |
| 5   | PAUSED (slide değişmedi) | M           | ACTIVE     | =     | Devam et                      |
| 6   | PAUSED (slide değişti)   | M           | LOCKED     | =     | Konsensüs bekle               |
| 7   | PAUSED                   | ←           | PAUSED     | -1    | Manuel geri, hala durmuş      |
| 8   | PAUSED                   | →           | PAUSED     | +1    | Manuel ileri, hala durmuş     |
| 9   | LOCKED                   | M           | PAUSED     | =     | Acil çıkış                    |
| 10  | LOCKED                   | ←           | LOCKED     | -1    | Yeni hedef belirle            |
| 11  | LOCKED                   | →           | LOCKED     | +1    | Yeni hedef belirle            |
| 12  | LOCKED                   | Konsensüs ✓ | ACTIVE     | =     | Kilidi aç, devam              |
| 13  | LOCKED                   | Konsensüs ✗ | LOCKED     | =     | Bekle                         |

---

## 4. Sınır Durumları

| #   | Durum                 | Event                 | Sonuç                            |
| --- | --------------------- | --------------------- | -------------------------------- |
| 14  | slide == 1            | ←                     | Slide değişmez, state aynı kalır |
| 15  | slide == son          | →                     | Slide değişmez, state aynı kalır |
| 16  | Herhangi              | Sistem ok simüle etti | YOK SAY (echo prevention)        |
| 17  | shutdown_flag == True | M veya ok             | YOK SAY                          |
| 18  | LOCKED                | ←←← (üç kere)         | slide -3, her biri ayrı işlenir  |

---

## 5. State Diyagramı

```
                         ┌──────────────────────────────────────────┐
                         │              BAŞLANGIÇ                   │
                         └────────────────────┬─────────────────────┘
                                              ▼
                                      ┌───────────────┐
           ┌─────────── M ───────────►│    PAUSED     │◄─────── M ──────────┐
           │                          │   (Sarı)      │                     │
           │                          └───────┬───────┘                     │
           │                             ← / →│(slide değişir)              │
           │                                  ▼                             │
           │                          ┌───────────────┐                     │
     ┌─────┴─────┐                    │    PAUSED     │                     │
     │  ACTIVE   │◄────── M ──────────┤(slide değişti)├───── M ─────────────┤
     │  (Yeşil)  │                    └───────────────┘                     │
     └─────┬─────┘                           │                              │
           │                                 │                              │
        ← / →                                M                              │
           │                                 ▼                              │
           ▼                          ┌───────────────┐                     │
     ┌───────────────┐                │    LOCKED     │─────── M ───────────┘
     │    LOCKED     │◄───────────────┤  (Kırmızı)    │
     │  (Kırmızı)    │                └───────────────┘
     └───────┬───────┘
             │
        Konsensüs ✓
             │
             ▼
     ┌───────────────┐
     │    ACTIVE     │
     │   (Yeşil)     │
     └───────────────┘
```

---

## 6. Bileşen Davranışları (State'e Göre)

### ACTIVE

| Bileşen    | Durum          |
| ---------- | -------------- |
| Mikrofon   | ✅ Çalışır     |
| STT        | ✅ Çalışır     |
| Queue      | ✅ Doluyor     |
| Navigator  | ✅ Çalışır     |
| Similarity | ✅ Hesaplanır  |
| Navigation | ✅ Ok gönderir |
| TUI Speech | ✅ Güncel      |
| TUI Match  | ✅ Güncel      |

### PAUSED

| Bileşen    | Durum                            |
| ---------- | -------------------------------- |
| Mikrofon   | ✅ Çalışır                       |
| STT        | ✅ Çalışır                       |
| Queue      | ✅ Doluyor                       |
| Navigator  | ⏸️ Queue'dan alır, TUI günceller |
| Similarity | ❌ Hesaplanmaz                   |
| Navigation | ❌ Ok göndermez                  |
| TUI Speech | ✅ Güncel                        |
| TUI Match  | ❄️ Donuk (son değer)             |

### LOCKED

| Bileşen    | Durum                          |
| ---------- | ------------------------------ |
| Mikrofon   | ✅ Çalışır                     |
| STT        | ✅ Çalışır                     |
| Queue      | ✅ Doluyor                     |
| Navigator  | ✅ Çalışır                     |
| Similarity | ✅ Hesaplanır (konsensüs için) |
| Navigation | ❌ Ok göndermez                |
| TUI Speech | ✅ Güncel                      |
| TUI Match  | ✅ Güncel                      |

---

## 7. Konsensüs Mekanizması

### Tanım

Konsensüs = Sistemin önerdiği slayt ile gözetmenin belirlediği slaytın aynı olması.

### Koşullar

İki koşul da sağlanmalı:

1. `top_match.section == current_section` (aynı slayt)
2. `top_match.score >= SIMILARITY_THRESHOLD` (yeterli güven)

### Threshold

Aynı `SIMILARITY_THRESHOLD` kullanılır (ayrı config yok).

---

## 8. Echo Prevention

### Problem

Sistem slayt değiştirirken `pynput.Controller` ile ok tuşu simüle eder. Aynı anda `pynput.Listener` bu tuşu yakalar ve LOCKED state'e geçirebilir.

### Çözüm

Sayaç mekanizması:

1. Navigasyon yapmadan önce: `own_keypress_count += abs(slide_delta)`
2. Listener'da: Eğer `own_keypress_count > 0` ise tuşu yok say, sayacı azalt

---

## 9. slide_changed_while_paused Flag

### Amaç

PAUSED'dan M ile çıkarken doğru state'e geçmek.

### Mantık

- PAUSED'da ok basıldı → flag = True
- PAUSED + M basıldı:
  - flag == True → LOCKED
  - flag == False → ACTIVE
  - flag = False (sıfırla)

---

## 10. Özel Durumlar

### PAUSED → ACTIVE Buffer Sorunu

**Senaryo:**

1. ACTIVE, slide 14
2. M → PAUSED
3. Ok ile slide 11'e git
4. M ile devam et

**Sorun:** Buffer hala slide 14 kelimeleri içeriyor.

**Çözüm:** `slide_changed_while_paused` flag sayesinde LOCKED'a geçer, konsensüs beklenir.

### Shutdown Durumu

- `shutdown_flag` set ise tüm keyboard input'ları yok sayılır
- Listener `control()` bittiğinde durur

---

## 11. TUI Göstergeleri

| State  | Renk    | Last Action Örneği              |
| ------ | ------- | ------------------------------- |
| ACTIVE | Yeşil   | "Auto: Slide 5 → Slide 6"       |
| PAUSED | Sarı    | "System paused"                 |
| LOCKED | Kırmızı | "Locked on 11, waiting sync..." |

---

## 12. Özet Kuralları

1. **M tuşu:** ACTIVE ↔ PAUSED toggle, LOCKED'dan PAUSED'a çıkar
2. **Ok tuşları:** Slide değiştirir, ACTIVE'den LOCKED'a geçer
3. **Konsensüs:** Sadece LOCKED → ACTIVE geçişi sağlar
4. **PAUSED'da slide değişikliği:** M ile LOCKED'a geçer
5. **Echo prevention:** Sistem kaynaklı oklar yok sayılır
6. **Shutdown:** Tüm input'lar yok sayılır
7. **Sınırlar:** slide 1'de ← veya son slide'da → yok sayılır
