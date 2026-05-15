import streamlit as st
import pandas as pd

# Import your LangChain function (ensure ai_service.py is in the same folder)
from ai_service import generate_itinerary 

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# ==========================================
st.set_page_config(page_title="AI Travel Assistant", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .top-header { background-color: #117b8f; color: white; padding: 15px 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; font-family: sans-serif; }
    .top-header h3 { margin: 0; font-size: 1.2rem; font-weight: 600; color: white; }
    .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #117b8f; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;}
    </style>
    <div class="top-header">
        <h3>☰ AI Travel Assistant - Team 10 [JDC]</h3>
        <span>Welcome, Admin@2025 👤</span>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 2. INITIALIZE GLOBAL STATE
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome! Please set your trip preferences in the sidebar, then tell me where you want to go!"}]
if "itinerary_data" not in st.session_state:
    st.session_state.itinerary_data = None 

# ==========================================
# 3. THE SIDEBAR (Structured Preferences)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2060/2060284.png", width=60)
    st.markdown("### ⚙️ Trip Parameters")
    
    st.divider()
    
    # Updated Inputs (Added Number of People)
    pref_budget = st.slider("💰 Total Budget (₹)", min_value=5000, max_value=500000, value=50000, step=5000)
    pref_days = st.number_input("📅 Number of Days", min_value=1, max_value=14, value=3)
    pref_people = st.number_input("👥 Number of People", min_value=1, max_value=20, value=2)
    pref_acc = st.selectbox("🏨 Accommodation Style", ["Budget / Hostel", "Standard Hotel", "Boutique / Airbnb", "Luxury (4-5 Star)"])
    pref_trans = st.selectbox("🚇 Transport Preference", ["Public Transit (Metro/Bus)", "Walking Focused", "Rental Car", "Taxis / Rideshares"])
    
    st.divider()
    
    if st.button("Apply Parameters to Chat", type="primary", use_container_width=True):
        system_injection = f"I am planning a {pref_days}-day trip for {pref_people} people. My total budget is ₹{pref_budget:,}. I prefer {pref_acc} for stays and {pref_trans} for transport."
        st.session_state.messages.append({"role": "user", "content": system_injection})
        st.rerun()

# ==========================================
# 4. MAIN UI: CHAT & DASHBOARD
# ==========================================
left_panel, right_panel = st.columns([1, 1.4], gap="large")

# ------------------------------------------
# LEFT PANEL: THE AI CHAT
# ------------------------------------------
with left_panel:
    st.markdown("##### 💬 AI Chat Interface")
    chat_container = st.container(height=550, border=True)
    
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
    if prompt := st.chat_input("E.g., Plan a trip to Kerala focusing on nature..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.write(prompt)
                
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing parameters and building itinerary..."):
                    # Updated prompt injection with 'People'
                    full_context = f"[Context: Budget ₹{pref_budget}, Days: {pref_days}, People: {pref_people}, Stay: {pref_acc}, Transport: {pref_trans}] User says: {prompt}"
                    
                    ai_chat_text, generated_json = generate_itinerary(full_context)
                    
                    if generated_json is not None:
                        st.session_state.itinerary_data = generated_json
                    
                    st.write(ai_chat_text)
                    st.session_state.messages.append({"role": "assistant", "content": ai_chat_text})
        st.rerun()

# ------------------------------------------
# RIGHT PANEL: DASHBOARD & ITINERARY
# ------------------------------------------
with right_panel:
    # Simplified to just two tabs
    tab_itinerary, tab_map = st.tabs(["📋 OVERVIEW & ITINERARY", "🗺️ MAP VIEW"])
    
    has_data = st.session_state.itinerary_data is not None
    data = st.session_state.itinerary_data if has_data else {}
    
    # --- TAB 1: OVERVIEW & TABS FOR DAYS ---
    with tab_itinerary:
        if not has_data:
            st.info("👈 Set your preferences in the sidebar and send a message to generate your trip!")
        else:
            st.markdown(f"#### ✈️ {data.get('title', 'Your Custom Trip')}")
            
            # High-Level Metrics (Now with 4 columns to include People)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"<div class='metric-card'><b>Budget</b><br>₹{pref_budget:,}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-card'><b>Days</b><br>{pref_days}</div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='metric-card'><b>Travelers</b><br>{pref_people}</div>", unsafe_allow_html=True)
            with col4:
                st.markdown(f"<div class='metric-card'><b>Transport</b><br>{pref_trans.split(' ')[0]}</div>", unsafe_allow_html=True) # Shortened name
            
            st.write("---")
            
            # DYNAMIC DAY TABS (This solves the "only one open at a time" request)
            days_data = data.get('days', [])
            if days_data:
                # Create the labels for the tabs
                day_labels = [day.get('day_label', f"Day {i+1}") for i, day in enumerate(days_data)]
                
                # Generate the Streamlit tabs dynamically
                day_tabs = st.tabs(day_labels)
                
                # Fill each tab with its specific activities
                for i, day in enumerate(days_data):
                    with day_tabs[i]:
                        st.markdown(f"##### {day.get('day_label', f'Day {i+1}')}")
                        for activity in day.get('activities', []):
                            st.markdown(f"**{activity.get('time', '')}** - **{activity.get('title', 'Activity')}**")
                            st.caption(f"_{activity.get('desc', '')}_")
                            st.divider()
            
            st.button("📥 EXPORT FULL PDF", use_container_width=True, type="primary")

    # --- TAB 2: MAP VIEW ---
    with tab_map:
        if not has_data:
            st.write("Awaiting destination...")
        else:
            st.markdown("#### Destination Map")
            # Static placeholder for the prototype map
            map_data = pd.DataFrame({'lat': [10.8505], 'lon': [76.2711]})
            st.map(map_data, zoom=6, use_container_width=True)