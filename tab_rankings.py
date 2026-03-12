import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# Import our math, data, and theme buckets!
from utils_math import time_to_seconds, seconds_to_time, calculate_season
from utils_data import load_and_clean_data
from config_theme import THEMES

# Grab the cached database
roster_data, races_data, workouts_data, vdot_data, rest_data, docs_data = load_and_clean_data()
CURRENT_SEASON = calculate_season(datetime.date.today())

# ==========================================
# --- RANKINGS & PROGRESS PLOTS ---
# ==========================================

def plot_athlete_progress(user_races):
    """Generates a Plotly line chart tracking an athlete's 5K times over the season."""
    df = user_races[(user_races["Distance"].str.upper() == "5K") & (user_races["Time_Sec"] > 0)].copy()
    if df.empty or len(df) < 2: return 
    
    df["Date_Obj"] = pd.to_datetime(df["Date"], errors='coerce')
    df = df.sort_values("Date_Obj")
    df["Time_Min"] = df["Time_Sec"] / 60.0  
    
    # Use the user's currently selected theme to color the chart!
    current_theme = THEMES[st.session_state["theme"]]
    
    fig = px.line(df, x="Date_Obj", y="Time_Min", markers=True, text="Meet_Name", title="Current Season 5K Progression", hover_data={"Date_Obj": "|%b %d, %Y", "Time_Min": False, "Total_Time": True, "Meet_Name": False})
    fig.update_traces(textposition="top center", line_color=current_theme["line"], line_width=3, marker_size=8)
    fig.update_yaxes(title="Finish Time (Minutes)")
    fig.update_xaxes(title="Race Date")
    fig.update_layout(template=current_theme["plotly_template"], margin=dict(t=50, b=20, l=20, r=20))
    
    st.plotly_chart(fig, use_container_width=True, theme=None)
    st.markdown("---")

def show_rankings_tab():
    """Calculates and displays the team Leaderboard and Master Data Grid."""
    st.subheader("Team Rankings & Season Grid")
    r_col1, r_col2, r_col3 = st.columns(3)
    
    available_seasons = sorted(races_data["Season"].unique().tolist(), reverse=True)
    if not available_seasons: available_seasons = [CURRENT_SEASON]
    
    with r_col1: r_season = st.selectbox("Season", available_seasons, key="rankings_season")
    with r_col2: r_gender = st.selectbox("Category", ["Men's", "Women's"], key="rankings_category")
    with r_col3: r_dist = st.selectbox("Distance", ["5K", "2 Mile"], key="rankings_distance")
        
    target_gender = "Male" if r_gender == "Men's" else "Female"
    
    # Merge race data with the roster to get names and verify they are active runners
    merged = pd.merge(races_data, roster_data[["Username", "First_Name", "Last_Name", "Gender", "Active_Clean"]], on="Username", how="inner")
    merged = merged[merged["Active_Clean"].isin(["TRUE", "1", "1.0"]) & merged["Active"].isin(["TRUE", "1", "1.0"])]
    merged = merged[(merged["Gender"].str.title() == target_gender) & (merged["Distance"].str.upper() == r_dist.upper()) & (merged["Season"] == r_season)]
    
    if merged.empty: 
        return st.info("No active race data found for this category and season.")
    
    tab_lead, tab_grid = st.tabs(["Leaderboard", "Master Grid"])
    
    with tab_lead:
        r_metric = st.radio("Rank By:", ["Weighted Average", "Personal Record (PR)"], horizontal=True, key="rankings_metric")
        merged["Time_Sec"] = merged["Total_Time"].apply(time_to_seconds)
        merged["Weight"] = pd.to_numeric(merged["Weight"], errors="coerce").fillna(1.0)
        
        results = []
        for user, group in merged.groupby("Username"):
            valid_races = group[group["Weight"] > 0] 
            if valid_races.empty: continue
            
            if r_metric == "Personal Record (PR)":
                best_time = valid_races["Time_Sec"].min()
                results.append({"Athlete": f"{group.iloc[0]['First_Name']} {group.iloc[0]['Last_Name']}", "Time_Sec": best_time, "Mark": seconds_to_time(best_time)})
            else: 
                # Weighted Average Logic
                total_weight = valid_races["Weight"].sum()
                if total_weight <= 0: continue
                weighted_sum = (valid_races["Time_Sec"] * valid_races["Weight"]).sum()
                avg_time = weighted_sum / total_weight
                results.append({"Athlete": f"{group.iloc[0]['First_Name']} {group.iloc[0]['Last_Name']}", "Time_Sec": avg_time, "Mark": seconds_to_time(avg_time)})
                
        if not results: 
            st.info("No valid ranked data (check if races have a weight of 0).")
        else:
            rank_df = pd.DataFrame(results).sort_values(by="Time_Sec").reset_index(drop=True)
            rank_df.index = rank_df.index + 1
            rank_df = rank_df.rename_axis("Rank").reset_index()
            display_df = rank_df[["Rank", "Athlete", "Mark"]].rename(columns={"Mark": "PR Time" if r_metric == "Personal Record (PR)" else "Weighted Avg Time"})
            
            # Wraps the leaderboard in columns to make it narrower and easier to read
            spacer_left, center_col, spacer_right = st.columns([1, 2, 1])
            with center_col:
                st.dataframe(display_df, hide_index=True, use_container_width=True)

    with tab_grid:
        st.markdown(f"### Master {r_dist} Grid")
        grid_df = merged.copy()
        grid_df["Athlete"] = grid_df["First_Name"] + " " + grid_df["Last_Name"]
        grid_df["Date_Obj"] = pd.to_datetime(grid_df["Date"], errors='coerce')
        grid_df = grid_df.sort_values(by="Date_Obj")
        
        # Appends the weight multiplier directly to the Meet column name for transparency
        grid_df["Weight_Str"] = grid_df["Weight"].apply(lambda x: f"{float(x):.1f}")
        grid_df["Race_Col"] = grid_df["Meet_Name"] + " (" + grid_df["Date_Obj"].dt.strftime('%m/%d').fillna("") + ") [" + grid_df["Weight_Str"] + "x]"
        
        ordered_cols = grid_df["Race_Col"].unique().tolist()
        pivot_df = grid_df.pivot_table(index="Athlete", columns="Race_Col", values="Total_Time", aggfunc="first").reindex(columns=ordered_cols).fillna("-").reset_index()
        
        st.dataframe(pivot_df, hide_index=True, use_container_width=True)
