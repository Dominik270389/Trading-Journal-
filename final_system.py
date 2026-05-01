import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- KONFIGURATION ---
st.set_page_config(page_title="VolumeEdge Trading Journal", layout="wide", page_icon="📈")

# Pfade und Dateien
DATEI_NAME = "trading_datenbank.csv"
BILDER_ORDNER = "trade_bilder"
LOGO_DATEI = "logo.png"

# Verzeichnisse erstellen falls nicht vorhanden
if not os.path.exists(BILDER_ORDNER):
    os.makedirs(BILDER_ORDNER)

# --- FUNKTIONEN ---

def daten_laden():
    """Lädt die Datenbank mit allen Spalten inklusive Bildpfaden."""
    spalten = ["Datum", "Uhrzeit", "Symbol", "Richtung", "Strategie", 
               "Ergebnis_Euro", "Emotion", "Kommentar",
               "Bild1", "Bild2", "Bild3", "Bild4"]
    if os.path.exists(DATEI_NAME):
        try:
            df = pd.read_csv(DATEI_NAME)
            # Sicherstellen, dass alle Spalten existieren (Migration)
            for col in spalten:
                if col not in df.columns:
                    df[col] = None
            return df
        except:
            return pd.DataFrame(columns=spalten)
    return pd.DataFrame(columns=spalten)

def daten_speichern(df):
    """Speichert die Daten in die CSV Datei."""
    try:
        df.to_csv(DATEI_NAME, index=False)
        return True
    except PermissionError:
        st.error("⚠️ Datei ist in Excel offen! Bitte schließen.")
        return False

def bild_speichern(uploaded_file):
    """Speichert hochgeladene Bilder lokal ab."""
    if uploaded_file is not None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dateiname = f"{ts}_{uploaded_file.name}"
        pfad = os.path.join(BILDER_ORDNER, dateiname)
        with open(pfad, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return pfad
    return None

# --- UI DESIGN (LOGO BEREICH) ---

col_l, col_m, col_r = st.columns([1, 2, 1])
with col_m:
    if os.path.exists(LOGO_DATEI):
        st.image(LOGO_DATEI, use_container_width=True)
    else:
        st.title("🦅 VolumeEdge Trading") # Fallback

df = daten_laden()

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "✍️ Neuer Trade", "📖 Journal (Bearbeiten & Löschen)", "🧠 Analyse"])

# ==============================================
# TAB 1: DASHBOARD
# ==============================================
with tab1:
    if not df.empty:
        # Metriken (KPIs)
        col1, col2, col3 = st.columns(3)
        gesamtsumme = df["Ergebnis_Euro"].sum()
        winrate = (len(df[df["Ergebnis_Euro"] > 0]) / len(df)) * 100 if len(df) > 0 else 0
        
        col1.metric("Gesamt P/L", f"{gesamtsumme:.2f} €")
        col2.metric("Win Rate", f"{winrate:.1f} %")
        col3.metric("Trades", len(df))
        
        st.markdown("---")
        
        # Performance Curve
        df_chart = df.copy()
        df_chart["TS"] = pd.to_datetime(df_chart["Datum"].astype(str) + " " + df_chart["Uhrzeit"].astype(str))
        df_chart = df_chart.sort_values("TS")
        df_chart["Equity"] = df_chart["Ergebnis_Euro"].cumsum()
        
        fig = px.area(df_chart, x="TS", y="Equity", title="Performance Verlauf", markers=True)
        fig.update_traces(line_color='#70C050', fillcolor='rgba(112, 192, 80, 0.2)') # VolumeEdge Grün
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Noch keine Daten vorhanden.")

