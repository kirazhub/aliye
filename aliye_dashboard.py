import streamlit as st
import pandas as pd
import plotly.express as px
import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from aliye_database import get_haberler, get_kanunlar, get_kategori_stats as get_stats, get_ilce_stats, init_db
from aliye_config import KATEGORILER, ILCELER, GYO_SEMBOLLER

logger = logging.getLogger(__name__)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🏙️ ALİYE — İstanbul Emlak",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auto-refresh (5 min) ─────────────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5 * 60 * 1000, key="aliye_refresh")
except ImportError:
    pass  # gracefully skip if package not installed

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ---- base dark ---- */
.stApp { background-color: #0e1117; color: #e0e0e0; }

/* ---- news cards ---- */
.card-red {
    border-left: 5px solid #e53935;
    background: #1c1114;
    padding: 12px 16px; margin: 8px 0; border-radius: 5px;
}
.card-orange {
    border-left: 5px solid #fb8c00;
    background: #1c1610;
    padding: 12px 16px; margin: 8px 0; border-radius: 5px;
}
.card-gray {
    border-left: 5px solid #555;
    background: #141720;
    padding: 12px 16px; margin: 8px 0; border-radius: 5px;
}
.card-title {
    font-weight: 700; font-size: 1.05em; color: #f0f0f0; margin-bottom: 5px;
}
.card-ozet {
    color: #aaa; font-size: 0.88em; margin-bottom: 8px;
}
.badge-kaynak {
    display: inline-block;
    background: #1e2a4a; color: #7fa8ff;
    padding: 2px 9px; border-radius: 10px; font-size: 0.78em;
    margin-right: 6px;
}
.badge-ilce {
    display: inline-block;
    background: #1a3028; color: #66bb6a;
    padding: 2px 9px; border-radius: 10px; font-size: 0.78em;
    margin-right: 6px;
}
.badge-kat {
    display: inline-block;
    background: #2a2040; color: #ce93d8;
    padding: 2px 9px; border-radius: 10px; font-size: 0.78em;
    margin-right: 6px;
}
.meta-text { color: #666; font-size: 0.78em; margin-right: 6px; }
.haber-link { color: #4a9eff; font-size: 0.82em; text-decoration: none; }
.haber-link:hover { text-decoration: underline; }

/* ---- legal cards ---- */
.card-legal {
    border: 1px solid #7b6200;
    border-left: 6px solid #fdd835;
    background: #18150a;
    padding: 14px 18px; margin: 10px 0; border-radius: 5px;
}
.legal-title { font-weight: 700; font-size: 1.08em; color: #fff59d; }

/* ---- ilçe mini cards ---- */
.ilce-mini {
    border: 1px solid #2a3040; background: #141720;
    padding: 10px 12px; margin: 5px 0; border-radius: 5px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── DB init ───────────────────────────────────────────────────────────────────
init_db()


# ── Helper: build a news card HTML ───────────────────────────────────────────
def card_html(haber: Dict[str, Any], show_kat: bool = True) -> str:
    onem: int = int(haber.get("onem_skoru", 5))
    if onem >= 8:
        css_class = "card-red"
    elif onem >= 6:
        css_class = "card-orange"
    else:
        css_class = "card-gray"

    baslik = str(haber.get("baslik", ""))[:250]
    ozet = str(haber.get("ozet", ""))[:220]
    kaynak = str(haber.get("kaynak", ""))
    ilce = str(haber.get("ilce", ""))
    kategori = str(haber.get("kategori", ""))
    tarih = str(haber.get("tarih", ""))[:10]
    url = str(haber.get("url", "#"))

    ilce_badge = f'<span class="badge-ilce">{ilce}</span>' if ilce else ""
    kat_badge = (
        f'<span class="badge-kat">{kategori}</span>'
        if (show_kat and kategori)
        else ""
    )

    return (
        f'<div class="{css_class}">'
        f'<div class="card-title">{baslik}</div>'
        f'<div class="card-ozet">{ozet}</div>'
        f'<span class="badge-kaynak">{kaynak}</span>'
        f"{ilce_badge}{kat_badge}"
        f'<span class="meta-text">{tarih}</span>'
        f'<a class="haber-link" href="{url}" target="_blank">→ Habere Git</a>'
        f"</div>"
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏙️ ALİYE")
    st.caption("İstanbul Emlak İstihbarat Ajanı")
    st.markdown("---")

    page = st.radio(
        "Sayfa",
        [
            "🏙️ Son Haberler",
            "⚖️ Kanunlar & Mevzuat",
            "🗺️ İlçe Analizi",
            "📊 İstatistikler",
            "🏢 GYO Takibi",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption(f"Son yenileme: {datetime.now().strftime('%H:%M')}")
    if st.button("🔄 Yenile"):
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Son Haberler
# ══════════════════════════════════════════════════════════════════════════════
def page_son_haberler() -> None:
    st.title("🏙️ ALİYE — İstanbul Emlak İstihbarat Ajanı")
    st.markdown("---")

    col_kat, col_ilce = st.columns([3, 2])
    with col_kat:
        secili_kategoriler: List[str] = st.multiselect(
            "Kategori",
            options=KATEGORILER,
            placeholder="Tüm kategoriler",
        )
    with col_ilce:
        secili_ilce: str = st.selectbox(
            "İlçe",
            options=["Tümü"] + ILCELER,
        )

    haberler = get_haberler(limit=200)

    # Apply filters
    if secili_kategoriler:
        haberler = [h for h in haberler if h.get("kategori") in secili_kategoriler]
    if secili_ilce != "Tümü":
        haberler = [h for h in haberler if h.get("ilce") == secili_ilce]

    haberler = haberler[:100]

    if not haberler:
        st.info(
            "Henüz haber bulunamadı. `python aliye_main.py` çalışıyor mu kontrol edin."
        )
        return

    st.markdown(f"**{len(haberler)} haber**")
    st.markdown("---")

    for h in haberler:
        st.markdown(card_html(h), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Kanunlar & Mevzuat
# ══════════════════════════════════════════════════════════════════════════════
def page_kanunlar() -> None:
    st.title("⚖️ Kanunlar & Mevzuat")
    st.markdown("---")

    kanunlar = get_kanunlar(limit=100)
    if not kanunlar:
        kanunlar = get_haberler(kategori="Kanunlar", limit=100)

    if not kanunlar:
        st.info("Henüz kanun/mevzuat haberi bulunamadı.")
        return

    st.markdown(f"**{len(kanunlar)} mevzuat haberi**")
    st.markdown("---")

    for k in kanunlar:
        baslik = str(k.get("baslik", ""))[:250]
        ozet = str(k.get("ozet", ""))[:220]
        kaynak = str(k.get("kaynak", ""))
        tarih = str(k.get("tarih", ""))[:10]
        url = str(k.get("url", "#"))
        resmi_gazete = str(k.get("resmi_gazete_no", "") or "")

        rg_block = (
            f'<div style="color:#fdd835;font-size:0.85em;margin:4px 0;">📋 RG No: {resmi_gazete}</div>'
            if resmi_gazete
            else ""
        )

        st.markdown(
            f'<div class="card-legal">'
            f'<div class="legal-title">{baslik}</div>'
            f'<div style="color:#bbb;font-size:0.9em;margin:6px 0">{ozet}</div>'
            f"{rg_block}"
            f'<span class="badge-kaynak">{kaynak}</span>'
            f'<span class="meta-text">{tarih}</span>'
            f'<a class="haber-link" href="{url}" target="_blank">→ Habere Git</a>'
            f"</div>",
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — İlçe Analizi
# ══════════════════════════════════════════════════════════════════════════════
def page_ilce_analizi() -> None:
    st.title("🗺️ İlçe Analizi")
    st.markdown("---")

    haberler = get_haberler(limit=1000)

    if not haberler:
        st.info("Henüz haber bulunamadı.")
        return

    ilce_counts: Dict[str, int] = {}
    ilce_son: Dict[str, str] = {}

    for h in haberler:
        ilce = str(h.get("ilce", ""))
        if ilce:
            ilce_counts[ilce] = ilce_counts.get(ilce, 0) + 1
            if ilce not in ilce_son:
                ilce_son[ilce] = str(h.get("baslik", ""))[:80]

    if ilce_counts:
        sorted_ilceler = sorted(ilce_counts.items(), key=lambda x: x[1], reverse=True)
        df_ilce = pd.DataFrame(sorted_ilceler, columns=["İlçe", "Haber Sayısı"])

        fig = px.bar(
            df_ilce,
            x="İlçe",
            y="Haber Sayısı",
            title="İlçelere Göre Haber Frekansı",
            color="Haber Sayısı",
            color_continuous_scale="Blues",
            template="plotly_dark",
        )
        fig.update_layout(xaxis_tickangle=-40, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("İlçe Bazlı Son Haberler")

        cols = st.columns(3)
        for idx, (ilce, count) in enumerate(sorted_ilceler):
            with cols[idx % 3]:
                st.markdown(
                    f'<div class="ilce-mini">'
                    f'<div style="color:#66bb6a;font-weight:700">{ilce}</div>'
                    f'<div style="color:#888;font-size:0.82em">{count} haber</div>'
                    f'<div style="color:#aaa;font-size:0.78em;margin-top:4px">{ilce_son.get(ilce,"")}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.info("İlçe etiketli haber bulunamadı.")

    no_news = [il for il in ILCELER if il not in ilce_counts]
    if no_news:
        st.markdown("---")
        st.caption(f"Haber bulunmayan ilçeler: {', '.join(no_news)}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — İstatistikler
# ══════════════════════════════════════════════════════════════════════════════
def page_istatistikler() -> None:
    st.title("📊 İstatistikler")
    st.markdown("---")

    stats = get_stats()

    if stats["total"] == 0:
        st.info("Henüz haber bulunamadı.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Haber", stats["total"])
    c2.metric("Kategori Sayısı", len(stats["by_category"]))
    c3.metric("Aktif İlçe", len(stats["by_ilce"]))

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        if stats["by_category"]:
            df_cat = pd.DataFrame(
                list(stats["by_category"].items()), columns=["Kategori", "Sayı"]
            )
            fig_pie = px.pie(
                df_cat,
                values="Sayı",
                names="Kategori",
                title="Kategorilere Göre Dağılım",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

    with right:
        if stats["by_day"]:
            sorted_days = sorted(stats["by_day"].items())
            df_day = pd.DataFrame(sorted_days, columns=["Tarih", "Sayı"])
            fig_day = px.bar(
                df_day,
                x="Tarih",
                y="Sayı",
                title="Son 30 Gün — Günlük Haber Sayısı",
                template="plotly_dark",
                color_discrete_sequence=["#4a9eff"],
            )
            fig_day.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_day, use_container_width=True)

    st.markdown("---")
    st.subheader("En Sık Geçen Kelimeler (Top 20)")

    haberler = get_haberler(limit=500)
    if haberler:
        all_text = " ".join(str(h.get("baslik", "")) for h in haberler)
        raw_words = re.findall(r"\w{4,}", all_text, re.UNICODE)

        STOP_WORDS = {
            "olan", "için", "daha", "çok", "gibi", "kadar", "bile",
            "veya", "iken", "ile", "yani", "nasıl", "neden", "sonra",
            "önce", "haber", "biri", "diğer", "şekilde", "olarak",
            "üzere", "ancak", "fakat", "lakin", "zira", "çünkü",
            "buna", "bunun", "bunlar", "şunu", "onun", "onlar",
            "yeni", "artık", "ayrıca", "kendi", "hangi", "bazı",
            "tüm", "her", "oldu", "olmak", "yapılan", "yapılacak",
            "edilen", "eden", "olacak", "gelen", "edilen", "olan",
            "olarak", "üzerinde", "birlikte", "göre", "karşı",
        }

        word_freq: Dict[str, int] = {}
        for word in raw_words:
            w = word.lower()
            if w not in STOP_WORDS:
                word_freq[w] = word_freq.get(w, 0) + 1

        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        if top_words:
            df_words = pd.DataFrame(top_words, columns=["Kelime", "Sıklık"])
            fig_words = px.bar(
                df_words,
                x="Kelime",
                y="Sıklık",
                title="En Sık Geçen 20 Kelime",
                template="plotly_dark",
                color="Sıklık",
                color_continuous_scale="Viridis",
            )
            fig_words.update_layout(xaxis_tickangle=-45, showlegend=False)
            st.plotly_chart(fig_words, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — GYO Takibi
# ══════════════════════════════════════════════════════════════════════════════
def page_gyo_takibi() -> None:
    st.title("🏢 GYO Takibi")
    st.markdown("---")

    st.subheader("GYO Hisse Fiyatları (Borsa İstanbul)")

    gyo_rows: List[Dict[str, Any]] = []

    with st.spinner("Piyasa verileri alınıyor..."):
        try:
            import yfinance as yf

            for sembol in GYO_SEMBOLLER:
                try:
                    ticker = yf.Ticker(sembol)
                    hist = ticker.history(period="2d")

                    if hist is not None and not hist.empty:
                        close_price: float = float(hist["Close"].iloc[-1])
                        volume: int = int(hist["Volume"].iloc[-1])

                        if len(hist) >= 2:
                            prev: float = float(hist["Close"].iloc[-2])
                            change_pct: float = (
                                ((close_price - prev) / prev * 100) if prev else 0.0
                            )
                        else:
                            change_pct = 0.0

                        arrow = "▲" if change_pct >= 0 else "▼"
                        gyo_rows.append({
                            "Sembol": sembol,
                            "Fiyat (TL)": f"{close_price:.2f}",
                            "Değişim": f"{arrow} {change_pct:+.2f}%",
                            "Hacim": f"{volume:,}",
                            "Durum": "✅",
                        })
                    else:
                        gyo_rows.append({
                            "Sembol": sembol,
                            "Fiyat (TL)": "—",
                            "Değişim": "—",
                            "Hacim": "—",
                            "Durum": "❌",
                        })
                except Exception as exc:
                    logger.error("GYO fetch error %s: %s", sembol, exc)
                    gyo_rows.append({
                        "Sembol": sembol,
                        "Fiyat (TL)": "—",
                        "Değişim": "—",
                        "Hacim": "—",
                        "Durum": "❌",
                    })

        except ImportError:
            st.error("yfinance kurulu değil. `pip install yfinance` çalıştırın.")

    if gyo_rows:
        st.dataframe(
            pd.DataFrame(gyo_rows),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")
    st.subheader("GYO Haberleri")

    gyo_haberler = get_haberler(kategori="GYO Haberleri", limit=30)

    if not gyo_haberler:
        # Fallback: search all haberler for GYO keywords
        all_h = get_haberler(limit=300)
        gyo_kws = ["GYO", "EKGYO", "ISGYO", "TRGYO", "OZGYO", "VKGYO", "ALKIM"]
        gyo_haberler = []
        for h in all_h:
            baslik = str(h.get("baslik", ""))
            found = False
            for kw in gyo_kws:
                if kw in baslik:
                    found = True
                    break
            if found:
                gyo_haberler.append(h)
                if len(gyo_haberler) >= 20:
                    break

    if gyo_haberler:
        for h in gyo_haberler:
            st.markdown(card_html(h), unsafe_allow_html=True)
    else:
        st.info("Henüz GYO haberi bulunamadı.")


# ── Route ─────────────────────────────────────────────────────────────────────
if page == "🏙️ Son Haberler":
    page_son_haberler()
elif page == "⚖️ Kanunlar & Mevzuat":
    page_kanunlar()
elif page == "🗺️ İlçe Analizi":
    page_ilce_analizi()
elif page == "📊 İstatistikler":
    page_istatistikler()
elif page == "🏢 GYO Takibi":
    page_gyo_takibi()
