"""
Aliye — Geçmişe Dönük Haber Ekleme
Trakya, Yassıören, Kanal İstanbul — 2 yıllık arşiv
"""
import sqlite3
import requests
import time
import hashlib
from datetime import datetime
from xml.etree import ElementTree as ET
import re

DB_PATH = "aliye.db"

ARAMA_TERIMLERI = [
    # Trakya
    ("Trakya arsa fiyatları", "Trakya"),
    ("Trakya gayrimenkul yatırım", "Trakya"),
    ("Trakya konut fiyatları", "Trakya"),
    ("Trakya imar planı", "Trakya"),
    ("Edirne arsa yatırım emlak", "Edirne"),
    ("Kırklareli arsa gayrimenkul", "Kırklareli"),
    ("Tekirdağ arsa fiyatları emlak", "Tekirdağ"),
    ("Çorlu gayrimenkul konut", "Çorlu"),
    ("Lüleburgaz arsa emlak", "Trakya"),
    ("Babaeski arsa fiyat", "Trakya"),

    # Yassıören
    ("Yassıören arsa", "Göktürk"),
    ("Yassıören konut", "Göktürk"),
    ("Yassıören gayrimenkul", "Göktürk"),
    ("Yassıören imar", "Göktürk"),
    ("Yassıören Eyüpsultan", "Göktürk"),

    # Kanal İstanbul
    ("Kanal İstanbul gayrimenkul", ""),
    ("Kanal İstanbul arsa fiyatları", ""),
    ("Kanal İstanbul yatırım emlak", ""),
    ("Kanal İstanbul imar konut", ""),
    ("Kanal İstanbul güzergah arsa", ""),
    ("Kanal İstanbul proje 2024", ""),
    ("Kanal İstanbul proje 2025", ""),
    ("Kanal İstanbul güzergah emlak 2023", ""),
    ("Kanal İstanbul güzergah değer", ""),
    ("Arnavutköy Kanal İstanbul", ""),
    ("Başakşehir Kanal İstanbul arsa", ""),
    ("Silivri Kanal İstanbul konut", ""),

    # Ek Trakya/Kanal bağlantılı
    ("Çerkezköy arsa fiyatları", "Trakya"),
    ("Muratlı gayrimenkul arsa", "Trakya"),
    ("Hayrabolu arsa emlak", "Trakya"),
    ("Malkara arsa fiyat", "Trakya"),
]

def url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:16]

def kategori_belirle(baslik: str, terim: str) -> str:
    baslik_lower = baslik.lower()
    terim_lower = terim.lower()
    if "fiyat" in baslik_lower or "değer" in baslik_lower or "artış" in baslik_lower:
        return "Konut Fiyatları"
    if "imar" in baslik_lower or "plan" in baslik_lower or "ruhsat" in baslik_lower:
        return "Yeni Projeler"
    if "kanal" in terim_lower:
        return "Yeni Projeler"
    if "yatırım" in baslik_lower or "arsa" in baslik_lower:
        return "Yatırım"
    if "kira" in baslik_lower:
        return "Kira Piyasası"
    return "Yatırım"

def onem_hesapla(baslik: str, terim: str) -> int:
    skor = 5
    onemli = ["kanal istanbul", "yassıören", "milyar", "ihale", "proje", "imar"]
    for k in onemli:
        if k in baslik.lower():
            skor += 1
    if "trakya" in terim.lower() or "kanal" in terim.lower():
        skor += 1
    return min(skor, 10)

def google_news_cek(terim: str, sayfa: int = 0) -> list:
    """Google News RSS'den haber çek"""
    encoded = requests.utils.quote(terim)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=tr&gl=TR&ceid=TR:tr&start={sayfa * 10}"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return []

        root = ET.fromstring(r.content)
        haberler = []

        for item in root.findall(".//item"):
            baslik = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            kaynak_el = item.find("source")
            kaynak = kaynak_el.text if kaynak_el is not None else "Google Haberler"

            # Tarih parse
            tarih = ""
            if pub_date:
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(pub_date)
                    tarih = dt.strftime("%Y-%m-%d")
                except:
                    tarih = datetime.now().strftime("%Y-%m-%d")

            if baslik and link:
                haberler.append({
                    "baslik": baslik,
                    "ozet": f"<a href=\"{link}\">{baslik}</a>",
                    "url": link,
                    "kaynak": kaynak,
                    "tarih": tarih,
                })

        return haberler
    except Exception as e:
        print(f"  ⚠️ Hata: {e}")
        return []

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Mevcut URL'leri al (duplicate engeli)
    c.execute("SELECT url FROM haberler")
    mevcut_urller = {r[0] for r in c.fetchall()}
    print(f"Mevcut haber sayısı: {len(mevcut_urller)}")

    toplam_eklendi = 0
    toplam_atlandı = 0

    for terim, ilce in ARAMA_TERIMLERI:
        print(f"\n🔍 Aranıyor: '{terim}' ({ilce or 'genel'})")

        # Her terim için 3 sayfa çek (~30 haber)
        for sayfa in range(3):
            haberler = google_news_cek(terim, sayfa)
            if not haberler:
                break

            eklendi = 0
            for h in haberler:
                if h["url"] in mevcut_urller:
                    toplam_atlandı += 1
                    continue

                # 2 yıldan eski haberleri filtrele
                if h["tarih"] < "2024-01-01":
                    continue

                kategori = kategori_belirle(h["baslik"], terim)
                onem = onem_hesapla(h["baslik"], terim)

                try:
                    c.execute("""
                        INSERT INTO haberler (baslik, ozet, url, kaynak, kategori, ilce, tarih, onem_skoru)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        h["baslik"],
                        h["ozet"],
                        h["url"],
                        h["kaynak"],
                        kategori,
                        ilce,
                        h["tarih"],
                        onem,
                    ))
                    mevcut_urller.add(h["url"])
                    eklendi += 1
                    toplam_eklendi += 1
                except sqlite3.IntegrityError:
                    pass

            conn.commit()
            print(f"  Sayfa {sayfa+1}: {len(haberler)} haber çekildi, {eklendi} eklendi")
            time.sleep(1.5)  # Rate limit

    conn.close()
    print(f"\n✅ Tamamlandı! Toplam {toplam_eklendi} yeni haber eklendi, {toplam_atlandı} atlandı")

if __name__ == "__main__":
    main()
