import streamlit as st
import pandas as pd
import datetime

# ==========================================
# --- 1. PAGE CONFIG MUST BE FIRST ---
# ==========================================
st.set_page_config(
    page_title="MCXC Team Dashboard", 
    layout="wide",
    page_icon="mcxc_logo.png"  
)

# ==========================================
# --- 2. IMPORT OUR MODULAR BUCKETS ---
# ==========================================
from config_theme import THEMES, force_mobile_icon, apply_theme
from utils_data import load_and_clean_data
from utils_math import time_to_seconds, seconds_to_time, calculate_season
from tab_coach import show_coach_dashboard
from tab_profile import display_athlete_races, display_athlete_workouts, display_suggested_paces, display_career_history
from tab_rankings import show_rankings_tab

# ==========================================
# --- 3. INITIALIZE APP & DATA ---
# ==========================================
force_mobile_icon()

if "theme" not in st.session_state:
    st.session_state["theme"] = "MCXC Classic (Light)"

# Inject the visual theme
apply_theme(st.session_state["theme"])

# Load the lightning-fast cached data!
roster_data, races_data, workouts_data, vdot_data, rest_data, docs_data = load_and_clean_data()
CURRENT_SEASON = calculate_season(datetime.date.today())

# ==========================================
# --- 4. SESSION STATE MANAGEMENT ---
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    for key in ["username", "first_name", "last_name", "role"]:
        st.session_state[key] = ""

def logout():
    """Clears session state to securely log the user out."""
    st.session_state["logged_in"] = False
    for key in ["username", "first_name", "last_name", "role"]:
        st.session_state[key] = ""
    st.rerun()

# ==========================================
# --- 5. LOGIN PAGE ---
# ==========================================
def login_page():
    spacer1, center_col, spacer2 = st.columns([1, 2, 1])
    with center_col:
        st.markdown("<h1 style='text-align: center;'>🏃‍♂️ MCXC Team Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("---")
        
        with st.form("login_form"):
            username_input = st.text_input("Username", placeholder="e.g. jsmith25")
            password_input = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Log In", use_container_width=True)
            
            if submit_button:
                # Check active roster only
                active_roster = roster_data[roster_data["Active_Clean"].isin(["TRUE", "1", "1.0"])]
                user_match = active_roster[(active_roster["Username"] == username_input) & (active_roster["Password"] == password_input)]
                
                if not user_match.empty:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user_match.iloc[0]["Username"]
                    st.session_state["first_name"] = user_match.iloc[0]["First_Name"]
                    st.session_state["last_name"] = user_match.iloc[0]["Last_Name"]
                    st.session_state["role"] = user_match.iloc[0]["Role"]
                    st.rerun()
                else:
                    st.error("Invalid Username or Password. Are you on the active roster?")

# ==========================================
# --- 6. MAIN APP ROUTING (TRAFFIC COP) ---
# ==========================================
if not st.session_state["logged_in"]:
    login_page()
else:
    # --- Top Navigation Bar ---
    col1, col2, col3 = st.columns([6, 2, 1])
    with col1:
        st.markdown(f"## Welcome, {st.session_state['first_name']} {st.session_state['last_name']}! ({st.session_state['role']})")
    with col2:
        theme_names = list(THEMES.keys())
        current_index = theme_names.index(st.session_state["theme"])
        selected_theme = st.selectbox("Theme:", theme_names, index=current_index, label_visibility="collapsed")
        if selected_theme != st.session_state["theme"]:
            st.session_state["theme"] = selected_theme
            st.rerun()
    with col3:
        st.button("Log Out", on_click=logout, use_container_width=True)

    st.markdown("---")

    # --- Route to Coach Dashboard ---
    if st.session_state["role"] == "Coach":
        show_coach_dashboard()

    # --- Route to Athlete Dashboard ---
    elif st.session_state["role"] == "Athlete":
        tab_me, tab_rankings, tab_resources = st.tabs(["My Season", "Team Rankings", "Team Resources"])
        
        with tab_me:
            st.subheader("My Season")
            
            # Fetch user-specific data
            user_races = races_data[(races_data["Username"] == st.session_state["username"]) & (races_data["Active"].isin(["TRUE", "1", "1.0"]))]
            user_workouts = workouts_data[workouts_data["Username"] == st.session_state["username"]]
            
            all_seasons = sorted(list(set(user_races["Season"].tolist() + user_workouts["Season"].tolist())), reverse=True)
            if not all_seasons: all_seasons = [CURRENT_SEASON]
            sel_season = st.selectbox("Select Season to View:", all_seasons, key="ath_season")
            
            # Athlete Top Metrics
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric(label=f"Races Run ({sel_season})", value=len(user_races[user_races["Season"] == sel_season]))
            col_m2.metric(label=f"Workouts Logged ({sel_season})", value=len(user_workouts[(user_workouts["Season"] == sel_season) & (user_workouts["Status"] == "Present")]))
            
            fastest_5k = "N/A"
            if not user_races.empty:
                five_k_races = user_races[user_races["Distance"].str.upper() == "5K"]
                if not five_k_races.empty:
                    fastest_sec = five_k_races["Total_Time"].apply(time_to_seconds).replace(0, float('inf')).min()
                    if fastest_sec != float('inf'): fastest_5k = seconds_to_time(fastest_sec)
                    
            col_m3.metric(label=f"Career 5K PR", value=fastest_5k)
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Load the sub-tabs we built in tab_profile!
            sub_races, sub_workouts, sub_paces, sub_career = st.tabs(["Race Results", "Workouts", "Training Paces", "Career PRs"])
            with sub_races: display_athlete_races(st.session_state["username"], sel_season)
            with sub_workouts: display_athlete_workouts(st.session_state["username"], sel_season)
            with sub_paces: display_suggested_paces(st.session_state["username"])
            with sub_career: display_career_history(st.session_state["username"])
            
        with tab_rankings:
            show_rankings_tab()
            
        with tab_resources:
            st.subheader("Team Resources & Links")
            if not docs_data.empty:
                for _, row in docs_data.iterrows():
                    if row["URL"]: st.markdown(f"- [{row['Title']}]({row['URL']})")
                    else: st.markdown(f"- {row['Title']} (No Link Provided)")
