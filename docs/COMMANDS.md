# moves-cli Komutları ve Çalışma Akışları

Bu doküman, moves-cli uygulamasındaki tüm CLI komutlarını, bunların detaylı çalışma akışlarını, ilgili dosya yapılarını ve alt modülleri Türkçe olarak açıklar.

## İçindekiler

1. [Genel Yapı](#genel-yapı)
2. [Ana Komutlar](#ana-komutlar)
3. [Speaker Alt Komutları](#speaker-alt-komutları)
4. [Settings Alt Komutları](#settings-alt-komutları)
5. [Veri Akışı ve Dosya Yapısı](#veri-akışı-ve-dosya-yapısı)
6. [Modül İlişkileri](#modül-ilişkileri)

---

## Genel Yapı

### CLI Giriş Noktası (`cli.py`)

CLI uygulaması `src/moves_cli/cli.py` dosyasında tanımlıdır ve şu yapıyı izler:

```python
app = typer.Typer(
    help="moves CLI - Presentation control, reimagined.",
    add_completion=False,
)
```

Ana uygulama iki alt komut grubuna ayrılır:
- `speaker_app`: Speaker profilleri ve işleme komutları
- `settings_app`: Sistem ayarları (model, API key)

### Versiyon Callback

```python
def version_callback(value: bool):
    """Get version from package metadata and display it"""
    if value:
        # importlib.metadata ile paket versiyonu alınır
        version = importlib.metadata.version("moves-cli")
        typer.echo(output(f"moves-cli version {version}"))
```

### Pompa Fonksiyonları

CLI dosyasında üç kritik pompa (factory) fonksiyonu vardır:

1. **`speaker_manager_instance()`**: SpeakerManager nesnesi oluşturur
2. **`presentation_controller_instance()`**: PresentationController nesnesi oluşturur
3. **`settings_editor_instance()`**: SettingsEditor nesnesi oluşturur

Bu fonksiyonlar lazy import kullanarak döngüsel bağımlılık sorunlarını önler.

---

## Ana Komutlar

### `present` Komutu

**Amaç:** Canlı ses kontrollü sunum navigasyonu başlatır.

**Kullanım:**
```bash
moves present <speaker>
```

**Parametreler:**
- `speaker`: Speaker adı veya ID'si (zorunlu)

**Detaylı Çalışma Akışı:**

#### Adım 1: Speaker Çözümleme
```python
# cli.py:486-497
speaker_manager = speaker_manager_instance()
resolved_speaker = speaker_manager.resolve(speaker)
```
1. `SpeakerManager.list()` çağrılarak mevcut speaker'lar listelenir
2. `by_id` ve `by_name` sözlükleri oluşturulur (O(n) karmaşıklık)
3. Önce ID ile arama yapılır (O(1))
4. Bulunamazsa isim ile arama yapılır (O(1))
5. Birden fazla eşleşme varsa hata fırlatılır

**İlgili Dosya:** `src/moves_cli/core/speaker_manager.py:153-177`

#### Adım 2: Processed Sections Kontrolü
```python
# cli.py:499-513
if not resolved_speaker.sections_file.exists():
    # sections.md dosyası yoksa hata
    raise typer.Exit(1)
```
- `speaker.sections_file` özelliği kontrol edilir
- Bu dosya `.moves/speakers/<speaker_id>/sections.md` yolunda bulunur
- Dosya yoksa kullanıcıya `moves speaker prepare` komutu önerilir

**İlgili Dosya:** `src/moves_cli/models.py:54-57`

#### Adım 3: Kaynak Dosya Doğrulaması
```python
# cli.py:515-537
missing_files = []
if not resolved_speaker.source_presentation.exists():
    missing_files.append(...)
if not resolved_speaker.source_transcript.exists():
    missing_files.append(...)
```
- Presentation PDF dosyası kontrol edilir
- Transcript PDF dosyası kontrol edilir
- Eksik dosya varsa hata mesajı ile çıkılır

#### Adım 4: Dosya Değişiklik Kontrolü (Hash Karşılaştırması)
```python
# cli.py:539-73
files_changed = []
if resolved_speaker.presentation_hash:
    current_pres_hash = SpeakerManager.compute_file_hash(
        resolved_speaker.source_presentation
    )
    if current_pres_hash != resolved_speaker.presentation_hash:
        files_changed.append("Presentation")
```
- `xxh3_64` algoritması kullanılarak dosya hash'leri hesaplanır
- Hash'ler speaker.yaml dosyasında saklanır
- Değişiklik varsa kullanıcıya uyarı gösterilir

**İlgili Dosya:** `src/moves_cli/core/speaker_manager.py:46-54`

#### Adım 5: Sections.md Değişiklik Kontrolü
```python
# cli.py:575-607
if resolved_speaker.sections_hash:
    current_sections_hash = SpeakerManager.compute_normalized_sections_hash(
        resolved_speaker.sections_file
    )
    if current_sections_hash != resolved_speaker.sections_hash:
        # Kullanıcıya seçenekler sunulur:
        # N: Abort
        # S: Hash'i güncelle
        # Y: Devam et
```
- `markdown_to_plain_text` ile markdown formatı temizlenir
- Hash karşılaştırması yapılır
- Kullanıcıya üç seçenek sunulur

**İlgili Dosya:** `src/moves_cli/utils/formatters.py:15-100`

#### Adım 6: Sections Yükleme
```python
# cli.py:609-619
sec_producer = SectionProducer()
sections = sec_producer.load_from_markdown(
    data_handler.read(resolved_speaker.sections_file)
)
```
- `SectionProducer.load_from_markdown()` ile markdown parse edilir
- `# N. Slide` formatındaki başlıklar section index olarak okunur

**İlgili Dosya:** `src/moves_cli/core/components/section_producer.py:195-218`

#### Adım 7: Boş Section Kontrolü
```python
# cli.py:625-637
empty_sections = [s for s in sections if not s.content.strip()]
if empty_sections:
    # Manual mode'da oluşturulan şablonlar için uyarı
    if not typer.confirm("Continue anyway?", default=False):
        raise typer.Abort()
```
- Manual mode ile oluşturulan şablonlarda içerik boş olabilir
- Kullanıcıya devam edip etmeyeceği sorulur

#### Adım 8: PresentationController Başlatma
```python
# cli.py:621-646
window_size = WINDOW_SIZE  # config.py'den 12
controller = presentation_controller_instance(sections, window_size=window_size)
controller.control()
```

**İlgili Dosya:** `src/moves_cli/core/presentation_controller.py`

---

### PresentationController Çalışma Akışı

#### Adım 1: Model Hazırlama
```python
# presentation_controller.py:197
asyncio.run(model_preparer.prepare_models())
```

**İlgili Dosya:** `src/moves_cli/utils/model_preparer.py`

**Adımlar:**
1. `EmbeddingModel`, `SttModel`, `VadModel` modelleri kontrol edilir
2. Hash doğrulaması yapılır (`_verify_checksum_sync`)
3. Eksik veya bozuk dosyalar indirilir
4. Eşzamanlı indirme (max 4 concurrent)

**Modeller:**
- **EmbeddingModel**: `all-MiniLM-l6-v2` (semantic similarity için)
- **SttModel**: `sherpa-onnx-nemo-streaming-fast-conformer-transducer-en-480ms`
- **VadModel**: `silero-vad-int8`

**İlgili Dosya:** `src/moves_cli/models.py:84-129`

#### Adım 2: STT ve VAD Model Yükleme
```python
# presentation_controller.py:199-232
self.recognizer = OnlineRecognizer.from_transducer(
    tokens=str(self.MODEL_DIR / "tokens.txt"),
    encoder=str(self.MODEL_DIR / "encoder.int8.onnx"),
    decoder=str(self.MODEL_DIR / "decoder.int8.onnx"),
    joiner=str(self.MODEL_DIR / "joiner.int8.onnx"),
    num_threads=self.NUM_THREADS,  # 8 thread
    decoding_method="greedy_search",
)

self.vad = VoiceActivityDetector(
    vad_config, buffer_size_in_seconds=self.VAD_BUFFER_SIZE  # 30 saniye
)
```

**VAD Konfigürasyonu:**
- `VAD_THRESHOLD`: 0.35 (düşük = daha hassas)
- `VAD_MIN_SILENCE`: 0.5 saniye
- `VAD_MIN_SPEECH`: 0.1 saniye
- `VAD_WINDOW_SIZE`: 512 (~32ms)

#### Adım 3: Chunk Üretimi
```python
# presentation_controller.py:260-264
self.chunks = chunk_producer.generate_chunks(sections, window_size)
self.candidate_chunk_generator = chunk_producer.CandidateChunkGenerator(
    self.chunks
)
self.similarity_calculator = SimilarityCalculator(self.chunks)
```

**İlgili Dosya:** `src/moves_cli/core/components/chunk_producer.py`

**Chunk Üretim Algoritması:**
```python
# chunk_producer.py:10-54
def generate_chunks(sections, window_size):
    words_with_sources = [
        (word, section) for section in sections for word in section.content.split()
    ]
    # Sliding window ile kelime grupları oluşturulur
    for i in range(n_words - window_size + 1):
        window = words_with_sources[i : i + window_size]
        chunks.append(Chunk(
            partial_content=normalize_text(joined_text, PREPROCESS),
            source_sections=tuple(sorted(sections_dict.values())),
            chunk_id=generate_chunk_id(),
        ))
    return chunks
```

**CandidateChunkGenerator İndeksleme:**
```python
# chunk_producer.py:57-87
class CandidateChunkGenerator:
    def __init__(self, all_chunks):
        for chunk in all_chunks:
            min_sec_idx = chunk.source_sections[0].section_index
            max_sec_idx = chunk.source_sections[-1].section_index
            # Candidate range: [-3, +5]
            for idx in range(min_sec_idx - 3, max_sec_idx + 5 + 1):
                self._index[idx].append(chunk)
```

**İlgili Dosya:** `src/moves_cli/utils/text_normalizer.py`

**Metin Normalizasyonu (LIVE mode):**
```python
def normalize_text(text, mode=LIVE):
    text = unicodedata.normalize("NFD", text.lower())
    text = RE_DIACRITICS.sub("", text)  # Aksanları kaldır
    text = RE_EMOJI.sub("", text)
    text = text.translate(QUOTE_TRANS_TABLE)
    if mode == PREPROCESS:
        text = RE_DIGITS.sub(_convert_number, text)  # Rakamları kelimelere çevir
    text = RE_SPECIAL_CHARS.sub(" ", text)
    return RE_WHITESPACE.sub(" ", text).strip()
```

#### Adım 4: SimilarityCalculator Başlatma
```python
# similarity_calculator.py:7-17
class SimilarityCalculator:
    def __init__(self, all_chunks):
        self.semantic = Semantic(all_chunks)  # O(1) lookup için embedding'leri hazırla
        self.phonetic = Phonetic(all_chunks)  # O(1) lookup için metaphone kodlarını hazırla
```

**Semantic Karşılaştırma:**
```python
# semantic.py
class Semantic:
    def __init__(self, all_chunks):
        self._model = TextEmbedding(
            model_name=EmbeddingModel.name,
            specific_model_path=EmbeddingModel.model_dir,
        )
        # Tüm chunk embedding'lerini hesapla
        chunk_embeddings = list(self._model.embed(chunk_contents))
        for chunk, embedding in zip(all_chunks, chunk_embeddings):
            norm = np.linalg.norm(embedding) or 1.0
            self._embeddings[chunk.chunk_id] = embedding / norm
```

**Phonetic Karşılaştırma:**
```python
# phonetic.py
class Phonetic:
    def __init__(self, all_chunks):
        self._phonetic_codes = {
            chunk.chunk_id: metaphone(chunk.partial_content).replace(" ", "")
            for chunk in all_chunks
        }
```

#### Adım 5: Audio ve STT İşleme
```python
# presentation_controller.py:391-468
def _audio_sampler_callback(self, indata, _frames, _time, _status):
    samples = indata[:, 0].copy()
    self.vad.accept_waveform(samples)
    
    if self.vad.is_speech_detected():
        # VAD konuşma tespit ettiyse STT'ye gönder
        if not self.audio_queue.full():
            self.audio_queue.put_nowait(samples)

def _stt_processor_task(self):
    stream = self.recognizer.create_stream()
    while not shutdown_flag.is_set():
        audio_chunk = self.audio_queue.get()
        stream.accept_waveform(self.SAMPLE_RATE, audio_chunk)
        
        if text := self.recognizer.get_result(stream):
            words = text.strip().split()
            # Sliding window buffer güncelle
            self._word_buffer.extend(new_words)
            self._word_buffer = self._word_buffer[-self.window_size:]
```

#### Adım 6: Navigator Görevi
```python
# presentation_controller.py:470-541
def _navigator_task(self):
    while not shutdown_flag.is_set():
        current_words = self.words_queue.get()
        input_text = " ".join(current_words)
        
        # Mevcut section için candidate chunks al
        candidate_chunks = self.candidate_chunk_generator.get_candidate_chunks(
            current_section
        )
        
        # Semantic ve phonetic similarity hesapla
        similarity_results = self.similarity_calculator.compare(
            input_text, candidate_chunks, current_section.section_index
        )
        
        top_match = similarity_results[0]
        
        # Threshold kontrolü
        if top_match.score >= SIMILARITY_THRESHOLD:  # 0.7
            # Navigasyon yap
            self._perform_navigation(target_section)
```

**Score Hesaplama:**
```python
# similarity_calculator.py:19-78
def compare(self, input_str, candidates, current_section_index):
    semantic_results = self.semantic.compare(input_str, candidates)
    phonetic_results = self.phonetic.compare(input_str, candidates)
    
    # Ağırlıklı birleştirme (SEMANTIC_WEIGHT=0.6, PHONETIC_WEIGHT=0.4)
    max_p = max(phonetic_scores.values()) or 1.0
    max_s = max(semantic_scores.values()) or 1.0
    
    batch_quality = (0.4 * max_p) + (0.6 * max_s)
    factor_p = (0.4 * batch_quality) / max_p
    factor_s = (0.6 * batch_quality) / max_s
    
    # Tie-breaking: İleri yöndeki slayt tercih edilir
    final_results.sort(key=lambda x: (-x.score, ...))
```

#### Adım 7: Navigasyon Gerçekleştirme
```python
# presentation_controller.py:549-577
def _perform_navigation(self, target_section):
    with self.section_lock:
        current_slide = self.current_section.section_index
        target_slide = target_section.section_index
        slide_delta = target_slide - current_slide
        
        if slide_delta != 0:
            # Echo suppression - kendi tuş vuruşlarımızı yok say
            self._echo_suppression.set()
            try:
                key_to_press = Key.right if slide_delta > 0 else Key.left
                for _ in range(abs(slide_delta)):
                    self.keyboard_controller.press(key_to_press)
                    self.keyboard_controller.release(key_to_press)
                    time.sleep(self.KEY_PRESS_DELAY)  # 0.01s
            finally:
                self._echo_suppression.clear()
            
            self.current_section = target_section
```

#### Adım 8: Klavye Dinleyici
```python
# presentation_controller.py:305-385
def _on_key_press(self, key):
    # M tuşu: Durum değiştir (ACTIVE -> PAUSED -> ACTIVE)
    if hasattr(key, "char") and key.char == "m":
        # Ok tuşları: Manuel müdahale (ACTIVE -> LOCKED)
        if key in (Key.left, Key.right):
            self._set_state(ControllerState.LOCKED)
    
    # Q tuşu: Çıkış
    if hasattr(key, "char") and key.char == "q":
        self.shutdown_flag.set()
```

**Durum Makinesi:**
- **ACTIVE**: Normal çalışma - otomatik navigasyon aktif
- **PAUSED**: Mikrofon duraklatıldı - ses işlenmiyor
- **LOCKED**: Manuel müdahale - navigasyon kilitli (ok tuşları ile)

#### Adım 9: UI Güncelleme
```python
# presentation_controller.py:79-164
def _build_frame(d: UIData) -> Panel:
    return Panel(
        Group(
            _build_header(d),  # Durum | Slayt | Benzerlik
            Rule(style="muted"),
            _build_content(d),  # Konuşma metni | Eşleşen section
            Rule(style="muted"),
            _build_footer(),   # Klavye kısayolları
        ),
        title="[accent]moves[/] Presenter",
    )
```

**Rich UI Bileşenleri:**
- Header: Durum (renkli), slayt sayısı, benzerlik yüzdesi
- Content: VAD ikonu + konuşma metni, section içeriği
- Footer: [M] Pause, [← →] Nav, [Q] Quit

---

## Speaker Alt Komutları

### `speaker add` Komutu

**Amaç:** Yeni speaker profili oluşturur.

**Kullanım:**
```bash
moves speaker add <name> <source_presentation> <source_transcript>
```

**Parametreler:**
- `name`: Speaker adı (zorunlu)
- `source_presentation`: Presentation PDF dosya yolu (zorunlu)
- `source_transcript`: Transcript PDF dosya yolu (zorunlu)

**Detaylı Çalışma Akışı:**

#### Adım 1: Dosya Varlık Kontrolü
```python
# cli.py:76-84
if not source_presentation.exists() or not source_transcript.exists():
    missing = {}
    if not source_presentation.exists():
        missing["Presentation"] = f"Not found: {source_presentation}"
    if not source_transcript.exists():
        missing["Transcript"] = f"Not found: {source_transcript}"
    raise typer.Exit(1)
```

#### Adım 2: Speaker Oluşturma
```python
# cli.py:86-92
speaker_manager = speaker_manager_instance()
speaker = speaker_manager.add(name, source_presentation, source_transcript)
```

**SpeakerManager.add() Akışı:**
```python
# speaker_manager.py:94-135
def add(self, name, source_presentation, source_transcript):
    # Mevcut speaker ID'lerini al
    current_speakers = self.list()
    speaker_ids = [speaker.speaker_id for speaker in current_speakers]
    
    # İsim çakışması kontrolü
    if name in speaker_ids:
        raise ValueError("Speaker name conflicts with existing ID")
    
    # Benzersiz speaker ID oluştur
    for attempt in range(SPEAKER_ID_GENERATION_MAX_RETRIES):
        candidate_id = id_generator.generate_speaker_id(name)
        if candidate_id not in speaker_ids:
            speaker_id = candidate_id
            break
    
    # Speaker nesnesi oluştur
    speaker = Speaker(
        name=name,
        speaker_id=speaker_id,
        source_presentation=source_presentation.resolve(),
        source_transcript=source_transcript.resolve(),
    )
    
    # speaker.yaml dosyasına yaz
    self._write_speaker_yaml(speaker_path / SPEAKER_FILENAME, speaker)
    return speaker
```

**ID Oluşturma:**
```python
# id_generator.py:34-42
def generate_speaker_id(name: str) -> str:
    ascii_name = unidecode(name).lower()
    slug = SLUG_CLEANER.sub("", ascii_name)
    slug = SLUG_SPACES.sub("-", slug).strip("-")
    suffix = IDEngine.get_id(SPEAKER_ID_SUFFIX_LENGTH)  # 5 karakter
    return f"{slug}-{suffix}"
```

**Speaker Veri Yapısı:**
```python
# models.py:31-62
@dataclass
class Speaker:
    name: str
    speaker_id: str
    source_presentation: Path
    source_transcript: Path
    last_processed: str | None = None
    presentation_hash: str | None = None
    transcript_hash: str | None = None
    sections_hash: str | None = None
    
    @property
    def data_dir(self) -> Path:
        return DATA_FOLDER / "speakers" / self.speaker_id
    
    @property
    def sections_file(self) -> Path:
        return self.data_dir / SECTIONS_FILENAME
    
    @property
    def speaker_file(self) -> Path:
        return self.data_dir / SPEAKER_FILENAME
```

**Speaker YAML Formatı:**
```yaml
name: "John Doe"
speaker_id: "john-doe-abc12"
source_presentation: "/path/to/presentation.pdf"
source_transcript: "/path/to/transcript.pdf"
last_processed: null
presentation_hash: null
transcript_hash: null
sections_hash: null
```

**Dosya Yapısı:**
```
~/.moves/
├── settings.toml
├── speakers/
│   └── john-doe-abc12/
│       ├── speaker.yaml
│       └── sections.md
└── ml_models/
    └── ...
```

---

### `speaker edit` Komutu

**Amaç:** Mevcut speaker'ın sunum ve/veya transcript dosyalarını günceller.

**Kullanım:**
```bash
moves speaker edit <speaker> [--presentation <path>] [--transcript <path>]
```

**Parametreler:**
- `speaker`: Speaker adı veya ID'si (zorunlu)
- `--presentation`, `-p`: Yeni presentation dosya yolu (isteğe bağlı)
- `--transcript`, `-t`: Yeni transcript dosya yolu (isteğe bağlı)

**Detaylı Çalışma Akışı:**

#### Adım 1: Parametre Doğrulama
```python
# cli.py:114-122
if not source_presentation and not source_transcript:
    # En az bir parametre verilmeli
    raise typer.Exit(1)
```

#### Adım 2: Speaker Çözümleme
```python
# cli.py:124-127
speaker_manager = speaker_manager_instance()
resolved_speaker = speaker_manager.resolve(speaker)
```

#### Adım 3: Dosya Varlık Kontrolü
```python
# cli.py:129-151
presentation_path = Path(source_presentation) if source_presentation else None
transcript_path = Path(source_transcript) if source_transcript else None

if presentation_path and not presentation_path.exists():
    raise typer.Exit(1)
if transcript_path and not transcript_path.exists():
    raise typer.Exit(1)
```

#### Adım 4: Speaker Güncelleme
```python
# cli.py:153-169
updated_speaker = speaker_manager.edit(
    resolved_speaker, presentation_path, transcript_path
)
```

**SpeakerManager.edit() Akışı:**
```python
# speaker_manager.py:137-151
def edit(self, speaker, source_presentation=None, source_transcript=None):
    speaker_path = self.SPEAKERS_PATH / speaker.speaker_id
    
    if source_presentation:
        speaker.source_presentation = source_presentation.resolve()
    if source_transcript:
        speaker.source_transcript = source_transcript.resolve()
    
    # YAML dosyasını güncelle
    self._write_speaker_yaml(speaker_path / SPEAKER_FILENAME, speaker)
    return speaker
```

---

### `speaker list` Komutu

**Amaç:** Tüm kayıtlı speaker'ları listeler.

**Kullanım:**
```bash
moves speaker list
```

**Detaylı Çalışma Akışı:**

#### Adım 1: Speaker Listeleme
```python
# cli.py:181-184
speaker_manager = speaker_manager_instance()
speakers = speaker_manager.list()
```

**SpeakerManager.list() Akışı:**
```python
# speaker_manager.py:437-444
def list(self) -> list[Speaker]:
    speakers = []
    for folder in self.data_handler.list(self.SPEAKERS_PATH):
        if folder.is_dir():
            speaker_yaml = folder / SPEAKER_FILENAME
            if speaker_yaml.exists():
                speakers.append(self._read_speaker_yaml(speaker_yaml))
    return speakers
```

#### Adım 2: Tablo Oluşturma
```python
# cli.py:190-203
rows = []
for speaker in speakers:
    ready_status = "Ready" if speaker.sections_file.exists() else "Not Ready"
    last_processed_str = format_datetime(speaker.last_processed)
    
    rows.append({
        "NAME": speaker.name,
        "ID": speaker.speaker_id,
        "STATUS": ready_status,
        "LAST PROCESSED": last_processed_str,
    })

typer.echo(output(f"There are {len(speakers)} registered speaker(s).", rows))
```

**Örnek Çıktı:**
```
NAME          ID              STATUS      LAST PROCESSED
John Doe      john-doe-abc12  Ready       2026-01-20 14:30
Jane Smith    jane-xyz-12345  Not Ready   N/A
```

---

### `speaker show` Komutu

**Amaç:** Belirli bir speaker'ın detaylı bilgilerini gösterir.

**Kullanım:**
```bash
moves speaker show <speaker>
```

**Parametreler:**
- `speaker`: Speaker adı veya ID'si (zorunlu)

**Detaylı Çalışma Akışı:**

#### Adım 1: Speaker Çözümleme
```python
# cli.py:220-222
speaker_manager = speaker_manager_instance()
resolved_speaker = speaker_manager.resolve(speaker)
```

#### Adım 2: Bilgi Görüntüleme
```python
# cli.py:227-239
typer.echo(output(
    f"Showing details for {resolved_speaker.label}",
    {
        "Name": resolved_speaker.name,
        "ID": resolved_speaker.speaker_id,
        "Status": status,
        "Last Processed": last_processed_str,
        "Presentation": resolved_speaker.source_presentation,
        "Transcript": resolved_speaker.source_transcript,
    },
))
```

**Örnek Çıktı:**
```
Showing details for John Doe (john-doe-abc12)
  Name:           John Doe
  ID:             john-doe-abc12
  Status:         Ready
  Last Processed: 2026-01-20 14:30
  Presentation:   /path/to/presentation.pdf
  Transcript:     /path/to/transcript.pdf
```

---

### `speaker prepare` Komutu

**Amaç:** Speaker'ı sunum kontrolü için hazırlar (LLM ile veya manuel).

**Kullanım:**
```bash
moves speaker prepare <speaker(s)> [--all] [--yes] [--manual]
```

**Parametreler:**
- `speakers`: Hazırlanacak speaker adı/ID'leri (isteğe bağlı, --all ile birlikte kullanılmaz)
- `--all`, `-a`: Tüm speaker'ları hazırla
- `--yes`, `-y`: Onay istemeden devam et
- `--manual`, `-m`: LLM kullanmadan çevrimdışı şablon oluştur

**Detaylı Çalışma Akışı:**

#### Adım 1: LLM Ayarları Kontrolü (Auto mode)
```python
# cli.py:261-304
if not manual:
    settings = settings_editor.list()
    if not settings.model:
        # Hata: LLM model ayarlanmamış
        raise typer.Exit(1)
    if not settings.key:
        # Hata: API key ayarlanmamış
        raise typer.Exit(1)
    llm_model = settings.model
    llm_api_key = settings.key
```

#### Adım 2: Speaker Çözümleme
```python
# cli.py:306-327
if all:
    resolved_speakers = speaker_manager.list()
elif speakers:
    resolved_speakers = []
    for pattern in speakers:
        resolved = speaker_manager.resolve(pattern)
        resolved_speakers.append(resolved)
else:
    # Hata: Speaker veya --all verilmeli
    raise typer.Exit(1)
```

#### Adım 3: Async Processing Başlatma
```python
# cli.py:329-338
results = asyncio.run(
    speaker_manager.process(
        resolved_speakers,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        skip_confirmation=yes,
        manual_mode=manual,
    )
)
```

**SpeakerManager.process() Akışı:**

**A. Manual Mode:**
```python
# speaker_manager.py:275-315
if manual_mode:
    results = []
    for speaker, speaker_path in zip(speakers, speaker_paths):
        start_time = time.perf_counter()
        
        # Sadece presentation dosyasından slide sayısını al
        sections = section_producer.generate_template(
            presentation_path=speaker.source_presentation,
        )
        
        # Boş section şablonu oluştur
        self.data_handler.write(
            speaker_path / SECTIONS_FILENAME,
            section_producer.convert_to_markdown(sections),
        )
        
        # Hash'leri güncelle
        speaker.presentation_hash = self.compute_file_hash(speaker.source_presentation)
        speaker.transcript_hash = None
        speaker.sections_hash = self.compute_normalized_sections_hash(...)
        
        self._write_speaker_yaml(speaker_path / SPEAKER_FILENAME, speaker)
```

**B. Auto Mode:**
```python
# speaker_manager.py:317-431
async def process_speaker(speaker, speaker_path, delay, task_id):
    # LLM çağrısı yap (daemon thread içinde)
    sections = section_producer.generate_sections(
        presentation_path=source_presentation,
        transcript_path=source_transcript,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        callback=progress_callback,
    )
    
    # Sections dosyasına yaz
    self.data_handler.write(
        speaker_path / SECTIONS_FILENAME,
        section_producer.convert_to_markdown(sections),
    )
    
    # Hash'leri güncelle
    speaker.last_processed = datetime.now().isoformat()
    speaker.presentation_hash = self.compute_file_hash(source_presentation)
    speaker.transcript_hash = self.compute_file_hash(source_transcript)
    speaker.sections_hash = self.compute_normalized_sections_hash(...)
    
    return ProcessResult(...)
```

**SectionProducer.generate_sections() Akışı:**
```python
# section_producer.py:220-254
def generate_sections(self, presentation_path, transcript_path, ...):
    # 1. PDF'lerden veri çıkar
    presentation_data = self._extract_pdf(presentation_path, "presentation")
    transcript_data = self._extract_pdf(transcript_path, "transcript")
    
    # 2. LLM çağır
    section_contents = self._call_llm(presentation_data, transcript_data, ...)
    
    # 3. Section nesneleri oluştur
    generated_sections = []
    for idx, content in enumerate(section_contents):
        section = Section(content=content, section_index=idx + 1)
        generated_sections.append(section)
    
    return generated_sections
```

**PDF Extraction:**
```python
# section_producer.py:14-42
def _extract_pdf(self, pdf_path, extraction_type):
    data = pdf_path.read_bytes()
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        if extraction_type == "transcript":
            # Tüm metni tek satır
            full_text = "".join(page.get_text("text") for page in doc)
            result = " ".join(full_text.split())
            return result
        
        elif extraction_type == "presentation":
            # Slayt slayt, yeni satır ile ayrılmış
            markdown_sections = []
            for i, page in enumerate(doc):
                page_text = page.get_text("text")
                cleaned_text = " ".join(page_text.split())
                markdown_sections.append(f"# Slide Page {i + 1}\n{cleaned_text}")
            return "\n\n".join(markdown_sections)
```

**LLM Çağrısı:**
```python
# section_producer.py:109-171
class SectionsOutputModel(BaseModel):
    class SectionItem(BaseModel):
        section_index: int = Field(..., ge=1)
        content: str = Field(...)
    
    sections: list[SectionItem] = Field(
        ..., min_items=slide_count, max_items=slide_count
    )

def _call_llm(self, presentation_data, transcript_data, llm_model, llm_api_key):
    system_prompt = files("moves_cli.data").joinpath("llm_instruction.md").read_text()
    
    client = instructor.from_litellm(completion, mode=instructor.Mode.JSON)
    
    response = client.chat.completions.create(
        model=llm_model,
        api_key=llm_api_key,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Presentation: {presentation_data}\nTranscript: {transcript_data}"},
        ],
        response_model=SectionsOutputModel,
        temperature=0.2,
    )
    
    return [item.content for item in response.sections]
```

**Sections Markdown Formatı:**
```markdown
# 1. Slide

Bu slaytın içeriği buraya gelir...

# 2. Slide

İkinci slaytın içeriği...
```

#### Adım 4: Sonuç Gösterimi
```python
# cli.py:340-388
if len(resolved_speakers) == 1:
    result = results[0]
    typer.echo(output(f"Speaker {speaker.label} prepared."))
    typer.echo()
    if manual:
        typer.echo(output(f"{result.section_count} empty sections created."))
    else:
        typer.echo(output(f"{result.section_count} sections in {result.time}s."))
else:
    # Çoklu speaker için özet
    ...
```

---

### `speaker delete` Komutu

**Amaç:** Speaker(s) ve verilerini siler.

**Kullanım:**
```bash
moves speaker delete <speaker(s)> [--all] [--yes]
```

**Parametreler:**
- `speakers`: Silinecek speaker adı/ID'leri (isteğe bağlı, --all ile birlikte kullanılmaz)
- `--all`, `-a`: Tüm speaker'ları sil
- `--yes`, `-y`: Onay istemeden sil

**Detaylı Çalışma Akışı:**

#### Adım 1: Speaker Çözümleme
```python
# cli.py:407-432
if all:
    resolved_speakers = speaker_manager.list()
elif speakers:
    resolved_speakers = []
    for pattern in speakers:
        resolved = speaker_manager.resolve(pattern)
        resolved_speakers.append(resolved)
else:
    raise typer.Exit(1)
```

#### Adım 2: Onay İsteme
```python
# cli.py:434-446
if not yes:
    typer.confirm("Proceed?", default=True, abort=True)
```

#### Adım 3: Silme İşlemi
```python
# cli.py:449-474
for speaker in resolved_speakers:
    try:
        speaker_manager.delete(speaker)
        deleted_count += 1
    except Exception as e:
        failed_count += 1
```

**SpeakerManager.delete() Akışı:**
```python
# speaker_manager.py:433-435
def delete(self, speaker: Speaker) -> None:
    speaker_path = self.SPEAKERS_PATH / speaker.speaker_id
    self.data_handler.delete(speaker_path)
```

**DataHandler.delete() Akışı:**
```python
# data_handler.py:71-84
def delete(self, path: Path) -> None:
    full_path = self._resolve_path(path)
    if full_path.is_file():
        full_path.unlink()
    elif full_path.is_dir():
        shutil.rmtree(full_path)
```

---

## Settings Alt Komutları

### `settings list` Komutu

**Amaç:** Mevcut sistem konfigürasyonunu görüntüler.

**Kullanım:**
```bash
moves settings list [--show]
```

**Parametreler:**
- `--show`, `-s`: API key'i tam olarak göster

**Detaylı Çalışma Akışı:**

#### Adım 1: Settings Okuma
```python
# cli.py:662-665
settings_editor = settings_editor_instance()
settings = settings_editor.list()
```

**SettingsEditor.list() Akışı:**
```python
# settings_editor.py:83-87
def list(self) -> Settings:
    return Settings(
        model=self._data.get("model") or None,
        key=self._data.get("key") or None,
    )
```

#### Adım 2: Key Maskeleme
```python
# cli.py:670-76
if settings.key:
    display_key = settings.key
    if not show:
        if len(settings.key) > 8:
            display_key = f"{settings.key[:4]}{'*' * (len(settings.key) - 8)}{settings.key[-4:]}"
        else:
            display_key = "*" * len(settings.key)
```

#### Adım 3: Görüntüleme
```python
# cli.py:680-685
typer.echo(output(
    f"moves settings (see: {settings_editor.data_handler.DATA_FOLDER / 'settings.toml'})",
    {"model (LLM Model)": model_value, "key (API Key)": display_key},
))
```

**Örnek Çıktı:**
```
moves settings (see: C:\Users\user\.moves\settings.toml)
  model (LLM Model): gemini/gemini-2.5-flash-lite
  key (API Key):     abcd****1234
```

---

### `settings set` Komutu

**Amaç:** Sistem ayarlarını günceller.

**Kullanım:**
```bash
moves settings set <key> <value>
```

**Parametreler:**
- `key`: Ayar adı (zorunlu) - `model` veya `key`
- `value`: Yeni değer (zorunlu)

**Detaylı Çalışma Akışı:**

#### Adım 1: Key Doğrulama
```python
# cli.py:704-710
valid_keys = ["model", "key"]
if key not in valid_keys:
    raise typer.Exit(1)
```

#### Adım 2: Ayar Güncelleme
```python
# cli.py:712-719
success = settings_editor.set(key, value)
if success:
    typer.echo(output(f"Setting '{key}' updated.", {"New Value": value}))
else:
    raise typer.Exit(1)
```

**SettingsEditor.set() Akışı:**
```python
# settings_editor.py:60-69
def set(self, key: str, value: Any) -> bool:
    if key not in self._template_defaults:
        return False
    
    self._data[key] = value
    self._save()
    return True
```

**SettingsEditor._save() Akışı:**
```python
# settings_editor.py:30-58
def _save(self) -> bool:
    self.settings.parent.mkdir(parents=True, exist_ok=True)
    
    doc = tomlkit.document()
    doc.add(tomlkit.comment("moves CLI Configuration"))
    
    for key in self._template_defaults.keys():
        if key == "model":
            doc.add(tomlkit.comment("LLM model for speaker processing..."))
        elif key == "key":
            doc.add(tomlkit.comment("API key for the LLM provider"))
        
        value = self._data.get(key)
        doc[key] = value if value is not None else ""
    
    with self.settings.open("w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(doc))
    return True
```

**Settings TOML Formatı:**
```toml
# moves CLI Configuration

# LLM model for speaker processing, find models at: https://models.litellm.ai/
model = "gemini/gemini-2.5-flash-lite"

# API key for the LLM provider
key = "your-api-key-here"
```

---

### `settings unset` Komutu

**Amaç:** Ayarı varsayılan değerine sıfırlar.

**Kullanım:**
```bash
moves settings unset <key>
```

**Parametreler:**
- `key`: Ayar adı (zorunlu) - `model` veya `key`

**Detaylı Çalışma Akışı:**

#### Adım 1: Key Doğrulama
```python
# cli.py:739-744
valid_keys = ["model", "key"]
if key not in valid_keys:
    raise typer.Exit(1)
```

#### Adım 2: Varsayılan Değeri Alma
```python
# cli.py:746-747
template_value = settings_editor._template_defaults.get(key)
# model: "gemini/gemini-2.5-flash-lite"
# key: ""
```

#### Adım 3: Sıfırlama
```python
# cli.py:749-764
success = settings_editor.unset(key)
if success:
    display_value = "Not configured" if template_value is None else str(template_value)
    typer.echo(output(
        f"Setting '{key}' reset to default.",
        {"New Value": display_value}
    ))
```

**SettingsEditor.unset() Akışı:**
```python
# settings_editor.py:71-81
def unset(self, key: str) -> bool:
    if key in self._template_defaults:
        self._data[key] = self._template_defaults[key]
    else:
        self._data.pop(key, None)
    
    self._save()
    return True
```

---

## Veri Akışı ve Dosya Yapısı

### Ana Veri Klasörü
```
~/.moves/
├── settings.toml          # Sistem ayarları (TOML format)
├── speakers/             # Speaker profilleri
│   ├── <speaker-id-1>/
│   │   ├── speaker.yaml   # Speaker metadata
│   │   └── sections.md    # İşlenmiş section'lar
│   └── <speaker-id-2>/
│       ├── speaker.yaml
│       └── sections.md
└── ml_models/            # ML modelleri
    ├── all-MiniLM-L6-v2_quint8_avx2/
    │   ├── model.onnx
    │   ├── config.json
    │   └── ...
    ├── nemo-streaming-fast-conformer-transducer-en-480ms-int8/
    │   ├── encoder.int8.onnx
    │   ├── decoder.int8.onnx
    │   ├── joiner.int8.onnx
    │   └── tokens.txt
    └── silero-vad-int8/
        └── silero_vad.int8.onnx
```

### Veri Akışı Diyagramı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          moves CLI Veri Akışı                                │
└─────────────────────────────────────────────────────────────────────────────┘

1. SPEAKER EKLEME (moves speaker add)
   ┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
   │ PDF Dosyaları   │────▶│ SectionProducer     │────▶│ speaker.yaml     │
   │ (presentation,  │     │ (PDF extraction)    │     │ sections.md      │
   │  transcript)    │     └─────────────────────┘     │ (.moves/)        │
   └─────────────────┘                                  └──────────────────┘


2. SPEAKER HAZIRLAMA (moves speaker prepare)

   AUTO MODE:
   ┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
   │ PDF Dosyaları   │────▶│ SectionProducer     │────▶│ sections.md      │
   │                 │     │ + LLM (Gemini)      │     │ (AI-generated)   │
   │                 │     └─────────────────────┘     └──────────────────┘
   └─────────────────┘
   
   MANUAL MODE:
   ┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
   │ Presentation PDF│────▶│ SectionProducer     │────▶│ sections.md      │
   │                 │     │ (template only)     │     │ (empty sections) │
   └─────────────────┘     └─────────────────────┘     └──────────────────┘


3. SUNUM KONTROL (moves present)
   ┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
   │ sections.md     │────▶│ ChunkProducer       │────▶│ Chunks           │
   │                 │     │ (sliding window)    │     │ (+ embeddings)   │
   └─────────────────┘     └─────────────────────┘     └──────────────────┘
                                                         │
   ┌─────────────────┐                                   ▼
   │ Mikrofon        │◀────────────────────────────────────────┐
   │ (Real-time)     │                                     ┌────┴────┐
   └─────────────────┘                                     │ Compare │
                                                           │ & Score │
   ┌─────────────────┐                                     └────┬────┘
   │ Klavye          │                                          │
   │ (Manual nav)    │◀─────────────────────────────────────────┘
   └─────────────────┘                                          │
         │                                                      ▼
         ▼                                            ┌─────────────────┐
   ┌─────────────────┐                                 │ Keyboard        │
   │ Rich UI         │◀────────────────────────────────│ Controller      │
   │ (Dashboard)     │                                └─────────────────┘
   └─────────────────┘
```

---

## Modül İlişkileri

### Modül Bağımlılık Haritası

```
cli.py (typer CLI)
    │
    ├── speaker_manager_instance()
    │   └── core/speaker_manager.py
    │       ├── utils/data_handler.py (dosya işlemleri)
    │       ├── utils/id_generator.py (ID üretimi)
    │       ├── models.py (Speaker, Section)
    │       └── core/components/section_producer.py
    │           ├── utils/text_normalizer.py
    │           └── (LLM calls via litellm)
    │
    ├── presentation_controller_instance()
    │   └── core/presentation_controller.py
    │       ├── utils/model_preparer.py (ML modelleri indirme)
    │       ├── models.py (Section, Chunk)
    │       ├── core/components/chunk_producer.py
    │       │   ├── utils/text_normalizer.py
    │       │   └── utils/id_generator.py
    │       └── core/components/similarity_calculator.py
    │           ├── core/components/similarity_units/semantic.py
    │           │   └── models.py (EmbeddingModel)
    │           └── core/components/similarity_units/phonetic.py
    │
    └── settings_editor_instance()
        └── core/settings_editor.py
            ├── utils/data_handler.py
            └── config.py (DEFAULT_LLM_MODEL, DEFAULT_API_KEY)
```

### Kritik Sınıflar ve Sorumlulukları

| Sınıf | Dosya | Sorumluluk |
|-------|-------|------------|
| `SpeakerManager` | `speaker_manager.py` | Speaker CRUD, ID üretimi, hash hesaplama |
| `PresentationController` | `presentation_controller.py` | Ses işleme, navigasyon, UI |
| `SettingsEditor` | `settings_editor.py` | TOML ayarları yönetimi |
| `SectionProducer` | `section_producer.py` | PDF çıkarma, LLM çağrısı, markdown dönüştürme |
| `ChunkProducer` | `chunk_producer.py` | Sliding window chunk üretimi |
| `SimilarityCalculator` | `similarity_calculator.py` | Semantic + phonetic karşılaştırma |
| `DataHandler` | `data_handler.py` | Dosya okuma/yazma/silme |
| `TextNormalizer` | `text_normalizer.py` | Metin normalizasyonu |

### Önemli Sabitler (`config.py`)

```python
# Dosya yapısı
DATA_FOLDER: Path = Path.home() / ".moves"
SECTIONS_FILENAME: str = "sections.md"
SPEAKER_FILENAME: str = "speaker.yaml"

# ID üretimi
SPEAKER_ID_SUFFIX_LENGTH: int = 5
CHUNK_ID_LENGTH: int = 16

# Benzerlik motoru
SEMANTIC_WEIGHT: float = 0.6
PHONETIC_WEIGHT: float = 0.4
SIMILARITY_THRESHOLD: float = 0.7

# Sunum kontrolü
WINDOW_SIZE: int = 12
CANDIDATE_RANGE_MIN_OFFSET: int = -3
CANDIDATE_RANGE_MAX_OFFSET: int = 5

# Varsayılan ayarlar
DEFAULT_LLM_MODEL: str = "gemini/gemini-2.5-flash-lite"
DEFAULT_API_KEY: str = ""
```

---

## Hata Yönetimi

### Exception Türleri

| Exception | Kullanım | Çıkış Kodu |
|-----------|----------|------------|
| `typer.Exit(0)` | Başarılı çıkış | 0 |
| `typer.Exit(1)` | Genel hata | 1 |
| `typer.Abort()` | Kullanıcı iptali | 0 |
| `FileNotFoundError` | Dosya bulunamadı | 1 |
| `ValueError` | Geçersiz değer | 1 |

### Örnek Hata Akışı

```python
# cli.py:86-100
try:
    speaker_manager = speaker_manager_instance()
    speaker = speaker_manager.add(name, source_presentation, source_transcript)
    typer.echo(output(f"Speaker {speaker.label} has been successfully added."))
except typer.Exit:
    raise
except Exception as e:
    typer.echo(output(f"Could not add speaker '{name}'.", {"Error": str(e)}), err=True)
    raise typer.Exit(1)
```

---

## Versiyon Bilgisi

CLI versiyonu `importlib.metadata.version("moves-cli")` ile alınır ve şu şekilde görüntülenir:

```bash
$ moves --version
moves-cli version X.Y.Z
```

---

Bu doküman, moves-cli uygulamasının tüm komutlarını, iç yapısını ve veri akışlarını detaylı olarak açıklamaktadır. Refactoring sırasında bu dokümantasyonu referans olarak kullanabilirsiniz.
