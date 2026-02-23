import streamlit as st
from google import genai
import folium
from streamlit_folium import st_folium
import requests
import json
import os
from dotenv import load_dotenv

# 1. SETUP & API INITIALIZATION
st.set_page_config(page_title="AI Travel Planner", layout="wide")
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY: 
    st.error("🚨 GEMINI_API_KEY not found in .env!"); st.stop()
if "gemini_client" not in st.session_state: 
    st.session_state.gemini_client = genai.Client(api_key=API_KEY)

# Condense State Initialization
defaults = {"active_tab": "Chatbot", "chat_history": [], "options_data": [], "selected_option": None, "workflow_step": "form", "user_inputs": {}}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

ss = st.session_state 

# 2. HELPER FUNCTIONS
def extract_json(t):
    """Extracts JSON array from text, ignoring markdown."""
    try: return json.loads(t[t.find('['):t.rfind(']')+1]) if '[' in t else json.loads(t)
    except: return None

def get_coords(city):
    try:
        r = requests.get(f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1", headers={'User-Agent': 'TravelApp'}, timeout=5).json()
        return (float(r[0]['lat']), float(r[0]['lon'])) if r else None
    except: return None

def get_route(coords):
    try:
        c_str = ";".join([f"{c[1]},{c[0]}" for c in coords])
        r = requests.get(f"http://router.project-osrm.org/route/v1/driving/{c_str}?overview=full&geometries=geojson", timeout=5).json()
        return r["routes"][0]["geometry"] if r.get("code") == "Ok" else None
    except: return None

def reset_app():
    ss.update({"workflow_step": "form", "options_data": [], "selected_option": None, "chat_history": []})

# 3. SIDEBAR
with st.sidebar:
    st.title("🗺️ Navigation")
    if st.button("💬 Chatbot View", use_container_width=True): ss.active_tab = "Chatbot"; st.rerun()
    if st.button("📍 Map View", use_container_width=True): ss.active_tab = "Map"; st.rerun()
    st.markdown("---")
    if st.button("🔄 Start Over", use_container_width=True, type="secondary"): reset_app(); ss.active_tab = "Chatbot"; st.rerun()

# 4. MAIN PANEL: CHATBOT VIEW
if ss.active_tab == "Chatbot":
    st.title("🎒 Budget-Friendly AI Travel Planner")

    # STEP 1: INPUT FORM
    if ss.workflow_step == "form":
        ptype = st.radio("Plan type?", ["Plan for Budget", "Plan for location chosen"], on_change=reset_app)
        
        with st.form("form"):
            cur_city = st.text_input("Current City")
            dest, occ, pass_opt = "", "", "No"
            budg, ppl, days = 0, 1, 1

            if ptype == "Plan for Budget":
                budg = st.number_input("Total budget", min_value=0)
                ppl = st.number_input("Number of people", min_value=1)
                
                if ppl > 0 and (budg / ppl) > 100000:
                    pass_opt = st.radio("Large budget! Do you have a valid passport?", ["Yes", "No"])
            else:
                dest = st.text_input("Destination")
                days = st.number_input("Visit days", min_value=1)
                ppl = st.number_input("Number of people", min_value=1)
                o_c = st.selectbox("Occasion?", ["Fun travel", "Mental peace", "Temple visit", "Heritage/Historical", "Others"])
                occ = st.text_input("Specify occasion:") if o_c == "Others" else o_c

            if st.form_submit_button("Find Options"):
                if not cur_city: st.warning("Enter current city."); st.stop()
                if ptype == "Plan for Budget" and budg < 500: st.error("Budget too low (500+)."); st.stop()
                
                ss.user_inputs = {"ptype": ptype, "city": cur_city, "dest": dest, "budg": budg, "ppl": ppl, "days": days, "occ": occ, "pass": pass_opt}
                start_c = get_coords(cur_city)
                if not start_c: st.error("City not found."); st.stop()

                with st.spinner("Analyzing routes..."):
                    if ptype == "Plan for Budget":
                        scope = "international or domestic cities" if pass_opt == "Yes" else "strictly domestic Indian cities"
                        prompt = f"Person(s) in {cur_city}, budget {budg} for {ppl} ppl. Suggest 3 affordable {scope}. Return JSON array of 3 strings: [\"A\",\"B\",\"C\"]"
                        res = extract_json(ss.gemini_client.models.generate_content(model='gemini-2.5-flash', contents=prompt).text)
                        if not res: st.error("AI parse failed. Try again."); st.stop()
                        
                        opts = [{"id": f"O_{i}", "type": "budget", "label": f"Route to {d}", "dest": d, "coords": [start_c, dc], "geo": get_route([start_c, dc]), "desc": f"Budget trip to {d}"} for i, d in enumerate(res) if (dc := get_coords(d))]
                    
                    else:
                        prompt = f"Driving {cur_city} to {dest}. Suggest 3 routes with unique major tourist stopovers. Return JSON array: [{{\"route_name\":\"N\",\"stopover_city\":\"S\",\"description\":\"D\"}}]"
                        res = extract_json(ss.gemini_client.models.generate_content(model='gemini-2.5-flash', contents=prompt).text)
                        if not res: st.error("AI parse failed. Try again."); st.stop()
                        dest_c = get_coords(dest)
                        
                        opts = [{"id": f"R_{i}", "type": "loc", "label": f"{r.get('route_name')} (via {r.get('stopover_city')})", "stop": r.get("stopover_city"), "desc": r.get("description"), "coords": [start_c, sc, dest_c], "geo": get_route([start_c, sc, dest_c])} for i, r in enumerate(res) if (sc := get_coords(r.get("stopover_city"))) and dest_c]

                    if opts: ss.options_data, ss.workflow_step = opts, "options_generated"; st.rerun()

    # STEP 2: SHOW EXPLANATIONS
    elif ss.workflow_step == "options_generated":
        st.subheader("📍 3 Route Options Found!")
        for o in ss.options_data:
            st.markdown(f"**{o['label']}**\n\n*{'Stopover' if o['type']=='loc' else 'Destination'}:* {o.get('stop', o.get('dest'))}\n\n*Why:* {o['desc']}")
        if st.button("🗺️ View on Map & Select Route", type="primary"): ss.active_tab = "Map"; st.rerun()

    # STEP 3: FINAL PLAN
    elif ss.workflow_step == "final_plan":
        ui, sel = ss.user_inputs, ss.selected_option
        if not ss.chat_history:
            st.success(f"Selected: **{sel['label']}**")
            with st.spinner("Generating travel plan..."):
                p = f"trip {ui['city']} to {sel.get('dest')} for {ui['ppl']} ppl, budget {ui['budg']}." if sel["type"] == "budget" else f"trip {ui['city']} to {ui['dest']} via {sel['stop']} for {ui['days']} days. Occasion: {ui['occ']}."
                p += " Provide budget estimate, day-by-day plan, and booking links (MakeMyTrip, Agoda, Redbus)."
                ss.chat_history = [{"role": "model", "text": ss.gemini_client.models.generate_content(model='gemini-2.5-flash', contents=p).text}]
                st.rerun()

        for m in ss.chat_history: 
            if m["role"] == "model":
                st.info(m["text"])
            else:
                st.success(f"You: {m['text']}")
        
        if usr := st.chat_input("Suggest changes..."):
            ss.chat_history.append({"role": "user", "text": usr})
            hist = "\n".join([f"{m['role']}: {m['text']}" for m in ss.chat_history])
            with st.spinner("Updating..."):
                ss.chat_history.append({"role": "model", "text": ss.gemini_client.models.generate_content(model='gemini-2.5-flash', contents=f"History:\n{hist}\n\nUpdate based on: '{usr}'. Keep budget constraints.").text})
                st.rerun()

# 5. MAIN PANEL: MAP VIEW
elif ss.active_tab == "Map":
    st.title("🗺️ Travel Map")
    if not ss.options_data: 
        st.info("No routes yet!"); st_folium(folium.Map([20.59, 78.96], zoom_start=4), width=900, height=600)
    else:
        st.success("👇 **CLICK ON A HIGHLIGHTED MARKER TO SELECT YOUR ROUTE!**")
        m = folium.Map(location=ss.options_data[0]["coords"][0], zoom_start=5)
        cols = ["blue", "green", "purple"]
        
        for i, o in enumerate(ss.options_data):
            folium.Marker(o["coords"][0], icon=folium.Icon(color="black", icon="play")).add_to(m)
            c_icon = folium.Icon(color="red", icon="star") if o["type"] == "budget" else folium.Icon(color="orange", icon="info-sign")
            folium.Marker(o["coords"][1], tooltip=o["label"], icon=c_icon).add_to(m) 
            if o["type"] == "loc": folium.Marker(o["coords"][2], icon=folium.Icon(color="red", icon="stop")).add_to(m)
            if o["geo"]: folium.PolyLine([(c[1], c[0]) for c in o["geo"]['coordinates']], color=cols[i%3], weight=5, opacity=0.7).add_to(m)
        
        # Capture the click
        map_d = st_folium(m, width=900, height=600, returned_objects=["last_object_clicked_tooltip"])
        
        if map_d and map_d.get("last_object_clicked_tooltip"):
            if sel := next((opt for opt in ss.options_data if opt["label"] == map_d["last_object_clicked_tooltip"]), None):
                ss.selected_option, ss.workflow_step, ss.active_tab = sel, "final_plan", "Chatbot"
                st.rerun()