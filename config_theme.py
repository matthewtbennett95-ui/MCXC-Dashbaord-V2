import streamlit as st
import streamlit.components.v1 as components
import base64

# ==========================================
# --- STREAMLIT UI HACKS ---
# ==========================================

# Aggressively hide all Streamlit branding and spacing
HIDE_ST_STYLE = """
    <style>
    /* Hide the default Streamlit footer */
    footer {visibility: hidden !important;}
    
    /* Hide the top right hamburger menu */
    [data-testid="stHeader"] {display: none !important;}
    
    /* Hide the floating 'Hosted with Streamlit' badge */
    .viewerBadge_container__1QSob {display: none !important;}
    [class^="viewerBadge_"] {display: none !important;}
    
    /* Bring the dashboard closer to the top of the phone screen */
    .block-container {padding-top: 1rem !important;}
    </style>
"""

def force_mobile_icon():
    """Forces mobile devices to use your logo for the 'Add to Home Screen' icon"""
    try:
        with open("mcxc_logo.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        icon_html = f"""
        <script>
            const doc = window.parent.document;
            let link = doc.querySelector("link[rel~='apple-touch-icon']");
            if (!link) {{
                link = doc.createElement('link');
                link.rel = 'apple-touch-icon';
                doc.head.appendChild(link);
            }}
            link.href = 'data:image/png;base64,{encoded_string}';
        </script>
        """
        components.html(icon_html, height=0, width=0)
    except Exception:
        pass

# ==========================================
# --- VISUAL THEMES DICTIONARY ---
# ==========================================

MCXC_CRIMSON = "#8B2331"
MCXC_NAVY = "#0C223F"
MCXC_GOLD = "#C7B683"

THEMES = {
    "MCXC Classic (Light)": {
        "bar": f"linear-gradient(to right, {MCXC_CRIMSON}, {MCXC_NAVY}, {MCXC_GOLD})", 
        "metric_bg": "rgba(139, 35, 49, 0.05)", "metric_border": "rgba(139, 35, 49, 0.2)",
        "line": MCXC_CRIMSON, "app_bg": "#FFFFFF", "text": "#31333F", 
        "header": MCXC_NAVY, "sidebar_bg": "#F0F2F6", "plotly_template": "plotly_white", "is_dark": False
    },
    "MCXC Elite (Dark)": {  
        "bar": f"linear-gradient(to right, {MCXC_CRIMSON}, {MCXC_GOLD}, {MCXC_CRIMSON})", 
        "metric_bg": "rgba(199, 182, 131, 0.1)", "metric_border": "rgba(199, 182, 131, 0.3)",
        "line": MCXC_GOLD, "app_bg": MCXC_NAVY, "text": "#FFFFFF", 
        "header": MCXC_GOLD, "sidebar_bg": "#08182D", "plotly_template": "plotly_dark", "is_dark": True
    },
    "Midnight Runner (Dark)": {
        "bar": "linear-gradient(to right, #FF4B4B, #FF904F)", 
        "metric_bg": "rgba(255, 75, 75, 0.1)", "metric_border": "rgba(255, 75, 75, 0.3)",
        "line": "#FF4B4B", "app_bg": "#0E1117", "text": "#FFFFFF", 
        "header": MCXC_GOLD, "sidebar_bg": "#1A1C24", "plotly_template": "plotly_dark", "is_dark": True
    },
    "Ocean Pace (Light)": {
        "bar": "linear-gradient(to right, #00C9FF, #92FE9D)", 
        "metric_bg": "rgba(0, 201, 255, 0.05)", "metric_border": "rgba(0, 201, 255, 0.3)",
        "line": "#00C9FF", "app_bg": "#F4F8FB", "text": "#1A2A3A", 
        "header": "#00C9FF", "sidebar_bg": "#E5F0F9", "plotly_template": "plotly_white", "is_dark": False
    },
    "Forest Trail (Light)": {
        "bar": "linear-gradient(to right, #2E7D32, #81C784)", 
        "metric_bg": "rgba(46, 125, 50, 0.05)", "metric_border": "rgba(46, 125, 50, 0.3)",
        "line": "#2E7D32", "app_bg": "#F1F8E9", "text": "#1B5E20", 
        "header": "#1B5E20", "sidebar_bg": "#E8F5E9", "plotly_template": "plotly_white", "is_dark": False
    },
    "Neon Track (Dark)": {
        "bar": "linear-gradient(to right, #E040FB, #18FFFF)", 
        "metric_bg": "rgba(224, 64, 251, 0.1)", "metric_border": "rgba(24, 255, 255, 0.3)",
        "line": "#18FFFF", "app_bg": "#121212", "text": "#FFFFFF", 
        "header": "#E040FB", "sidebar_bg": "#1E1E1E", "plotly_template": "plotly_dark", "is_dark": True
    }
}

# ==========================================
# --- THEME INJECTION FUNCTION ---
# ==========================================

def apply_theme(theme_name):
    """Generates and injects the CSS required for the selected theme."""
    current_theme = THEMES.get(theme_name, THEMES["MCXC Classic (Light)"])
    
    dark_mode_css = ""
    if current_theme["is_dark"]:
        dark_mode_css = f"""
            [data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-baseweb="base-input"] {{
                background-color: rgba(0,0,0,0.4) !important;
                color: #FFFFFF !important; border-color: rgba(255,255,255,0.2) !important;
            }}
            [data-testid="stForm"] {{ background-color: {current_theme['sidebar_bg']} !important;
                border-color: rgba(255,255,255,0.1) !important; }}
            input, textarea, select {{ color: #FFFFFF !important; }}
            [data-testid="stDataFrame"], [data-testid="stDataEditor"] {{ filter: invert(0.92) hue-rotate(180deg); }}
        """

    custom_css = f"""
        <style>
            .stApp {{ background-color: {current_theme['app_bg']} !important; }}
            [data-testid="stSidebar"] {{ background-color: {current_theme['sidebar_bg']} !important; }}
            [data-testid="stHeader"] {{ background-color: transparent !important; }}
            
            .color-bar {{ height: 8px; background: {current_theme['bar']}; margin-bottom: 2rem; border-radius: 4px; }}
            div[data-testid="metric-container"] {{ 
                background-color: {current_theme['metric_bg']} !important; 
                border: 1px solid {current_theme['metric_border']} !important; 
                padding: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
            }}
            
            h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ 
                color: {current_theme['header']} !important; 
            }}
            
            .stMarkdown p, .stMarkdown li, .stMarkdown span, div[data-testid="stCaptionContainer"], 
            label, .stMetricValue, div[data-testid="stTabs"] button p {{ 
                color: {current_theme['text']} !important; 
            }}
            
            div.stButton > button, div.stFormSubmitButton > button {{ 
                background-color: {current_theme['sidebar_bg']} !important;
                color: {current_theme['text']} !important; 
                border: 1px solid {current_theme['metric_border']} !important; 
                transition: all 0.3s ease; 
            }}
            
            div.stButton > button:hover, div.stFormSubmitButton > button:hover {{ 
                border-color: {current_theme['line']} !important;
                color: {current_theme['line']} !important; 
                background-color: {current_theme['app_bg']} !important; 
            }}
            
            {dark_mode_css}
        </style>
        <div class="color-bar"></div>
    """
    
    st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)
    st.markdown(custom_css, unsafe_allow_html=True)
    return current_theme
