import schedule
import time
import logging
import sys
from aliye_database import init_db
from aliye_scraper import tum_haberleri_cek

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("aliye.log", encoding="utf-8")],
)
logger = logging.getLogger("aliye_main")

def run_scraping():
    logger.info("=" * 50)
    logger.info("Haber çekme başlıyor — Göktürk | Kemerburgaz | Trakya | Kanal İstanbul")
    n = tum_haberleri_cek()
    logger.info(f"✅ {n} yeni haber eklendi")

def main():
    init_db()
    logger.info("ALİYE başlatıldı — 30 dakikada bir güncelleniyor")
    
    # Hemen çalıştır
    run_scraping()
    
    # Her 30 dakikada tekrarla
    schedule.every(30).minutes.do(run_scraping)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
