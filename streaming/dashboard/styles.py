"""
CSS Styles for TikTok Safety Dashboard
"""

MAIN_CSS = """
<style>
    /* Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
    }

    /* CUSTOM HEADER COMPONENT STYLE */
    .header-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 24px 32px;
        border-radius: 16px;
        border-left: 6px solid #FE2C55;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 28px;
    }
    .header-title {
        color: #161823;
        font-size: 32px;
        font-weight: 800;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        color: #6B7280;
        font-size: 16px;
        margin-top: 10px;
        font-weight: 400;
    }

    /* CARD STYLING - Enhanced */
    .custom-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #E5E7EB;
        margin-bottom: 20px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .custom-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }

    /* METRICS CARD OVERRIDE */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 20px;
        border-radius: 14px;
        border-left: 5px solid #25F4EE;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetric"] label {
        font-weight: 600;
        color: #374151;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 800;
        color: #111827;
    }

    /* TERMINAL LOGS - Enhanced */
    .terminal-box {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        color: #00FF9C;
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        padding: 20px;
        border-radius: 12px;
        height: 380px;
        overflow-y: auto;
        font-size: 13px;
        border: 1px solid #30363d;
        line-height: 1.6;
    }
    .terminal-box::-webkit-scrollbar {
        width: 8px;
    }
    .terminal-box::-webkit-scrollbar-track {
        background: #21262d;
        border-radius: 4px;
    }
    .terminal-box::-webkit-scrollbar-thumb {
        background: #484f58;
        border-radius: 4px;
    }

    /* BADGES - Enhanced */
    .badge-harm {
        background: linear-gradient(135deg, #FE2C55 0%, #d91a40 100%);
        color: white;
        padding: 6px 16px;
        border-radius: 25px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 8px rgba(254, 44, 85, 0.3);
        display: inline-block;
    }
    .badge-safe {
        background: linear-gradient(135deg, #25F4EE 0%, #1dd6d0 100%);
        color: #161823;
        padding: 6px 16px;
        border-radius: 25px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 8px rgba(37, 244, 238, 0.3);
        display: inline-block;
    }
    .badge-unknown {
        background: linear-gradient(135deg, #9CA3AF 0%, #6B7280 100%);
        color: white;
        padding: 6px 16px;
        border-radius: 25px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }
    
    /* BUTTONS - Enhanced */
    div.stButton > button {
        font-weight: 600;
        border-radius: 12px;
        height: 48px;
        transition: all 0.3s ease;
        border: none;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FE2C55 0%, #d91a40 100%);
    }

    /* Video Card Grid */
    .video-card {
        background: white;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .video-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.15);
    }
    .video-card-content {
        padding: 16px;
    }
    .video-card-title {
        font-weight: 600;
        font-size: 14px;
        color: #111827;
        margin-bottom: 8px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    /* Gallery Grid */
    .gallery-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 20px;
        padding: 10px 0;
    }

    /* Stats Box */
    .stats-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 14px;
        text-align: center;
    }
    .stats-box h3 {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
    }
    .stats-box p {
        font-size: 0.9rem;
        opacity: 0.9;
        margin: 5px 0 0 0;
    }

    /* Table Styling */
    .dataframe {
        border-radius: 12px !important;
        overflow: hidden;
    }
    
    /* Expander Enhancement */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 15px;
    }

    /* Info/Warning/Success boxes */
    .stAlert {
        border-radius: 12px;
    }

    /* Sidebar Enhancement */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
    }
    section[data-testid="stSidebar"] .stImage {
        margin-bottom: 20px;
    }

    /* Tab Enhancement */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
    }

    /* Progress bar */
    .stProgress > div > div {
        border-radius: 10px;
    }

    /* Help tooltip */
    .help-panel {
        background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
        border: 1px solid #C7D2FE;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
    }
    .help-panel h4 {
        color: #4338CA;
        margin: 0 0 8px 0;
    }
    .help-panel p {
        color: #4B5563;
        margin: 0;
        font-size: 14px;
    }
</style>
"""


def get_styles():
    """Return the main CSS styles"""
    return MAIN_CSS
