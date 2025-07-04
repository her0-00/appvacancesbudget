import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import io
from fpdf import FPDF
import altair as alt

# --- CONFIGURATION ---
st.set_page_config(page_title="SubvenTrack Pro", layout="wide")
st.title("🏖️ SubvenTrack Pro – Vacation Expense Tracker")

# --- LANGUES ---
translations = {
    "Français": {
        "params": "🔧 Paramètres CSE",
        "add_expense": "🛒 Ajouter une dépense",
        "history": "📋 Historique",
        "summary": "📊 Synthèse",
        "category": "Catégorie",
        "amount": "Montant (€)",
        "date": "Date",
        "add": "✅ Ajouter",
        "alert_max": "🚨 Dépassement du plafond !",
        "alert_near": "⚠️ Tu approches du plafond autorisé !",
        "alert_ok": "✅ Tout est sous contrôle !",
        "bar_chart": "📊 Graphique en barres",
        "pie_chart": "📈 Répartition par catégorie",
        "save_json": "💾 Sauvegarder les données",
        "load_json": "📤 Charger des dépenses",
        "export_excel": "📁 Export Excel",
        "export_pdf": "📄 Export PDF",
        "date_range": "📆 Filtrer par période",
    },
    "English": {
        "params": "🔧 CSE Settings",
        "add_expense": "🛒 Add Expense",
        "history": "📋 History",
        "summary": "📊 Summary",
        "category": "Category",
        "amount": "Amount (€)",
        "date": "Date",
        "add": "✅ Add",
        "alert_max": "🚨 Limit exceeded!",
        "alert_near": "⚠️ Approaching your spending limit!",
        "alert_ok": "✅ You're within budget!",
        "bar_chart": "📊 Bar Chart",
        "pie_chart": "📈 Spending Breakdown",
        "save_json": "💾 Save Data",
        "load_json": "📤 Load Expenses",
        "export_excel": "📁 Export Excel",
        "export_pdf": "📄 Export PDF",
        "date_range": "📆 Filter by Date Range",
    }
}

# --- SIDEBAR ---
st.sidebar.header("🌐 Choisir la langue | Select language")
lang = st.sidebar.selectbox("Langue | Language", ["Français", "English"])
t = translations[lang]

st.sidebar.header(t["params"])
base = st.sidebar.number_input("Base de calcul (€)", value=2400)
cpp = st.sidebar.number_input("Coefficient CPP", value=0.479, format="%.3f")
seuil = st.sidebar.slider("Seuil d'alerte (%)", min_value=70, max_value=100, value=90)

# --- CALCULS ---
max_sub = base * cpp
plafond = base 

# --- SESSION STATE ---
if "depenses" not in st.session_state:
    st.session_state.depenses = pd.DataFrame(columns=["Date", "Catégorie", "Montant (€)"])

# --- AJOUT DE DÉPENSE ---
st.subheader(t["add_expense"])
with st.form("ajouter_depense"):
    montant = st.number_input(t["amount"], min_value=0.0, step=1.0)
    categorie = st.selectbox(t["category"], ["🏨 Hébergement", "✈️ Transport", "🍽️ Nourriture", "🎟️ Activité", "🛍️ Autre"])
    date = st.date_input(t["date"], value=datetime.date.today())
    submit = st.form_submit_button(t["add"])

if submit:
    nouvelle = {"Date": date, "Catégorie": categorie, "Montant (€)": montant}
    st.session_state.depenses = pd.concat([st.session_state.depenses, pd.DataFrame([nouvelle])], ignore_index=True)
    st.success("✅ Dépense enregistrée !" if lang == "Français" else "✅ Expense recorded!")

# --- FILTRAGE PAR DATE ---
st.subheader(t["date_range"])
start_date = st.date_input("Date de début", datetime.date.today() - datetime.timedelta(days=30))
end_date = st.date_input("Date de fin", datetime.date.today())
df_filtered = st.session_state.depenses[
    (pd.to_datetime(st.session_state.depenses["Date"]) >= pd.to_datetime(start_date)) &
    (pd.to_datetime(st.session_state.depenses["Date"]) <= pd.to_datetime(end_date))
]

# --- HISTORIQUE ---
st.subheader(t["history"])
st.dataframe(df_filtered.sort_values("Date", ascending=False), use_container_width=True)

# --- SYNTHÈSE ---
total = df_filtered["Montant (€)"].sum()
ratio = total / plafond
st.subheader(t["summary"])
col1, col2, col3 = st.columns(3)
col1.metric("Total", f"{total:.2f} €")
col2.metric("Plafond", f"{plafond:.2f} €")
col3.metric("Subvention", f"{max_sub:.2f} €")
st.progress(min(ratio, 1.0))

# --- ALERTES ---
if total >= plafond:
    st.error(t["alert_max"])
elif total >= plafond * seuil / 100:
    st.warning(t["alert_near"])
else:
    st.info(t["alert_ok"])

# --- GRAPHIQUES ---
if not df_filtered.empty:
    st.subheader(t["pie_chart"])
    fig, ax = plt.subplots()
    df_filtered.groupby("Catégorie")["Montant (€)"].sum().plot.pie(autopct="%1.1f%%", ax=ax, figsize=(6, 6))
    st.pyplot(fig)

    st.subheader(t["bar_chart"])
    bar = alt.Chart(df_filtered).mark_bar().encode(
        x=alt.X("Catégorie", sort='-y'),
        y="sum(Montant (€))",
        tooltip=["Catégorie", "sum(Montant (€))"]
    ).properties(width=600, height=400)
    st.altair_chart(bar)

# --- SAUVEGARDE JSON ---
st.subheader(t["save_json"])
if st.button(t["save_json"]):
    json_data = st.session_state.depenses.to_json()
    st.download_button("📥 Télécharger JSON", data=json_data, file_name="depenses.json")

uploaded = st.file_uploader(t["load_json"], type="json")
if uploaded:
    st.session_state.depenses = pd.read_json(uploaded)
    st.success("✅ Données chargées !" if lang == "Français" else "✅ Data loaded!")

# --- EXPORT EXCEL ---
st.subheader(t["export_excel"])
if st.button(t["export_excel"]):
    excel_output = io.BytesIO()
    with pd.ExcelWriter(excel_output, engine="xlsxwriter") as writer:
        df_filtered.to_excel(writer, index=False, sheet_name="Dépenses")
    st.download_button("📂 Télécharger Excel", data=excel_output.getvalue(), file_name="depenses_vacances.xlsx")

# --- EXPORT PDF ---
def generate_pdf(df, total, plafond):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Résumé des Dépenses – SubvenTrack Pro", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total : {total:.2f} € / Plafond : {plafond:.2f} €", ln=True)
    pdf.ln(5)
    for _, row in df.iterrows():
        pdf.cell(200, 8, txt=f"{row['Date']} - {row['Catégorie']} - {row['Montant (€)']} €", ln=True)
    return pdf.output(dest='S').encode('latin-1')

st.subheader(t["export_pdf"])
if st.button(t["export_pdf"]):
    pdf_bytes = generate_pdf(df_filtered, total, plafond)
    st.download_button("📄 Télécharger PDF", data=pdf_bytes, file_name="rapport_vacances.pdf")
