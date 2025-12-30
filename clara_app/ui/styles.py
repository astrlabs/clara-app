import streamlit as st

APP_STYLES = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Chat typography & spacing, mobile-friendly but safe for desktop */
@media (max-width: 600px) {
    .chat-line {
        font-size: 0.98rem;
        line-height: 1.5;
    }
}

.chat-line {
    margin: 0.35rem 0;
}

.chat-line .name {
    display: block;
    font-weight: 600;
    font-size: 0.82rem;
    margin-bottom: 0.15rem;
    opacity: 0.95;
}

.chat-line .msg {
    display: inline-block;
    padding: 0.55rem 0.8rem;
    border-radius: 0.9rem;
    max-width: 100%;
    word-wrap: break-word;
    color: #E5E7EB; /* soft off-white for message text */
}

.clara-label {
    color: #60A5FA; /* muted blue for Clara's name */
}

.user-label {
    color: #2DD4BF; /* soft teal for user name */
}

.chat-line.clara .msg {
    background: rgba(148, 163, 184, 0.12);
}

.chat-line.user .msg {
    background: rgba(56, 189, 248, 0.18);
}

/* Safe chat labels (used in non-retro mode) */
.chat-name {
    display: block;
    font-weight: 600;
    font-size: 0.82rem;
    margin: 0 0 0.15rem 0;
    opacity: 0.95;
}

/* Data & Privacy sidebar text: slightly smaller and softer */
.privacy-text {
    font-size: 0.8rem;
    line-height: 1.4;
    color: #9CA3AF; /* muted gray */
}

.privacy-text h2,
.privacy-text h3,
.privacy-text strong {
    color: #D1D5DB; /* lighter gray for headings/emphasis */
}

/* Sidebar overall: slightly smaller, tighter spacing, no heavy borders */
[data-testid="stSidebar"] * {
    font-size: 0.9rem;
}

[data-testid="stSidebar"] .st-expander {
    border: none;
    padding-top: 0.1rem;
    padding-bottom: 0.1rem;
}

[data-testid="stSidebar"] .st-expanderHeader {
    padding-top: 0.25rem;
    padding-bottom: 0.25rem;
}

[data-testid="stSidebar"] .st-expanderContent {
    padding-top: 0.25rem;
    padding-bottom: 0.4rem;
}

/* Force sidebar buttons to be left-aligned */
[data-testid="stSidebar"] .stButton button {
    width: 100%;
    text-align: left;
    display: flex;
    justify-content: flex-start;
    padding-left: 1rem;
}


/* RED BUTTON OVERRIDES – Danger Zone delete buttons */
.danger-delete button {
    background-color: #FF4B4B !important;
    border-color: #FF4B4B !important;
    color: white !important;
}

.danger-delete button:hover {
    background-color: #D93434 !important;
    border-color: #D93434 !important;
    color: white !important;
}

/* Footer / Disclaimer text */
.footer-text {
    font-size: 0.75rem;
    color: #9CA3AF; /* muted gray */
    text-align: center;
    margin-top: 2rem;
    padding-bottom: 1rem;
    opacity: 0.8;
}

.footer-text a {
    color: #9CA3AF;
    text-decoration: underline;
}
</style>
"""

def apply_styles():
    st.markdown(APP_STYLES, unsafe_allow_html=True)
