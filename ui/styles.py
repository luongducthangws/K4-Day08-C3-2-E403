"""
Custom CSS styling and Material You Design Tokens for Luật Đi Làm Streamlit App.
"""

def get_custom_css(dark_mode: bool = True) -> str:
    """Return CSS string based on dark/light mode preference."""
    
    if dark_mode:
        bg_main = "#0b0f19"
        bg_surface = "#131b2e"
        bg_sidebar = "#090d16"
        text_primary = "#f8fafc"
        text_muted = "#94a3b8"
        border_color = "rgba(99, 102, 241, 0.2)"
        user_bubble_bg = "linear-gradient(135deg, #2e1065 0%, #3b0764 100%)"
        user_bubble_border = "rgba(192, 132, 252, 0.3)"
        assistant_bubble_bg = "linear-gradient(135deg, #131b2e 0%, #0f172a 100%)"
        assistant_bubble_border = "rgba(99, 102, 241, 0.25)"
    else:
        bg_main = "#f8fafc"
        bg_surface = "#ffffff"
        bg_sidebar = "#f1f5f9"
        text_primary = "#0f172a"
        text_muted = "#64748b"
        border_color = "rgba(99, 102, 241, 0.15)"
        user_bubble_bg = "linear-gradient(135deg, #818cf8 0%, #6366f1 100%)"
        user_bubble_border = "rgba(99, 102, 241, 0.3)"
        assistant_bubble_bg = "#ffffff"
        assistant_bubble_border = "rgba(226, 232, 240, 0.8)"

    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}

        /* App Main Canvas */
        .stApp {{
            background-color: {bg_main} !important;
            color: {text_primary} !important;
        }}

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: {bg_sidebar} !important;
            border-right: 1px solid {border_color} !important;
        }}

        /* Brand Container in Sidebar */
        .sidebar-brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 4px 18px 4px;
            border-bottom: 1px solid {border_color};
            margin-bottom: 16px;
        }}
        .brand-icon {{
            font-size: 2rem;
            background: linear-gradient(135deg, #c084fc 0%, #6366f1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .brand-title {{
            font-size: 1.35rem;
            font-weight: 800;
            color: {text_primary};
            letter-spacing: -0.3px;
            margin: 0;
            line-height: 1.2;
        }}
        .brand-tagline {{
            font-size: 0.78rem;
            color: {text_muted};
            margin: 2px 0 0 0;
        }}

        /* Top Header Styling */
        .app-header {{
            background: {bg_surface};
            border: 1px solid {border_color};
            border-radius: 20px;
            padding: 18px 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .header-title-box {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .status-dot {{
            width: 10px;
            height: 10px;
            background-color: #22c55e;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px #22c55e;
        }}

        /* Welcome Hero Screen */
        .welcome-hero {{
            text-align: center;
            padding: 32px 20px 24px 20px;
            max-width: 800px;
            margin: 0 auto;
        }}
        .welcome-avatar {{
            font-size: 3.2rem;
            margin-bottom: 12px;
            display: inline-block;
            background: linear-gradient(135deg, #c084fc 0%, #2dd4bf 100%);
            padding: 16px;
            border-radius: 24px;
            box-shadow: 0 10px 25px rgba(192, 132, 252, 0.25);
        }}
        .welcome-title {{
            font-size: 1.85rem;
            font-weight: 800;
            color: {text_primary};
            margin-bottom: 10px;
        }}
        .welcome-subtitle {{
            font-size: 1.02rem;
            color: {text_muted};
            line-height: 1.6;
            margin-bottom: 28px;
        }}

        /* Suggestion Cards Grid */
        .suggestion-card-btn {{
            background-color: {bg_surface} !important;
            border: 1px solid {border_color} !important;
            border-radius: 18px !important;
            padding: 16px !important;
            text-align: left !important;
            color: {text_primary} !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            transition: all 0.25s ease !important;
        }}
        .suggestion-card-btn:hover {{
            border-color: #c084fc !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(192, 132, 252, 0.2) !important;
        }}

        /* Chat Message Containers (Flexbox Left / Right Alignment) */
        .chat-row-user {{
            display: flex;
            justify-content: flex-end;
            margin-bottom: 20px;
            width: 100%;
        }}
        .chat-bubble-user {{
            background: {user_bubble_bg};
            border: 1px solid {user_bubble_border};
            color: #ffffff;
            padding: 16px 22px;
            border-radius: 22px 22px 4px 22px;
            max-width: 75%;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
            font-size: 0.96rem;
            line-height: 1.55;
        }}

        .chat-row-assistant {{
            display: flex;
            justify-content: flex-start;
            margin-bottom: 22px;
            width: 100%;
        }}
        .chat-bubble-assistant {{
            background: {assistant_bubble_bg};
            border: 1px solid {assistant_bubble_border};
            color: {text_primary};
            padding: 20px 24px;
            border-radius: 22px 22px 22px 4px;
            max-width: 85%;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            font-size: 0.96rem;
            line-height: 1.65;
        }}

        /* Source Chips / Cards */
        .source-chip {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(99, 102, 241, 0.12);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #c084fc;
            padding: 4px 12px;
            border-radius: 100px;
            font-size: 0.78rem;
            font-weight: 600;
            margin-right: 6px;
            margin-top: 6px;
        }}

        /* Risk Alert Cards */
        .risk-urgent-card {{
            background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%);
            border: 1px solid #ef4444;
            border-radius: 18px;
            padding: 18px 22px;
            color: #fef2f2;
            margin-bottom: 20px;
            box-shadow: 0 8px 24px rgba(239, 68, 68, 0.25);
        }}
        .risk-important-card {{
            background: linear-gradient(135deg, #451a03 0%, #78350f 100%);
            border: 1px solid #f59e0b;
            border-radius: 18px;
            padding: 16px 20px;
            color: #fffbeb;
            margin-bottom: 20px;
        }}

        /* Disclaimer Footer */
        .disclaimer-text {{
            font-size: 0.78rem;
            color: {text_muted};
            text-align: center;
            margin-top: 12px;
            margin-bottom: 20px;
            padding: 0 10px;
        }}

        /* Action Buttons Row for Assistant Messages */
        .msg-action-bar {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 12px;
            padding-top: 10px;
            border-top: 1px solid {border_color};
            font-size: 0.82rem;
        }}

        /* Streamlit Override Details */
        .stButton > button {{
            border-radius: 14px !important;
            transition: all 0.2s ease !important;
        }}
        .stTextInput > div > div > input {{
            border-radius: 14px !important;
        }}
        .stChatInput > div {{
            border-radius: 28px !important;
            border: 1px solid {border_color} !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
        }}
    </style>
    """
