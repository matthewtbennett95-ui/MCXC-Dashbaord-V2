import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# Import our math and data buckets!
from utils_math import time_to_seconds, seconds_to_time, calculate_season, find_suggested_rest, get_weather_for_date
from utils_data import load_and_clean_data

# Grab the cached database
roster_data, races_data, workouts_data, vdot_data, rest_data, docs_data = load_and_clean_data()
CURRENT_SEASON = calculate_season(datetime.date.today())

# ==========================================
# --- INDIVIDUAL ATHLETE LOGIC ---
# ==========================================

def get_athlete_baseline(target_username):
    """Finds the athlete's current 5K PR to establish their baseline for pacing."""
    user_races = races_data[(races_data["Username"] == target_username) & (races_data["Active"].isin(["TRUE", "1", "1.0"]))].copy()
    if user_races.empty: return None, None
    
    c_5k = user_races[(user_races["Season"] == CURRENT_SEASON) & (user_races["Distance"].str.upper() == "5K") & (user_races["Total_Time"].str.strip() != "")]
    if not c_5k.empty:
        c_5k["sec"] = c_5k["Total_Time"].apply(time_to_seconds)
        return c_5k["sec"].min(), "Current 5K PR"
        
    p_5k = user_races[(user_races["Distance"].str.upper() == "5K") & (user_races["Total_Time"].str.strip() != "")]
    if not p_5k.empty:
        p_5k["sec"] = p_5k["Total_Time"].apply(time_to_seconds)
        return p_5k["sec"].min(), "Career 5K PR"
        
    c_2m = user_races[(user_races["Season"] == CURRENT_SEASON) & (user_races["Distance"].str.upper() == "2 MILE") & (user_races["Total_Time"].str.strip() != "")]
    if not c_2m.empty:
        c_2m["sec"] = c_2m["Total_Time"].apply(time_to_seconds)
        return c_2m["sec"].min(), "Current 2-Mile PR"
        
    p_2m = user_races[(user_races["Distance"].str.upper() == "2 MILE") & (user_races["Total_Time"].str.strip() != "")]
    if not p_2m.empty:
        p_2m["sec"] = p_2m["Total_Time"].apply(time_to_seconds)
        return p_2m["sec"].min(), "Career 2-Mile PR"
        
    return None, None

def display_suggested_paces(target_username):
    """Calculates and displays VDOT training paces and Rest cycles based on baseline."""
    st.markdown(f"### 🎯 Training Paces & Rest Cycles")
    
    baseline_sec, baseline_source = get_athlete_baseline(target_username)
    if not baseline_sec:
        st.warning(f"No race data found for {target_username} to calculate paces. Run a race first!")
        return
        
    vdot_data["5K_Sec"] = vdot_data["5K_Time"].apply(time_to_seconds)
    vdot_data["2M_Sec"] = vdot_data["2_Mile_Time"].apply(time_to_seconds)
    
    match_row = None
    if "5K" in baseline_source:
        diffs = (vdot_data["5K_Sec"] - baseline_sec).abs()
        match_row = vdot_data.loc[diffs.idxmin()]
    else:
        diffs = (vdot_data["2M_Sec"] - baseline_sec).abs()
        match_row = vdot_data.loc[diffs.idxmin()]
        
    st.info(f"**Baseline Used:** {seconds_to_time(baseline_sec)} ({baseline_source}) → **Estimated VDOT:** {match_row['VDOT']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🏃‍♂️ Training Paces")
        p_df = pd.DataFrame({
            "Workout Type": ["Easy / Long Run", "Tempo (Threshold) Mile", "Tempo 400m", "Interval 400m", "Interval 800m", "Interval 1000m", "Interval 1200m", "Interval Mile"],
            "Target Pace": [match_row["Easy_Pace"], match_row["Tempo_Mile"], match_row["Tempo_400m"], match_row["Interval_400m"], match_row["Interval_800m"], match_row["Interval_1000m"], match_row["Interval_1200m"], match_row["Interval_Mile"]]
        })
        st.dataframe(p_df, hide_index=True, use_container_width=True)
        
    with col2:
        st.markdown("#### ⏱️ Suggested Rest Cycles")
        rest_list = [
            {"Workout": "Tempo 400s", "Cycle": find_suggested_rest("Tempo 400s", time_to_seconds(match_row["Tempo_400m"]), rest_data)},
            {"Workout": "800s (I Pace)", "Cycle": find_suggested_rest("800s", baseline_sec if "5K" in baseline_source else None, rest_data)},
            {"Workout": "1000s (I Pace)", "Cycle": find_suggested_rest("1000s", baseline_sec if "5K" in baseline_source else None, rest_data)},
            {"Workout": "1200s (I Pace)", "Cycle": find_suggested_rest("1200s", baseline_sec if "5K" in baseline_source else None, rest_data)},
            {"Workout": "Mile Intervals", "Cycle": find_suggested_rest("Mile Intervals", baseline_sec if "2M" in baseline_source else None, rest_data)},
            {"Workout": "Hill Repeats", "Cycle": find_suggested_rest("Hills", baseline_sec if "5K" in baseline_source else None, rest_data)}
        ]
        st.dataframe(pd.DataFrame(rest_list), hide_index=True, use_container_width=True)

