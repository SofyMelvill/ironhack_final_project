import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Madeira Crop & Funding Advisor", layout="wide")

# ===== Carregar dados =====
@st.cache_data
def load_data():
    df = pd.read_excel(
        r"C:\Users\sofia\Documents\Data_Analytics_Ironhack\Projects\ironhack_final_project\Worked_datasets\dataset_tableau.xlsx"
    )
    return df

df = load_data()

with open("pepac.json", "r", encoding="utf-8") as f:
    pepac = json.load(f)

# ===== Funções =====
def recommend_lines(age, start, modernize, transform, collective,
                    access, calamity, landscape, insurance, pepac):
    results = []
    if age < 40 and start: results.append(("F.4.1", pepac["F.4.1"]))
    if age < 40 and not start: results.append(("F.1.2", pepac["F.1.2"]))
    if modernize: results.append(("F.1.1", pepac["F.1.1"]))
    if transform: results.append(("F.1.3", pepac["F.1.3"]))
    if collective: results.append(("F.1.4", pepac["F.1.4"]))
    if access: results.append(("F.1.5", pepac["F.1.5"]))
    if calamity: results.append(("F.1.6", pepac["F.1.6"]))
    if landscape: results.append(("F.1.7", pepac["F.1.7"]))
    if insurance: results.append(("F.5.1", pepac["F.5.1"]))
    if not results:
        results.append((None, {"name": "Not applicable", "objective": "No clear line"}))
    return results

def estimate_score(ph_min, ph_max, sol_min, df_ref):
    mask = (
        (df_ref["ph_min"] <= ph_max) &
        (df_ref["ph_max"] >= ph_min) &
        (df_ref["sol_min"].fillna(0) <= sol_min)
    )
    similares = df_ref[mask]
    if not similares.empty:
        return similares["score_agro"].mean()
    else:
        return None

def auto_recommend(cultura, df, pepac, categoria_override=None):
    """Sugere linhas com base na categoria da cultura ou manual (override)."""
    if categoria_override:
        categoria = categoria_override
    else:
        row = df[df["Cultura"] == cultura]
        if row.empty:
            return []
        categoria = row["categoria"].iloc[0]

    mapping = {
        "Frutos": ["F.1.1", "F.1.3"],
        "Plantas Industriais": ["F.1.1", "F.1.5"],
        "Vegetais e Produtos Hortícolas": ["F.1.1", "F.1.4"],
        "Plantas e flores": ["F.1.7"],
    }

    codes = mapping.get(categoria, [])
    return [(c, pepac[c]) for c in codes if c in pepac]


# ===== UI =====

st.title("🌱 Crop Genie")
st.markdown("Decision pipeline: **Agronomy → Economy → Funding**")

# --- Input inicial ---
st.header("🔹 Input data")
mode = st.radio("Input type:", ["Select existing crop", "Add new crop"])

if mode == "Select existing crop":
    cultura = st.selectbox("Choose crop:", sorted(df["Cultura"].unique()))
    dados_cultura = df[df["Cultura"] == cultura]
    score_agro = dados_cultura["score_agro"].mean() if not dados_cultura.empty else None

else:  # Add new crop
    cultura = st.text_input("Enter crop name")
    ph_min = st.number_input("Min pH", 3.0, 9.0, 6.0)
    ph_max = st.number_input("Max pH", 3.0, 9.0, 7.0)
    sol_min = st.number_input("Min sunlight (h/day)", 0.0, 15.0, 8.0)
    categoria_new = st.selectbox(
        "Select category",
        ["Frutos", "Plantas Industriais", "Vegetais e Produtos Hortícolas", "Plantas e flores", "Other"]
    )
    score_agro = estimate_score(ph_min, ph_max, sol_min, df) if cultura else None


area = st.number_input("Area (ha)", min_value=0.1, max_value=100.0, step=0.1)
if area < 0.25:
    st.error("❌ Minimum area required: 0.25 ha")
    st.stop()

custos = st.number_input("Operational costs per ha (€)", min_value=100.0, max_value=50000.0, step=100.0)

# ==========================
# Passo 1: Agronomic viability
# ==========================
st.header("1️⃣ Agronomic viability")

if score_agro is not None:
    st.metric("Agronomic Score", f"{score_agro:.2f}")
    if score_agro >= 0.75:
        st.success("✅ Good match with Madeira conditions")
    elif score_agro >= 0.5:
        st.warning("⚠️ Partial match (risks exist)")
    else:
        st.error("❌ Poor match (not recommended)")
