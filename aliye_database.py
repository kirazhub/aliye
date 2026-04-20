from typing import Optional, List, Dict, Any
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger("aliye_database")
DB_PATH = str(Path(__file__).parent / "aliye.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS haberler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baslik TEXT NOT NULL,
                ozet TEXT DEFAULT '',
                url TEXT UNIQUE,
                kaynak TEXT,
                kategori TEXT DEFAULT 'Yatırım',
                ilce TEXT DEFAULT '',
                tarih TEXT,
                onem_skoru INTEGER DEFAULT 5
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kanunlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baslik TEXT NOT NULL,
                ozet TEXT DEFAULT '',
                url TEXT UNIQUE,
                tarih TEXT,
                resmi_gazete_no TEXT DEFAULT ''
            )
        """)
        conn.commit()
    logger.info("Veritabanı tabloları hazır.")

def haber_ekle(baslik: str, ozet: str, url: str, kaynak: str,
               kategori: str, ilce: str, tarih: str, onem_skoru: int) -> bool:
    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO haberler (baslik, ozet, url, kaynak, kategori, ilce, tarih, onem_skoru)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (baslik, ozet, url, kaynak, kategori, ilce, tarih, onem_skoru))
            conn.commit()
            return conn.total_changes > 0
    except Exception as e:
        logger.error(f"Haber ekleme hatası: {e}")
        return False

def get_haberler(limit: int = 100, kategori: Optional[str] = None, 
                  ilce: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        query = "SELECT * FROM haberler"
        params: List[Any] = []
        where: List[str] = []
        
        if kategori:
            where.append("kategori = ?")
            params.append(kategori)
        if ilce:
            where.append("ilce LIKE ?")
            params.append(f"%{ilce}%")
        
        if where:
            query += " WHERE " + " AND ".join(where)
        
        # En yeni haberler yukarıda (aşağı doğru akan feed)
        query += """
            ORDER BY 
                tarih DESC,
                onem_skoru DESC,
                id DESC
            LIMIT ?
        """
        params.append(limit)
        
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

def get_kanunlar(limit: int = 50) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM kanunlar ORDER BY tarih DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

def get_ilce_stats() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT ilce, COUNT(*) as count, MAX(tarih) as son_tarih
            FROM haberler 
            WHERE ilce != ''
            GROUP BY ilce 
            ORDER BY 
                CASE 
                    WHEN ilce LIKE '%Göktürk%' THEN 1
                    WHEN ilce LIKE '%Kemerburgaz%' THEN 2
                    WHEN ilce LIKE '%Eyüp%' THEN 3
                    WHEN ilce LIKE '%Trakya%' OR ilce LIKE '%Edirne%' OR ilce LIKE '%Tekirdağ%' THEN 4
                    ELSE 5
                END,
                count DESC
        """).fetchall()
        return [dict(r) for r in rows]

def get_kategori_stats() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT kategori, COUNT(*) as count 
            FROM haberler GROUP BY kategori ORDER BY count DESC
        """).fetchall()
        return [dict(r) for r in rows]

def tablolari_olustur() -> None:
    init_db()
