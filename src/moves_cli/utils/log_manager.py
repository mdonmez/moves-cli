import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# --- GÜNCEL YAPILANDIRMA AYARLARI ---
# Ana logger'ımızın ismi.
MAIN_LOGGER_NAME = "moves"

# Tüm detayları (DEBUG) dosyaya kaydetmek için en düşük seviye
GLOBAL_LEVEL = logging.DEBUG

# Konsola sadece Hataları (ERROR ve CRITICAL) yazdırmak için seviye
CONSOLE_LEVEL = logging.ERROR

# Dosya ayarları
LOG_DIR = "logs"
LOG_FILENAME = "moves.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB dosya boyutu
BACKUP_COUNT = 5  # 5 adet yedek dosya tutulur

# Formatlayıcı
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | [%(name)s] | %(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """
    Loglama sistemini başlatır ve handler'ları (işleyicileri) ayarlar.
    Bu fonksiyon, uygulamanın başlangıcında SADECE BİR KEZ çağrılmalıdır.
    """
    # 1. Ana Logger'ı Al
    root_logger = logging.getLogger(MAIN_LOGGER_NAME)
    if root_logger.hasHandlers():
        # Logger zaten kurulmuşsa tekrar kurulumu engelle
        return

    root_logger.setLevel(GLOBAL_LEVEL)  # Tüm logları yakalamak için DEBUG seviyesi

    # Formatlayıcı oluştur
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # 2. Handler 1: Konsol İşleyici (StreamHandler)
    console_handler = logging.StreamHandler(sys.stdout)
    # Konsola sadece ERROR ve CRITICAL seviyesindeki mesajları yazdır
    console_handler.setLevel(CONSOLE_LEVEL)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 3. Handler 2: Dosya İşleyici (RotatingFileHandler)

    # Log klasörünün varlığını kontrol et ve gerekirse oluştur
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, LOG_FILENAME)

    try:
        file_handler = RotatingFileHandler(
            log_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        # Dosyaya tüm logları (DEBUG ve üstü) kaydet
        file_handler.setLevel(GLOBAL_LEVEL)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    except IOError as e:
        root_logger.warning(f"Dosyaya loglama kurulamadı: {e}")


def get_logger(name: str) -> logging.Logger:
    """
    Belirtilen isme sahip bir logger nesnesi döndürür.

    :param name: Genellikle çağıran modülün adı olmalıdır (__name__).
    :return: Yapılandırılmış Logger nesnesi.
    """
    # Alt logger, ana logger'ın ('moves') ayarlarını miras alır.
    return logging.getLogger(f"{MAIN_LOGGER_NAME}.{name}")


# --------------- KULLANIM ÖRNEĞİ ---------------
if __name__ == "__main__":
    setup_logging()

    main_logger = get_logger("Startup")

    # Konsola YAZILMAYACAK (ERROR'dan düşük) ama DOSYAYA YAZILACAK
    main_logger.debug("Çok detaylı hata ayıklama mesajı.")
    main_logger.info("Uygulama başarıyla başlatıldı.")
    main_logger.warning("Beklenmedik bir durum oluştu, ancak işlem devam ediyor.")

    # Hem KONSOLA hem de DOSYAYA YAZILACAK
    main_logger.error("Kritik veritabanı bağlantı hatası oluştu.")
    main_logger.critical("Uygulama durduruluyor.")

    # Simülasyon sonrası konsol çıktısı sadece iki hata mesajını içerecektir.
    # moves.log dosyası ise beş mesajın hepsini içerecektir.
