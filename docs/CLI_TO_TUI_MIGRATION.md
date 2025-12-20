# CLI to TUI Migration - Konsept Dokümanı

Bu doküman, presentation controller'ın CLI çıktılarından (typer.echo) Rich tabanlı gerçek zamanlı TUI'ye dönüştürülmesi için gereken mantığı ve konseptleri açıklar.

---

## 1. Mevcut Durum vs Hedef

### Mevcut Durum (CLI)

- Her similarity hesaplamasında `typer.echo()` ile yeni satır yazılıyor
- Terminal sürekli kayıyor
- Hangi durumda olduğunu anlamak zor
- Profesyonel görünmüyor

### Hedef (TUI)

- Sabit bir panel, yerinde güncelleniyor
- Renkli durum göstergeleri (ACTIVE=yeşil, PAUSED=sarı, LOCKED=kırmızı)
- Input ve Match metinleri ayrı satırlarda
- Son yapılan aksiyonun gösterildiği footer
- Profesyonel ve izlenebilir görünüm

---

## 2. Mimari Değişiklikler

### 2.1 Yeni TUI Class'ı

**Amaç:** Tüm görsel state'i tek bir yerde tutmak, render mantığını ayırmak.

**Tutulacak state'ler:**

- `current_slide` - Şu anki slayt numarası
- `total_slides` - Toplam slayt sayısı
- `status` - ACTIVE / PAUSED / LOCKED
- `match_score` - Benzerlik yüzdesi (0-100)
- `speech_text` - Kullanıcının söylediği metin
- `match_text` - Eşleşen chunk metni
- `last_action` - Son yapılan işlemin açıklaması
- `speaker_label` - Konuşmacı adı ve ID'si

**Render metodu:**

- Rich Panel döndürür
- Status'a göre renk seçer
- Match score'a göre renk seçer (yüksek=yeşil, düşük=kırmızı)
- Metinleri terminal genişliğine göre truncate eder

### 2.2 Controller'a TUI Entegrasyonu

**`__init__` değişiklikleri:**

- Yeni parametre: `speaker_label` (CLI'dan gelecek)
- Yeni instance variable: `console` (Rich Console)
- Yeni instance variable: `tui` (PresentationTUI instance)

### 2.3 STT Processor Değişikliği

**Sorun:** Mevcut kodda queue'ya sadece similarity için kullanılan kelimeler gönderiliyor.

**Çözüm:** Queue'ya tuple gönder:

- `(full_display_text, similarity_words)`
- `full_display_text`: Tüm normalize edilmiş konuşma (TUI'da gösterilecek)
- `similarity_words`: Son N kelime (similarity hesabı için)

### 2.4 Navigator Değişikliği

**Kaldırılacaklar:**

- `typer.echo()` çağrıları
- Status emoji hesaplama mantığı (✖, ■, ▶, ◀)
- CLI formatında string oluşturma

**Eklenecekler:**

- Queue'dan tuple unpack etme
- `self.tui.*` property'lerini güncelleme
- Her durumda uygun `last_action` mesajı atama

### 2.5 Control Loop Değişikliği

**Mevcut:** Basit while loop, `shutdown_flag.wait()` ile bekliyor

**Yeni:** Rich Live context manager ile sarma:

- `with Live(...)` bloğu audio stream ile aynı context'te
- Her SHUTDOWN_CHECK_INTERVAL'da `live.update()` çağrısı
- TUI otomatik olarak refresh oluyor (refresh_per_second=4)

---

## 3. Veri Akışı

```
Audio → STT Processor → (full_text, words) → Queue → Navigator → TUI Properties
                                                           ↓
                                                    Live.update() → Panel → Terminal
```

---

## 4. Global Word Index Sistemi

### 4.1 Nedir?

Global Word Index, sunumdaki TÜM kelimelerin tek bir listede tutulması ve her chunk'ın bu listede nerede başladığının kaydedilmesi sistemidir.

### 4.2 Neden Gerekli?

**Problem:** Mevcut Match display sadece eşleşen chunk'ın 12 kelimesini gösteriyor. Bu yeterli context sağlamıyor.

**Örnek:**

- Chunk: "juggling work deadlines family responsibilities and"
- Kullanıcı: "...your juggling work deadlines family responsibilities"

Sadece chunk'ı göstermek yeterli değil. Önceki birkaç kelimeyi de görmek istiyorsun ama chunk'lar overlapping olduğu için "önceki chunk"u almak temiz bir çözüm değil.

### 4.3 Nasıl Çalışır?

**Veri yapıları:**

1. `all_words: list[str]`

   - Tüm section'lardaki kelimelerin birleştirilmiş listesi
   - Normalize edilmiş halde
   - Örnek: `["merhaba", "bugun", "sizlere", "onemli", "konular", ...]`

2. `chunk_start_positions: dict[str, int]`
   - Her chunk_id için bu chunk'ın `all_words` listesinde hangi index'te başladığı
   - Örnek: `{"chunk-abc123": 0, "chunk-def456": 1, "chunk-ghi789": 2, ...}`

**Kullanım:**

Best match chunk bulunduğunda:

1. `chunk_id`'yi al
2. `start_pos = chunk_start_positions[chunk_id]`
3. `end_pos = start_pos + window_size`
4. Context için: `all_words[start_pos - 30 : end_pos]` (30 kelime öncesi + chunk)
5. Bu kelimeleri birleştirip `match_text` olarak göster

### 4.4 Avantajları

- **Temiz mimari:** Chunk sınırlarıyla uğraşmak yerine düz slice işlemi
- **Esnek context:** İstediğin kadar önceki/sonraki kelimeyi alabilirsin
- **O(1) lookup:** Dictionary ile anında pozisyon bulma
- **Bellek verimli:** Kelimeler zaten section'larda var, sadece index tutuluyor

### 4.5 Implementasyon Yeri

Bu değişiklik `chunk_producer.generate_chunks()` fonksiyonunda yapılır:

- Dönüş tipi `list[Chunk]` yerine `ChunkGenerationResult` dataclass olur
- Bu dataclass içinde: `chunks`, `all_words`, `chunk_start_positions`

`PresentationController.__init__`'te:

- `generate_chunks()` çağrısından dönen result'tan üç değer de alınır
- `self.all_words` ve `self.chunk_start_positions` saklanır

`_navigator_task`'ta:

- Match display oluştururken bu yapılar kullanılır

---

## 5. Implementasyon Sırası

1. **TUI Class oluştur** - Bağımsız, test edilebilir
2. **Controller'a TUI ekle** - `__init__`'te instance oluştur
3. **STT Processor güncelle** - Tuple gönder
4. **Navigator güncelle** - TUI property'leri güncelle, typer.echo kaldır
5. **Control loop güncelle** - Rich Live ekle
6. **CLI güncelle** - speaker_label gönder
7. **(Opsiyonel) Global Word Index ekle** - Daha iyi match display için

---

## 6. Test Kontrol Listesi

- [ ] Panel görünüyor mu?
- [ ] Status renkleri doğru mu? (ACTIVE=yeşil)
- [ ] Match score rengi değişiyor mu?
- [ ] Input/Match metinleri güncelleniyor mu?
- [ ] Slayt numarası doğru mu?
- [ ] Navigasyon mesajları görünüyor mu?
- [ ] Ctrl+C ile temiz çıkış oluyor mu?
- [ ] Panel terminal genişliğine uyuyor mu?
