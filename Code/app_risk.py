import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Madeira Crop & Funding Advisor", layout="wide")

# ===== Carregar dados =====
@st.cache_data
def load_data():
    df = pd.read_excel("Worked_datasets/dataset_tableau.xlsx")
    return df

df = load_data()

with open("Code/pepac.json", "r", encoding="utf-8") as f:
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

categoria_new = None 

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
    necessidade_hidrica = st.selectbox(
        "Water needs",
        [(1,"Low"), (2, "Normal"), (3,"High"), "Unknown"],
        format_func=lambda x: x[1]
    )
    solo = st.selectbox(
        "Soil type",
        [(1,"Sandy"), (2, "Loamy"), (3,"Clay"), "Unknown"]
    )
    score_agro = estimate_score(ph_min, ph_max, sol_min, df) if cultura else None


area = st.number_input("Area (ha)", min_value=0.1, max_value=100.0, step=0.1)
if area < 0.25:
    st.error("❌ Minimum area required: 0.25 ha")
    st.stop()


# ==========================
# Passo 1: Agronomic viability
# ==========================
st.header("1️⃣ Agronomic viability")

result_agro = None  # <-- variável para guardar o resultado

if score_agro is not None:
    st.metric("Agronomic Score", f"{score_agro:.2f}")
    if score_agro >= 0.75:
        result_agro = "✅ Good match with Madeira conditions"
        st.success(result_agro)
    elif score_agro >= 0.5:
        result_agro = "⚠️ Partial match (risks exist)"
        st.warning(result_agro)
    else:
        result_agro = "❌ Poor match (not recommended)"
        st.error(result_agro)
else:
    if mode == "Add new crop" and cultura:
        result_agro = "❌ Agronomically not viable in Madeira conditions"
        st.error(result_agro)

# ==========================
# Passo 2: Economic viability
# ==========================
st.header("2️⃣ Economic viability")

result_econ = None  # <-- variável para guardar o resultado
custo_default = 5000  # fallback

# --- Cultura existente ---
if mode == "Select existing crop":
    dados_cultura = df[df["Cultura"] == cultura]

    if not dados_cultura.empty:
        preco_medio = dados_cultura["Preco"].mean()
        prod_media = dados_cultura["Producao"].mean()
        categoria = dados_cultura["categoria"].iloc[0]

        # Custos médios por categoria
        custo_medio_categoria = {
            "Vegetais e Produtos Hortícolas": 3400,
            "Frutos": 10500
        }
        custo_default = custo_medio_categoria.get(categoria, 5000)

    else:
        preco_medio, prod_media, categoria = 0, 0, None

# --- Cultura nova ---
else:  # Add new crop
    df_cat = df[df["categoria"] == categoria_new]

    if df_cat.empty:
        preco_medio, prod_media = 0, 0
        st.error(f"No reference data available for category: {categoria_new}")
    else:
        preco_medio = df_cat["Preco"].mean()
        prod_media = df_cat["Producao"].mean()

    custo_medio_categoria = {
        "Vegetais e Produtos Hortícolas": 3400,
        "Frutos": 10500
    }
    custo_default = custo_medio_categoria.get(categoria_new, 5000)

# --- Input único de custos ---
custos = st.number_input(
    "Operational costs per hectare (€)",
    min_value=100.0, max_value=50000.0, step=100.0,
    value=float(custo_default)
)

# --- Cálculos económicos ---
if preco_medio > 0 and prod_media > 0 and score_agro is not None:
    receita_bruta = preco_medio * prod_media * area / 100
    receita_ajustada = receita_bruta * score_agro
    custo_total = custos * area
    lucro = receita_ajustada - custo_total

    if mode == "Select existing crop":
        st.subheader(f"📊 Results for {cultura}")
    else:
        st.subheader(f"📊 Results for {cultura} (new crop)")

    st.metric("Agronomic Score", f"{score_agro:.2f}")
    st.metric("Average Price", f"{preco_medio:.2f} €/100kg")
    st.metric("Average Production", f"{prod_media:.0f} kg/ha")
    st.metric("Adjusted Revenue (with climate risk)", f"{receita_ajustada:,.0f} €")
    st.metric("Estimated Profit", f"{lucro:,.0f} €")
    st.caption(f"*Default cost: {custo_default} €/ha*")

    # Avaliação de viabilidade
    if score_agro >= 0.75 and lucro > 0:
        result_econ = "✅ High viability: recommended"
        st.success(result_econ)
    elif score_agro >= 0.5 and lucro > 0:
        result_econ = "⚠️ Medium viability: possible risk (climate/economic)"
        st.warning(result_econ)
    else:
        result_econ = "❌ Low viability: high risk (climate or economic loss)"
        st.error(result_econ)

else:
    result_econ = "❌ No economic data available to assess viability"
    st.error(result_econ)


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
    st.write(f"- Agronomic result: {result_agro}")
    st.write(f"- Economic result: {result_econ}")

    # ✅ Frase única de síntese
    if "✅" in result_agro and "✅" in result_econ:
        final_sentence = f"🌟 The crop **{cultura}** is both agronomically and economically viable in Madeira."
    elif "✅" in result_agro and "❌" in result_econ:
        final_sentence = f"⚠️ The crop **{cultura}** is agronomically viable, but **not economically viable** under current conditions."
    elif "❌" in result_agro and "✅" in result_econ:
        final_sentence = f"⚠️ The crop **{cultura}** is economically viable, but **not suitable agronomically** for Madeira."
    elif "⚠️" in result_agro or "⚠️" in result_econ:
        final_sentence = f"⚠️ The crop **{cultura}** has medium viability: risks exist either in climate or economics."
    else:
        final_sentence = f"❌ The crop **{cultura}** is not viable for Madeira."

    st.subheader("📝 Summary")
    st.info(final_sentence)
else:
    st.warning("⚠️ No agronomic data available for this crop. Cannot calculate final recommendation.")


st.subheader("💶 Funding Summary")
    
if auto_lines:
    st.markdown("**Based on crop category:**")
    for code, line in auto_lines:
        st.markdown(f"- {code} – {line['name']}")

if 'lines' in locals() and lines:  # se refinou manualmente
    st.markdown("**Based on farmer profile:**")
    for code, line in lines:
        st.markdown(f"- {code if code else 'N/A'} – {line['name']}")