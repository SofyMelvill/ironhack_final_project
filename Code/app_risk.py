import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Madeira Crop & Funding Advisor", layout="wide")

# --- Load datasets ---
@st.cache_data
def load_data():
    df = pd.read_excel(
        r"C:\Users\sofia\Documents\Data_Analytics_Ironhack\Projects\ironhack_final_project\Worked_datasets\dataset_tableau.xlsx"
    )
    return df

df_crops = load_data()
with open("pepac.json", "r", encoding="utf-8") as f:
    pepac = json.load(f)

# --- Funding function ---
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

# --- UI ---
#st.set_page_config(page_title="Madeira Crop & Funding Advisor", layout="wide")
st.title("🌱 Crop Genie")

tab1, tab2, tab3 = st.tabs(["🌾 Crop Advisor", "💶 Funding Advisor", "📊 Profitability Simulator"])

# -------------------
# Tab 1: Crop Advisor
# -------------------
with tab1:
    st.header("🌾 Crop advisor")

    mode = st.radio("Choose input type:", ["Select existing crop", "Add custom crop"])

    if mode == "Select existing crop":
        crop_choice = st.selectbox("Select a crop:", df_crops["Cultura"].unique())
        crop_row = df_crops[df_crops["Cultura"] == crop_choice].iloc[0]

        st.subheader(f"Details for {crop_choice}")
        st.write("Category:", crop_row["categoria"])
        st.write("Price (€/100kg):", crop_row["Preco"])
        st.write("Agronomic score:", crop_row["score_agro"])
        st.write("Preferred soil category:", crop_row["solo_pref_cat"])
        st.write("pH range:", crop_row["ph_min"], "-", crop_row["ph_max"])

        if 6.0 <= crop_row["ph_min"] <= 7.5:
            st.success("✅ Crop seems compatible with Madeira soils")
        else:
            st.warning("⚠️ Crop may face challenges in Madeira soils")

    else:
        crop_name = st.text_input("Enter crop name")
        soil_pref = st.selectbox("Soil preference category", [1, 2, 3, "Unknown"])
        ph_min = st.number_input("Min pH", min_value=3.0, max_value=9.0, value=6.0)
        ph_max = st.number_input("Max pH", min_value=3.0, max_value=9.0, value=7.0)
        water_need = st.selectbox("Water need", ["Low", "Medium", "High", "Unknown"])

        if crop_name:
            st.subheader(f"Custom crop: {crop_name}")
            st.write("Soil preference:", soil_pref)
            st.write("pH range:", ph_min, "-", ph_max)
            st.write("Water need:", water_need)

            if 6.0 <= ph_min and ph_max <= 7.5:
                st.success("✅ Likely compatible with Madeira soils")
            else:
                st.warning("⚠️ Outside the ideal soil pH range for Madeira")

# -------------------
# Tab 2: Funding Advisor
# -------------------
with tab2:
    st.header("💶 Funding advisor")

    age = st.number_input("Farmer age", 18, 100, 30)
    start = st.checkbox("Starting new farm?")
    modernize = st.checkbox("Modernize existing farm?")
    transform = st.checkbox("Processing/marketing products?")
    collective = st.checkbox("Collective irrigation project?")
    access = st.checkbox("Need agricultural access?")
    calamity = st.checkbox("Affected by natural disaster?")
    landscape = st.checkbox("Non-productive investment?")
    insurance = st.checkbox("Has/Plans insurance?")

    if st.button("🔍 Recommend funding lines"):
        lines = recommend_lines(age, start, modernize, transform,
                                collective, access, calamity, landscape,
                                insurance, pepac)
        st.subheader("Recommended funding lines")
        for code, line in lines:
            st.markdown(f"**{code if code else 'N/A'} – {line['name']}**")
            st.write("Objective:", line["objective"])
            st.write("Support:", line.get("support", "N/A"))
            with st.expander("Criteria details"):
                for c in line.get("criteria", []):
                    st.markdown(f"- {c}")
            st.markdown("---")

# -------------------
# Tab 3: Profitability Simulator
# -------------------
with tab3:
    st.header("📊 Profitability Simulator with Climate Risk")

    cultura = st.selectbox("Choose the crop:", sorted(df_crops["Cultura"].unique()))
    area = st.number_input("Area to be planted (hectares)", min_value=0.1, max_value=100.0, step=0.1)
    custos = st.number_input("Operational costs per hectare (€)", min_value=100.0, max_value=50000.0, step=100.0)

    dados_cultura = df_crops[df_crops["Cultura"] == cultura]

    if not dados_cultura.empty:
        preco_medio = dados_cultura["Preco"].mean()
        prod_media = dados_cultura["Producao"].mean()
        score_agro = dados_cultura["score_agro"].mean()

        receita_bruta = preco_medio * prod_media * area / 100
        receita_ajustada = receita_bruta * score_agro
        custo_total = custos * area
        lucro = receita_ajustada - custo_total

        st.subheader(f"Results for {cultura}")
        st.metric("Agronomic Score", f"{score_agro:.2f}")
        st.metric("Average Price", f"{preco_medio:.2f} €/100kg")
        st.metric("Average Production", f"{prod_media:.0f} kg/ha")
        st.metric("Adjusted Revenue (with climate risk)", f"{receita_ajustada:,.0f} €")
        st.metric("Estimated Profit", f"{lucro:,.0f} €")

        if score_agro >= 0.75 and lucro > 0:
            st.success("✅ High viability: recommended")
        elif score_agro >= 0.5 and lucro > 0:
            st.warning("⚠️ Low viability: high risk (climate or economic loss)")
        else:
            st.error("❌ Low viability: high risk (climate or economic loss)")
    else:
        st.error("Not enough data for this crop")
