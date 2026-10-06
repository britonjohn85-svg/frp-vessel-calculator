import streamlit as st

st.set_page_config(
    page_title="Chlorine Dosing Calculator",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Chlorine Dosing Calculator")
st.markdown("For Calcium Hypochlorite Solutions")
st.markdown("---")
st.sidebar.title("Navigation")
option = st.sidebar.radio(
    "Choose a calculation:",
    [
        "1. Prepare Stock Solution",
        "2. Dilute Stock",
        "3. Dose a Batch Tank",
        "4. Continuous Inline Dosing",
        "5. Stock Consumption"
    ]
)
if option == "1. Prepare Stock Solution":
    st.header("🧪 Prepare Stock Solution")
    st.write("Calculate how much calcium hypochlorite to weigh.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        c_stock_percent = st.number_input(
            "Stock Concentration (%)",
            min_value=0.1,
            max_value=15.0,
            value=3.5,
            step=0.1
        )
    
    with col2:
        v_water = st.number_input(
            "Volume of Water (L)",
            min_value=1.0,
            max_value=1000.0,
            value=5.0,
            step=0.5
        )
    
    with col3:
        purity = st.number_input(
            "Purity of Pellets (%)",
            min_value=1.0,
            max_value=100.0,
            value=70.0,
            step=1.0
        )
    
    c_stock_ppm = c_stock_percent * 10000
    mass_g = (c_stock_ppm * v_water) / (purity * 10000)
    mass_kg = mass_g / 1000
    
    st.markdown("---")
    st.subheader("📊 Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Stock Concentration", f"{c_stock_ppm:,.0f} ppm")
    
    with col2:
        st.metric("Mass of Pellets", f"{mass_g:.1f} g")
    
    with col3:
        st.metric("Mass of Pellets", f"{mass_kg:.3f} kg")
    
    st.success(f"✅ Weigh {mass_g:.1f} g of {purity}% calcium hypochlorite and dissolve in {v_water} L of water.")
    elif option == "2. Dilute Stock":
    st.header("💧 Dilute Stock to Working Solution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        c1_percent = st.number_input(
            "Stock Concentration (%)",
            min_value=0.1,
            max_value=15.0,
            value=3.5,
            step=0.1
        )
        
        c2_percent = st.number_input(
            "Working Concentration (%)",
            min_value=0.01,
            max_value=5.0,
            value=0.5,
            step=0.01
        )
    
    with col2:
        v2 = st.number_input(
            "Final Volume (L)",
            min_value=0.1,
            max_value=1000.0,
            value=7.0,
            step=0.5
        )
    
    c1_ppm = c1_percent * 10000
    c2_ppm = c2_percent * 10000
    v1 = (c2_ppm * v2) / c1_ppm
    v_water_add = v2 - v1
    
    st.markdown("---")
    st.subheader("📊 Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Stock to Use", f"{v1:.3f} L")
    
    with col2:
        st.metric("Water to Add", f"{v_water_add:.3f} L")
    
    with col3:
        st.metric("Final Volume", f"{v2:.1f} L")
    
    st.success(f"✅ Mix {v1:.3f} L of stock with {v_water_add:.3f} L of water.")
    