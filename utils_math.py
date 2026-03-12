import pandas as pd
import datetime
import requests
import re
import numpy as np
import streamlit as st

# ==========================================
# --- TIME MATH & CONVERSIONS ---
# ==========================================

def time_to_seconds(time_str):
    """Converts a standard running time string (e.g., '15:40') into mathematical seconds."""
    if pd.isna(time_str) or time_str == "" or str(time_str).strip() == "": return 0
    time_str = str(time_str).strip()
    if ":" in time_str:
        parts = time_str.split(':')
        return int(parts[0]) * 60 + float(parts[1])
    return 0

def seconds_to_time(seconds):
    """Converts mathematical seconds back into a standard running time string."""
    if seconds <= 0 or pd.isna(seconds): return ""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins}:{secs:05.2f}".replace(".00", "")

def parse_fast_time(val, mode):
    """Parses user input times safely handling decimals, colon formatting, or pure seconds."""
    if pd.isna(val) or str(val).strip() == "": return ""
    val_str = str(val).strip()
    if ":" in val_str: return val_str
    if not val_str.replace('.', '').isdigit(): return val_str 
    
    num = float(val_str)
    if "Total Seconds" in mode:
        mins = int(num // 60)
        secs = num % 60
        return f"{mins}:{secs:05.2f}".replace(".00", "")
    else:
        if "." in val_str:
            parts = val_str.split('.')
            whole_num = int(parts[0])
            decimal_part = "." + parts[1]
        else:
            whole_num = int(val_str)
            decimal_part = ""
            
        if len(str(whole_num)) <= 2:
            mins = whole_num // 60
            secs = whole_num % 60
            return f"{mins}:{secs:02d}{decimal_part}"
        else:
            secs = int(str(whole_num)[-2:])
            mins = int(str(whole_num)[:-2])
            mins += secs // 60
            secs = secs % 60
            return f"{mins}:{secs:02d}{decimal_part}"

def extract_seconds(time_str):
    """Uses Regex to extract total seconds from text strings for the Rest cycles."""
    m = re.search(r'(\d+):(\d+)', time_str)
    if m: return int(m.group(1)) * 60 + int(m.group(2))
    m2 = re.search(r'(\d+) minute', time_str)
    if m2: return int(m2.group(1)) * 60
    return None

def find_suggested_rest(category, compare_sec, rest_data_df):
    """Parses the text rules in the rest dataframe to figure out an athlete's interval cycle."""
    if not compare_sec or pd.isna(compare_sec): return "Rest data unavailable"
    subset = rest_data_df[rest_data_df["Workout"].str.contains(category, case=False, na=False)]
    
    for _, row in subset.iterrows():
        cond = str(row["Pace / Time"]).lower()
        res = str(row["Cycle / Rest"])
        times = re.findall(r'(\d+:\d+)', cond)
        
        if "sub" in cond or "under" in cond or "faster" in cond:
            if times and compare_sec < extract_seconds(times[0]): return res
        elif "+" in cond or "slower" in cond or "over" in cond:
            if times and compare_sec >= extract_seconds(times[0]): return res
        elif len(times) == 2:
            lower = extract_seconds(times[0])
            upper = extract_seconds(times[1])
            if lower <= compare_sec <= upper: return res
    return "Check Coach / Rest Chart directly"

# ==========================================
# --- DATES, SEASONS & DEMOGRAPHICS ---
# ==========================================

def get_grade_level(grad_year_str):
    """Calculates an athlete's current grade (9th, 10th) based on graduation year."""
    if str(grad_year_str).upper() == "COACH" or not str(grad_year_str).strip().isdigit(): return "Coach"
    grad_year = int(grad_year_str)
    today = datetime.date.today()
    current_season_year = today.year - 1 if today.month < 7 else today.year
    spring_grad_year = current_season_year + 1
    grade = 12 - (grad_year - spring_grad_year)
    
    if grade == 9: return "9th"
    elif grade == 10: return "10th"
    elif grade == 11: return "11th"
    elif grade == 12: return "12th"
    elif grade < 9: return "Middle School"
    elif grade > 12: return "Alumni"
    else: return "Unknown"

def calculate_season(date_val):
    """Calculates XC Season year based on a specific date (rolling over in July)."""
    try:
        d = pd.to_datetime(date_val)
        if pd.isna(d): return str(datetime.date.today().year)
        return str(d.year) if d.month >= 7 else str(d.year - 1)
    except:
        return str(datetime.date.today().year)

def add_season_column(df, date_col="Date"):
    """EFFICIENCY UPGRADE: Replaces the slow `.apply()` loop with vectorized math for dataframes."""
    if date_col in df.columns:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        today_year = datetime.date.today().year
        season_years = np.where(dates.dt.month >= 7, dates.dt.year, dates.dt.year - 1)
        df["Season"] = pd.Series(season_years).fillna(today_year).astype(int).astype(str)
    return df

# ==========================================
# --- EXTERNAL APIs & HTML FORMATTING ---
# ==========================================

@st.cache_data(ttl=86400) 
def get_weather_for_date(date_str):
    """Hits the Open-Meteo API to fetch historical weather or future forecasts for a date."""
    LATITUDE, LONGITUDE = 34.077604, -83.877289
    try:
        d_obj = pd.to_datetime(date_str)
        d = d_obj.strftime('%Y-%m-%d')
        days_ago = (pd.to_datetime("today") - d_obj).days
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={LATITUDE}&longitude={LONGITUDE}&start_date={d}&end_date={d}&daily=temperature_2m_max,precipitation_sum&temperature_unit=fahrenheit&precipitation_unit=inch&timezone=America/New_York" if days_ago > 60 else f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&start_date={d}&end_date={d}&daily=temperature_2m_max,precipitation_sum&temperature_unit=fahrenheit&precipitation_unit=inch&timezone=America/New_York"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            temp = data.get('daily', {}).get('temperature_2m_max', [None])[0]
            precip = data.get('daily', {}).get('precipitation_sum', [None])[0]
            if temp is None: return "Can't access weather data"
            desc = f"{round(temp)}°F"
            if precip and precip > 0.05: desc += f" ({round(precip, 1)}in Rain)"
            else: desc += " (Dry)"
            return desc
        return "Can't access weather data"
    except Exception: return "Can't access weather data"

def wrap_html_for_print(title, body_content, is_attendance=False):
    """Generates the hidden CSS document required to cleanly print roster/attendance sheets."""
    page_settings = "size: portrait;" if is_attendance else "size: auto;"
    return f"""<!DOCTYPE html>
    <style>
    /* Modern UI Variables applied for Print */
    :root {{
        --border-color: #cbd5e1; 
        --text-main: #1e293b; 
        --text-muted: #64748b;
        --font-family: 'Inter', system-ui, -apple-system, sans-serif;
        --mcxc-crimson: #8B2331;
    }}
    
    body {{ 
        font-family: var(--font-family); 
        padding: 20px; 
        margin: 0; 
        color: var(--text-main); 
        background-color: #ffffff;
    }}
    
    /* Setting margin to 0 specifically strips out the browser's default Date and URL headers! */
    @page {{ margin: 0; {page_settings} }}
    
    h2 {{ 
        margin: 0 0 10px 0; 
        font-size: 22px; 
        font-weight: 700; 
        text-align: center; 
        color: var(--text-main);
        letter-spacing: -0.5px;
        page-break-after: avoid; 
        break-after: avoid;
    }}
    
    h3 {{ 
        margin: 15px 0 0 0; 
        font-size: 14px; 
        font-weight: 600; 
        background-color: #f8fafc; 
        padding: 10px 15px; 
        border: 1px solid var(--border-color); 
        border-radius: 8px 8px 0 0;
        border-bottom: none;
        color: var(--text-main);
        page-break-after: avoid; 
        break-after: avoid;
    }}
    
    table {{ 
        width: 100%; 
        border-collapse: collapse; 
        margin-bottom: 25px; 
        page-break-inside: avoid; 
        break-inside: avoid;
        border: 1px solid var(--border-color); 
    }}
    
    tr {{ page-break-inside: avoid; page-break-after: auto; }}
    
    th, td {{ 
        padding: 10px 4px; 
        border: 1px solid var(--border-color); 
        text-align: center; 
        font-size: 12px; 
    }}
    
    th:first-child, td:first-child {{
        text-align: left;
        padding-left: 12px;
    }}
    
    th {{ 
        color: var(--text-muted); 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 0.5px; 
        font-size: 11px; 
        background: #f8fafc;
    }}
    
    .print-btn {{ 
        background: var(--mcxc-crimson); color: #ffffff; border: none; 
        padding: 12px 24px; border-radius: 6px; font-size: 14px; 
        font-weight: 600; cursor: pointer; transition: all 0.2s; 
        text-transform: uppercase; letter-spacing: 0.5px; 
        box-shadow: 0 4px 6px -1px rgba(139, 35, 49, 0.3);
        margin-bottom: 10px;
    }}
    .print-btn:hover {{ filter: brightness(1.1); transform: translateY(-1px); }}

    .keep-together {{
        page-break-inside: avoid;
        break-inside: avoid;
        margin-bottom: 25px;
    }}
    
    .no-print-container {{
        text-align: center; margin-bottom: 30px; padding: 20px; 
        background: #f0f4f8; border-radius: 12px; border: 1px solid var(--border-color);
    }}
    
    @media print {{ 
        .no-print {{ display: none !important; }} 
        body {{ padding: 0.5in; }} 
        * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }} 
    }}
    </style>
    <div class="no-print no-print-container">
        <button class="print-btn" onclick="window.print()">🖨️ Click Here to Print / Save as PDF</button>
        <p style="color: var(--text-muted); font-size: 13px; margin: 10px 0 0 0;"><strong>Pro Tip:</strong> For large rosters, set your printer "Scale" to <i>Fit to Page</i>.</p>
        <p style="color: var(--text-muted); font-size: 13px; margin: 5px 0 0 0;"><i>If you still see dates/URLs on the print preview, uncheck "Headers and Footers" in your print dialog box!</i></p>
    </div>
    {body_content}
    """