else:
    if mode == "Add new crop" and cultura:
        st.error("❌ Agronomically not viable in Madeira conditions")

# ==========================
# Passo 2: Economic viability
# ==========================
st.header("2️⃣ Economic viability")

if score_agro is not None:
    if mode == "Select existing crop":
        preco_medio = dados_cultura["Preco"].mean()
        prod_media = dados_cultura["Producao"].mean()
    else:
        preco_medio = df["Preco"].mean()
        prod_media = df["Producao"].mean()

    receita_bruta = preco_medio * prod_media * area / 100
    receita_ajustada = receita_bruta * score_agro if score_agro else 0
    lucro = receita_ajustada - (custos * area)

    st.metric("Estimated Profit", f"{lucro:,.0f} €")

    if score_agro >= 0.75 and lucro > 0:
        st.success(f"✅ {cultura}: High economic viability")
    elif score_agro >= 0.5 and lucro > 0:
        st.warning(f"⚠️ {cultura}: Medium viability (risk exists)")
    else:
        st.error(f"❌ {cultura}: Not economically viable")

else:
    st.info("No economic calculation possible without agronomic score.")

# ==========================
# Passo 3: Funding suggestions
# ==========================
st.header("3️⃣ Funding advisor")

# Sugestões automáticas
auto_lines = auto_recommend(cultura, df, pepac)
if auto_lines:
    st.markdown("**Suggested based on crop category:**")
    for code, line in auto_lines:
        st.markdown(f"**{code} – {line['name']}**")
        st.write("Objective:", line["objective"])
        st.write("Support:", line.get("support", "N/A"))
        st.markdown("---")

# Refinamento manual
age = st.number_input("Farmer age", 18, 100, 30)
start = st.checkbox("Starting new farm?")
modernize = st.checkbox("Modernize existing farm?")
transform = st.checkbox("Processing/marketing products?")
collective = st.checkbox("Collective irrigation project?")
access = st.checkbox("Need agricultural access?")
calamity = st.checkbox("Affected by natural disaster?")
landscape = st.checkbox("Non-productive investment?")
insurance = st.checkbox("Has/Plans insurance?")

if st.button("🔍 Refine funding recommendations"):
    lines = recommend_lines(age, start, modernize, transform,
                            collective, access, calamity, landscape,
                            insurance, pepac)
    st.markdown("**Refined suggestions:**")
    for code, line in lines:
        st.markdown(f"**{code if code else 'N/A'} – {line['name']}**")
        st.write("Objective:", line["objective"])
        st.write("Support:", line.get("support", "N/A"))
        with st.expander("Criteria details"):
            for c in line.get("criteria", []):
                st.markdown(f"- {c}")
        st.markdown("---")

## ==========================
# Final Recommendation
# ==========================

st.header("4️⃣ Final Decision")

if score_agro is not None:
    st.write(f"**Crop selected:** {cultura}")
    st.write(f"Agronomic Score: {score_agro:.2f}")
    st.write(f"Estimated Profit: **{lucro:,.0f} €**")

    # Mostrar linhas de financiamento recomendadas
    st.subheader("💶 Suggested Funding Lines (Final)")
    
    # Sugestões automáticas com base na categoria
    auto_lines = auto_recommend(
        cultura,
        df,
        pepac,
        categoria_override=categoria_new if mode == "Add new crop" else None
    )

    if auto_lines:
        st.markdown("**Suggested based on crop category:**")
        for code, line in auto_lines:
            st.markdown(f"**{code} – {line['name']}**")
            st.write("Objective:", line["objective"])
            st.write("Support:", line.get("support", "N/A"))
            st.markdown("---")

    # Sugestões refinadas com base nos inputs do agricultor
    lines = recommend_lines(age, start, modernize, transform,
                            collective, access, calamity, landscape,
                            insurance, pepac)
    if lines:
        st.markdown("**Refined suggestions (based on your inputs):**")
        for code, line in lines:
            st.markdown(f"**{code if code else 'N/A'} – {line['name']}**")
            st.write("Objective:", line["objective"])
            st.write("Support:", line.get("support", "N/A"))
            with st.expander("Criteria details"):
                for c in line.get("criteria", []):
                    st.markdown(f"- {c}")
            st.markdown("---")

else:
    st.warning("⚠️ No agronomic data available for this crop. Cannot calculate final recommendation.")

