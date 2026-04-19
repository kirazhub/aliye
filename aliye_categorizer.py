from typing import Dict, List
from aliye_config import ILCELER

KATEGORI_KEYWORDS: Dict[str, List[str]] = {
    "Kanunlar": [
        "kanun", "yasa", "mevzuat", "kararname", "yönetmelik",
        "tebliğ", "genelge", "düzenleme", "resmi gazete"
    ],
    "Konut Fiyatları": [
        "fiyat", "metrekare", "m²", "artış", "değer",
        "pahalı", "ucuz", "zam", "piyasa", "endeks"
    ],
    "Yeni Projeler": [
        "proje", "inşaat", "yapı", "TOKİ", "TOKI",
        "rezidans", "site", "yeni konut", "yapım"
    ],
    "GYO Haberleri": [
        "GYO", "yatırım ortaklığı", "gayrimenkul yatırım",
        "borsa", "hisse", "EKGYO", "ISGYO", "TRGYO"
    ],
    "Kira Piyasası": [
        "kira", "kiralık", "kiracı", "ev sahibi", "kira artış",
        "kira stopaj", "kira sözleşme"
    ],
    "Kentsel Dönüşüm": [
        "dönüşüm", "kentsel", "deprem", "yıkım",
        "riskli yapı", "güçlendirme", "kentsel dönüşüm"
    ],
    "Yabancı Yatırımcı": [
        "yabancı", "vatandaşlık", "yatırımcı", "uluslararası",
        "döviz", "yurt dışı", "yabancı alım"
    ],
}

ONEM_SKORU_MAP: Dict[str, int] = {
    "Kanunlar": 9,
    "Konut Fiyatları": 8,
    "Kentsel Dönüşüm": 8,
    "Yeni Projeler": 7,
    "Kira Piyasası": 7,
    "Yabancı Yatırımcı": 6,
    "GYO Haberleri": 6,
    "Yatırım": 5,
}


def kategorize(baslik: str) -> str:
    baslik_lower = baslik.lower()
    for kategori, keywords in KATEGORI_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in baslik_lower:
                return kategori
    return "Yatırım"


def ilce_tespit(baslik: str) -> str:
    baslik_lower = baslik.lower()
    for ilce in ILCELER:
        if ilce.lower() in baslik_lower:
            return ilce
    return ""


def onem_hesapla(baslik: str, kategori: str) -> int:
    return ONEM_SKORU_MAP.get(kategori, 5)