def display_career_history(target_username):
    """Shows an athlete's all-time PRs across all distances."""
    st.markdown("### 🏆 Career Personal Records")
    user_races = races_data[(races_data["Username"] == target_username) & (races_data["Active"].isin(["TRUE", "1", "1.0"]))].copy()
    
    if user_races.empty:
        st.info("No race history found.")
        return
        
    user_races["Time_Sec"] = user_races["Total_Time"].apply(time_to_seconds)
    valid_races = user_races[user_races["Time_Sec"] > 0]
    
    if valid_races.empty:
        st.info("No valid race times found.")
        return
        
    prs = valid_races.loc[valid_races.groupby("Distance")["Time_Sec"].idxmin()]
    prs_display = prs[["Distance", "Total_Time", "Meet_Name", "Date", "Season"]].rename(columns={"Total_Time": "PR Time", "Meet_Name": "Meet Set", "Season": "Year"})
    st.dataframe(prs_display.sort_values("Distance"), hide_index=True, use_container_width=True)

def display_athlete_races(username, season):
    """Displays a detailed grid of all races run by the athlete in a specific season."""
    user_races = races_data[(races_data["Username"] == username) & (races_data["Season"] == season) & (races_data["Active"].isin(["TRUE", "1", "1.0"]))].copy()
    if user_races.empty:
        st.info(f"No race results found for {season}.")
        return
    
    display_df = user_races[["Date", "Meet_Name", "Race_Name", "Distance", "Mile_1", "Mile_2", "Total_Time"]].sort_values("Date", ascending=False)
    display_df = display_df.rename(columns={"Meet_Name": "Meet", "Race_Name": "Race", "Total_Time": "Time"})
    st.dataframe(display_df, hide_index=True, use_container_width=True)

def display_athlete_workouts(target_username, target_season):
    """Displays a detailed grid of all workouts completed by the athlete in a specific season."""
    user_workouts = workouts_data[(workouts_data["Username"] == target_username) & (workouts_data["Season"] == target_season)].copy()
    if user_workouts.empty:
        st.info(f"No workouts logged for {target_season}.")
        return
        
    display_w = user_workouts[["Date", "Workout_Type", "Rep_Distance", "Status", "Splits", "Weather"]].sort_values("Date", ascending=False)
    display_w = display_w.rename(columns={"Workout_Type": "Workout", "Rep_Distance": "Distance"})
    
    def highlight_status(val):
        color = '#2e7d32' if val == 'Present' else '#c62828' if val in ['Absent', 'Unexcused'] else '#f57c00'
        return f'color: {color}; font-weight: bold'
        
    st.dataframe(display_w.style.map(highlight_status, subset=['Status']), hide_index=True, use_container_width=True)
