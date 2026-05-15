import streamlit as st
import pandas as pd
import graphviz

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
    .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #117b8f; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
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
    st.image("https://cdn-icons-png.flaticon.com/512/2060/2060284.png", width=60) # Travel Icon
    st.markdown("### ⚙️ Trip Parameters")
    st.markdown("Set your baseline constraints here before chatting.")
    
    st.divider()
    
    # New Specific Inputs requested
    pref_budget = st.slider("💰 Total Budget (₹)", min_value=5000, max_value=500000, value=50000, step=5000)
    pref_days = st.number_input("📅 Number of Days", min_value=1, max_value=14, value=3)
    pref_acc = st.selectbox("🏨 Accommodation Style", ["Budget / Hostel", "Standard Hotel", "Boutique / Airbnb", "Luxury (4-5 Star)"])
    pref_trans = st.selectbox("🚇 Transport Preference", ["Public Transit (Metro/Bus)", "Walking Focused", "Rental Car", "Taxis / Rideshares"])
    
    st.divider()
    
    # A button to inject these settings into the chat
    if st.button("Apply Parameters to Chat", type="primary", use_container_width=True):
        system_injection = f"I want a {pref_days}-day trip. My budget is ₹{pref_budget:,}. I prefer {pref_acc} for stays and {pref_trans} for getting around. Now, let's plan the destination!"
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
                with st.spinner("Analyzing parameters and generating flowchart..."):
                    # We pass the prompt PLUS the sidebar settings so the AI knows the constraints!
                    full_context = f"[Context: Budget ₹{pref_budget}, Days: {pref_days}, Stay: {pref_acc}, Transport: {pref_trans}] User says: {prompt}"
                    
                    ai_chat_text, generated_json = generate_itinerary(full_context)
                    
                    if generated_json is not None:
                        st.session_state.itinerary_data = generated_json
                    
                    st.write(ai_chat_text)
                    st.session_state.messages.append({"role": "assistant", "content": ai_chat_text})
        st.rerun()

# ------------------------------------------
# RIGHT PANEL: DASHBOARD, FLOWCHART & ITINERARY
# ------------------------------------------
with right_panel:
    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD & FLOWCHART", "📋 DETAILED ITINERARY", "🗺️ MAP VIEW"])
    
    # Check if data exists
    has_data = st.session_state.itinerary_data is not None
    data = st.session_state.itinerary_data if has_data else {}
    
    # --- TAB 1: VISUAL DASHBOARD & FLOWCHART ---
    with tab1:
        if not has_data:
            st.info("👈 Set your preferences in the sidebar and send a message to generate your visual dashboard!")
        else:
            st.markdown(f"#### ✈️ {data.get('title', 'Your Custom Trip')}")
            
            # 1. High-Level Metrics (Looks great for judges)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div class='metric-card'><b>Budget:</b><br>₹{pref_budget:,}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-card'><b>Duration:</b><br>{pref_days} Days</div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='metric-card'><b>Transport:</b><br>{pref_trans}</div>", unsafe_allow_html=True)
            
            st.write("---")
            st.markdown("##### 🛤️ Trip Flowchart")
            
            # 2. GENERATE THE FLOWCHART DYNAMICALLY
            # We use Graphviz to read the AI JSON and draw a route
            graph = graphviz.Digraph(node_attr={'shape': 'box', 'style': 'rounded,filled', 'fillcolor': '#e8f1f2', 'color': '#117b8f'})
            graph.attr(rankdir='LR') # Left to Right layout
            
            previous_node = None
            
            # Loop through days to build the flowchart
            for i, day in enumerate(data.get('days', [])):
                day_node = f"Day {i+1}"
                graph.node(day_node, label=day.get('day_label', f"Day {i+1}"), shape='folder', fillcolor='#117b8f', fontcolor='white')
                
                # Connect days together
                if previous_node:
                    graph.edge(previous_node, day_node)
                previous_node = day_node
                
                # Add 1 or 2 main activities below the day to keep the chart clean
                activities = day.get('activities', [])
                if activities:
                    act_node = f"act_{i}"
                    # Just grab the first activity title for the flowchart
                    act_title = activities[0].get('title', 'Activity')
                    graph.node(act_node, label=act_title)
                    graph.edge(day_node, act_node, style='dashed')
            
            # Render the flowchart in Streamlit!
            st.graphviz_chart(graph, use_container_width=True)

    # --- TAB 2: THE ACCORDION ITINERARY ---
    with tab2:
        if not has_data:
            st.write("Awaiting data...")
        else:
            st.markdown(f"#### 📝 Detailed Daily Plan")
            for index, day in enumerate(data.get('days', [])):
                with st.expander(day.get('day_label', f"Day {index + 1}"), expanded=(index == 0)):
                    for activity in day.get('activities', []):
                        st.markdown(f"**{activity.get('time', '')}** - **{activity.get('title', 'Activity')}**")
                        st.caption(f"_{activity.get('desc', '')}_")
                        st.divider()
            
            st.button("📥 EXPORT FULL PDF", use_container_width=True, type="primary")

    # --- TAB 3: MAP VIEW ---
    with tab3:
        if not has_data:
            st.write("Awaiting destination...")
        else:
            st.markdown("#### Destination Map")
            map_data = pd.DataFrame({'lat': [10.8505], 'lon': [76.2711]}) # Example: Kerala coordinates
            st.map(map_data, zoom=6, use_container_width=True)