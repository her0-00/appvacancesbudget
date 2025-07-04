import streamlit as st
import pandas as pd
import datetime
import io
import altair as alt
import plotly.express as px
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="SubvenTrack Pro", layout="wide")
st.title("🏖️  Vacation Expense Tracker")

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
        "grant_acquired": "💶 Subvention acquise",
        "to_pay": "💳 Montant réel à payer"
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
        "grant_acquired": "💶 Grant acquired",
        "to_pay": "💳 Amount you’ll actually pay"
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

max_sub = base * (1-cpp)
plafond = base

# --- SESSION STATE ---
if "depenses" not in st.session_state:
    st.session_state.depenses = pd.DataFrame(columns=["Date", "Catégorie", "Montant (€)", "Dépense (€)"])

# --- AJOUT DE DÉPENSE ---
st.subheader(t["add_expense"])
with st.form("ajouter_depense"):
    montant = st.number_input(t["amount"], min_value=0.0, step=1.0)
    categorie = st.selectbox(t["category"], ["🏨 Hébergement", "✈️ Transport", "🍽️ Nourriture", "🎟️ Activité", "🛍️ Autre"])
    date = st.date_input(t["date"], value=datetime.date.today())
    submit = st.form_submit_button(t["add"])

if submit:
    subvention = montant * (1 - cpp) + 17
    depense_reelle = montant - subvention
    nouvelle = {
        "Date": date,
        "Catégorie": categorie,
        "Montant (€)": montant,
        "Dépense (€)": depense_reelle
    }
    st.session_state.depenses = pd.concat([st.session_state.depenses, pd.DataFrame([nouvelle])], ignore_index=True)
    st.success("✅ Dépense enregistrée !" if lang == "Français" else "✅ Expense recorded!")
    st.info(f"{t['grant_acquired']} : {subvention:.2f} €")
    st.info(f"{t['to_pay']} : {depense_reelle:.2f} €")

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
total_dep = df_filtered["Dépense (€)"].sum()
ratio = total / plafond if plafond else 0

st.subheader(t["summary"])
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total", f"{total:.2f} €")
col2.metric("Plafond", f"{plafond:.2f} €")
col3.metric("Subvention", f"{max_sub:.2f} €")
col4.metric("Dépense réel", f"{total_dep:.2f} €")
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
    pie_data = df_filtered.groupby("Catégorie")["Montant (€)"].sum().reset_index()
    fig = px.pie(pie_data, names='Catégorie', values='Montant (€)',
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo='percent+label', pull=[0.05]*len(pie_data))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(t["bar_chart"])
    bar = alt.Chart(pie_data).mark_bar(size=40).encode(
        x=alt.X("Catégorie:N", sort='-y', axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Montant (€):Q"),
        tooltip=["Catégorie", "Montant (€)"]
    ).properties(width=700, height=400)
    st.altair_chart(bar)

# --- EXPORT JSON ---
st.subheader(t["save_json"])
if st.button(t["save_json"]):
    json_data = st.session_state.depenses.to_json()
    st.download_button("📥 Télécharger JSON", data=json_data, file_name="depenses.json")

uploaded = st.file_uploader(t["load_json"], type="json")
if uploaded:
    try:
        st.session_state.depenses = pd.read_json(uploaded)
        st.success("✅ Données chargées !" if lang == "Français" else "✅ Data loaded!")
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")

# --- EXPORT EXCEL ---
st.subheader(t["export_excel"])
if st.button(t["export_excel"]):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_filtered.to_excel(writer, index=False, sheet_name="Dépenses")
    st.download_button("📂 Télécharger Excel", data=output.getvalue(), file_name="depenses_vacances.xlsx")

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
    st.download_button("📄 Télécharger PDF", data=pdf_bytes, file_name="synthesevacances.pdf")