# ==============================================
# TAB 2: NEUER TRADE
# ==============================================
with tab2:
    st.subheader("Trade Erfassung")
    with st.form("trade_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 1, 1.5])
        
        with c1:
            datum = st.date_input("Datum", datetime.now())
            uhrzeit = st.time_input("Uhrzeit", datetime.now().time())
            markt = st.text_input("Markt", "ES / DAX")
            richtung = st.selectbox("Richtung", ["Long", "Short"])
        
        with c2:
            strat = st.selectbox("Strategie", ["Volume Trend", "Edge Breakout", "Flow Reversal"])
            ergebnis = st.number_input("Ergebnis (€)", step=10.0)
            emotion = st.selectbox("Emotion", ["Neutral 😐", "Fokussiert 😌", "Gierig 🤑", "Angst 😨"])
            kommentar = st.text_area("Notizen")
            
        with c3:
            st.write("📸 **Screenshots (max. 4)**")
            up1 = st.file_uploader("Bild 1", type=['png', 'jpg'], key="u1")
            up2 = st.file_uploader("Bild 2", type=['png', 'jpg'], key="u2")
            up3 = st.file_uploader("Bild 3", type=['png', 'jpg'], key="u3")
            up4 = st.file_uploader("Bild 4", type=['png', 'jpg'], key="u4")
            
        if st.form_submit_button("💾 TRADE SPEICHERN", type="primary"):
            p1 = bild_speichern(up1)
            p2 = bild_speichern(up2)
            p3 = bild_speichern(up3)
            p4 = bild_speichern(up4)
            
            neuer_trade = pd.DataFrame([{
                "Datum": datum, "Uhrzeit": uhrzeit, "Symbol": markt, "Richtung": richtung,
                "Strategie": strat, "Ergebnis_Euro": ergebnis, "Emotion": emotion,
                "Kommentar": kommentar, "Bild1": p1, "Bild2": p2, "Bild3": p3, "Bild4": p4
            }])
            
            df = pd.concat([df, neuer_trade], ignore_index=True)
            if daten_speichern(df):
                st.success("Trade gespeichert!")
                st.rerun()

# ==============================================
# TAB 3: JOURNAL (BEARBEITEN & LÖSCHEN)
# ==============================================
with tab3:
    if not df.empty:
        st.subheader("Journal-Verwaltung")
        
        # Schnell-Edit Tabelle
        st.write("📝 **Tabellen-Werte bearbeiten:**")
        edit_cols = ["Datum", "Uhrzeit", "Symbol", "Richtung", "Strategie", "Ergebnis_Euro", "Emotion", "Kommentar"]
        edited_df_part = st.data_editor(df[edit_cols], use_container_width=True)
        
        if st.button("💾 Alle Tabellen-Änderungen speichern"):
            for col in edit_cols:
                df[col] = edited_df_part[col]
            daten_speichern(df)
            st.success("Änderungen übernommen!")
            st.rerun()
            
        st.markdown("---")
        
        # Trade markieren für Details/Löschen
        st.write("🔍 **Trade auswählen für Bilder & Löschen:**")
        auswahl_texte = df.apply(lambda x: f"ID {x.name}: {x['Datum']} | {x['Symbol']} | {x['Ergebnis_Euro']}€", axis=1)
        idx = st.selectbox("Trade markieren", options=auswahl_texte.index, format_func=lambda x: auswahl_texte[x])
        
        trade_sel = df.iloc[idx]
        
        # Löschen Button
        if st.button("🗑️ Markierten Trade löschen", type="primary"):
            df = df.drop(idx).reset_index(drop=True)
            daten_speichern(df)
            st.rerun()
            
        # Bilder Anzeige
        st.write("🖼️ **Zugehörige Bilder:**")
        img_cols = st.columns(4)
        for i, b_col in enumerate(["Bild1", "Bild2", "Bild3", "Bild4"]):
            img_path = trade_sel[b_col]
            if img_path and os.path.exists(str(img_path)):
                img_cols[i].image(img_path, caption=f"Bild {i+1}", use_container_width=True)
            else:
                img_cols[i].info(f"Kein Bild {i+1}")
    else:
        st.info("Journal ist noch leer.")

# ==============================================
# TAB 4: ANALYSE
# ==============================================
with tab4:
    if not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            strat_perf = df.groupby("Strategie")["Ergebnis_Euro"].sum().reset_index()
            st.plotly_chart(px.bar(strat_perf, x="Strategie", y="Ergebnis_Euro", title="P/L nach Strategie", color="Strategie"), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(df, names="Emotion", title="Emotions-Verteilung"), use_container_width=True)