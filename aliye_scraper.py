from typing import Optional, List, Dict, Any
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import aliye_database as db
from aliye_config import ONCELIK_KEYWORDS, onem_skoru_hesapla

logger = logging.getLogger("aliye_scraper")

def ilce_tespit_et(metin: str) -> str:
    oncelik = ["Göktürk", "Kemerburgaz", "Eyüpsultan", "Eyüp Sultan",
                "Trakya", "Edirne", "Kırklareli", "Tekirdağ", "Çorlu",
                "Lüleburgaz", "Kadıköy", "Beşiktaş", "Şişli", "Sarıyer",
                "Üsküdar", "Ataşehir", "Başakşehir", "Esenyurt", "Beylikdüzü"]
    for ilce in oncelik:
        if ilce.lower() in metin.lower():
            return ilce
    return ""

def kategori_tespit_et(metin: str) -> str:
    m = metin.lower()
    if any(k in m for k in ["kanun", "yasa", "mevzuat", "kararname", "yönetmelik"]):
        return "Kanunlar"
    if any(k in m for k in ["fiyat", "metrekare", "m²", "artış", "değer", "endeks"]):
        return "Konut Fiyatları"
    if any(k in m for k in ["proje", "inşaat", "yapı", "toki", "rezidans"]):
        return "Yeni Projeler"
    if any(k in m for k in ["kira", "kiralık", "kiracı"]):
        return "Kira Piyasası"
    if any(k in m for k in ["dönüşüm", "kentsel", "deprem", "yıkım"]):
        return "Kentsel Dönüşüm"
    if any(k in m for k in ["yabancı", "vatandaşlık"]):
        return "Yabancı Yatırımcı"
    return "Yatırım"

def google_news_rss(query: str, kaynak_etiket: str) -> int:
    """Google News RSS ile haber çek"""
    import urllib.parse
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=tr&gl=TR&ceid=TR:tr"
    
    kaydedilen = 0
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.content, "xml")
        
        items = soup.find_all("item")
        for item in items[:20]:
            baslik = item.find("title")
            baslik = baslik.get_text(strip=True) if baslik else ""
            if not baslik:
                continue
            
            link_el = item.find("link")
            link = link_el.get_text(strip=True) if link_el else ""
            
            ozet_el = item.find("description")
            ozet = ozet_el.get_text(strip=True)[:300] if ozet_el else ""
            
            pub_el = item.find("pubDate")
            tarih = datetime.now().strftime("%Y-%m-%d")
            if pub_el:
                try:
                    from email.utils import parsedate_to_datetime
                    tarih = parsedate_to_datetime(pub_el.get_text()).strftime("%Y-%m-%d")
                except:
                    pass
            
            ilce = ilce_tespit_et(baslik + " " + ozet)
            kategori = kategori_tespit_et(baslik + " " + ozet)
            onem = onem_skoru_hesapla(baslik, ozet)
            
            source_el = item.find("source")
            kaynak = source_el.get_text(strip=True) if source_el else kaynak_etiket
            
            if db.haber_ekle(baslik, ozet, link, kaynak, kategori, ilce, tarih, onem):
                kaydedilen += 1
        
        logger.info(f"'{query}': {kaydedilen} yeni haber")
    except Exception as e:
        logger.error(f"RSS hatası '{query}': {e}")
    
    return kaydedilen

def tum_haberleri_cek() -> int:
    """Tüm öncelikli bölgeler için haber çek"""
    toplam = 0
    
    # 1. Göktürk — en yüksek öncelik
    logger.info("🏘️ Göktürk haberleri çekiliyor...")
    toplam += google_news_rss("Göktürk emlak konut gayrimenkul", "Google News")
    toplam += google_news_rss("Göktürk Eyüpsultan konut proje", "Google News")
    
    # 2. Eyüpsultan
    logger.info("🏘️ Eyüpsultan haberleri çekiliyor...")
    toplam += google_news_rss("Eyüpsultan gayrimenkul inşaat", "Google News")
    
    # 3. Kemerburgaz
    logger.info("🏘️ Kemerburgaz haberleri çekiliyor...")
    toplam += google_news_rss("Kemerburgaz emlak konut proje", "Google News")
    toplam += google_news_rss("Kemerburgaz gayrimenkul", "Google News")
    
    # 4. Trakya bölgesi
    logger.info("🌾 Trakya bölgesi haberleri çekiliyor...")
    toplam += google_news_rss("Trakya gayrimenkul konut", "Google News")
    toplam += google_news_rss("Edirne emlak arsa konut", "Google News")
    toplam += google_news_rss("Tekirdağ emlak gayrimenkul", "Google News")
    toplam += google_news_rss("Kırklareli emlak konut", "Google News")
    toplam += google_news_rss("Çorlu emlak gayrimenkul", "Google News")
    
    # 5. İstanbul genel emlak
    logger.info("🏙️ İstanbul genel emlak haberleri...")
    toplam += google_news_rss("İstanbul konut fiyatları 2026", "Google News")
    toplam += google_news_rss("İstanbul emlak gayrimenkul", "Google News")
    toplam += google_news_rss("İstanbul kira artış konut", "Google News")
    
    # 6. Kanunlar
    logger.info("⚖️ Kanun ve mevzuat haberleri...")
    toplam += google_news_rss("konut kanunu mevzuat 2026", "Google News")
    toplam += google_news_rss("imar kanunu değişiklik", "Google News")
    
    # 7. Kanal İstanbul
    logger.info("🌊 Kanal İstanbul haberleri...")
    toplam += google_news_rss("Kanal İstanbul proje gayrimenkul konut", "Google News")
    toplam += google_news_rss("Kanal İstanbul arsa yatırım 2026", "Google News")
    
    logger.info(f"✅ Toplam {toplam} yeni haber eklendi")
    return toplam
