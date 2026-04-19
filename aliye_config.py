from typing import List, Dict

PORT = 8504
GUNCELLEME_ARALIGI = 1800  # 30 dakika

HABER_LIMITI = 1000

# Raif'in öncelik bölgeleri (sıraya göre)
ONCELIK_BOLGELER: List[str] = [
    "Göktürk",
    "Eyüpsultan",
    "Eyüp Sultan",
    "Kemerburgaz", 
    "Trakya",
    "Edirne",
    "Kırklareli",
    "Tekirdağ",
    "Çorlu",
]

# Tüm takip edilen ilçeler
ILCELER: List[str] = [
    # Öncelikli bölgeler
    "Göktürk", "Eyüpsultan", "Kemerburgaz", "Trakya",
    "Edirne", "Kırklareli", "Tekirdağ", "Çorlu", "Lüleburgaz",
    # Diğer İstanbul ilçeleri
    "Kadıköy", "Beşiktaş", "Şişli", "Ataşehir", "Üsküdar", "Sarıyer",
    "Beylikdüzü", "Esenyurt", "Maltepe", "Pendik", "Kartal", "Ümraniye",
    "Bağcılar", "Bahçelievler", "Zeytinburnu", "Fatih",
    "Kağıthane", "Bayrampaşa", "Gaziosmanpaşa", "Başakşehir",
]

KATEGORILER: List[str] = [
    "Konut Fiyatları", "Kanunlar", "Yeni Projeler", "GYO Haberleri",
    "Kira Piyasası", "Kentsel Dönüşüm", "Yatırım", "Yabancı Yatırımcı"
]

# Öncelikli arama kelimeleri
ONCELIK_KEYWORDS: List[str] = [
    "Göktürk", "Kemerburgaz", "Eyüpsultan", "Eyüp Sultan",
    "Trakya", "Edirne", "Kırklareli", "Tekirdağ", "Çorlu"
]

# Genel emlak anahtar kelimeleri
EMLAK_KEYWORDS: List[str] = [
    "emlak", "konut", "kira", "gayrimenkul", "tapu", "imar", "inşaat",
    "TOKI", "TOKİ", "daire", "rezidans", "İstanbul", "müteahhit", "arsa",
    "satılık", "kiralık", "metrekare",
    # Öncelikli bölgeler de keyword olarak
    "Göktürk", "Kemerburgaz", "Eyüpsultan", "Trakya", "Edirne"
]

GYO_SEMBOLLER: List[str] = [
    "EKGYO.IS", "ISGYO.IS", "TRGYO.IS", "OZGYO.IS", "VKGYO.IS", "ALKIM.IS"
]

# Önem skoru: öncelikli bölgeler daha yüksek
def onem_skoru_hesapla(baslik: str, ozet: str) -> int:
    metin = (baslik + " " + ozet).lower()
    
    # En yüksek öncelik: Göktürk, Kemerburgaz
    if any(b.lower() in metin for b in ["göktürk", "kemerburgaz"]):
        return 10
    
    # Yüksek öncelik: Eyüpsultan, Trakya bölgesi
    if any(b.lower() in metin for b in ["eyüpsultan", "eyüp sultan", "trakya", "edirne", "kırklareli", "tekirdağ", "çorlu"]):
        return 9
    
    # Standart
    if "kanun" in metin or "mevzuat" in metin or "kararname" in metin:
        return 8
    if "fiyat" in metin or "metrekare" in metin or "m²" in metin:
        return 7
    if "proje" in metin or "inşaat" in metin:
        return 6
    
    return 5
