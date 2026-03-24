import streamlit as st
import requests
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Car Lease AI - Contract Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(105deg, #667eea 0%, #264ba2 100%);
    }
    .main-header {
        color: white;
        text-align: center;
        padding: 2rem;
        font-size: 3rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 1rem;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .vin-box {
        background: linear-gradient(105deg, #667eea 0%, #264ba2 100%);        
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        font-size: 28px;
        font-family: monospace;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        margin: 1rem 0;
        border: 2px solid rgba(255,255,255,0.3);
    }
    .section-header {
        color: white;
        padding: 15px 0;
        border-bottom: 3px solid #4CAF50;
        margin: 1.5rem 0 1rem 0;
        font-size: 1.8rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    .high-risk {
        background: linear-gradient(105deg, #667eea 0%, #264ba2 100%);       
        border-radius: 10px;
        margin: 5px 0;
        color: white;
        box-shadow: 0 5px 15px rgba(244, 67, 54, 0.3);
        border-left: 5px solid #ffeb3b;
    }
    .medium-risk {
        background: linear-gradient(105deg, #667eea 0%, #264ba2 100%);        
        padding: 15px;            
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        color: white;
        box-shadow: 0 5px 15px rgba(255, 152, 0, 0.3);
        border-left: 5px solid #ffeb3b;
    }
    .low-risk {
        background: linear-gradient(105deg, #667eea 0%, #264ba2 100%);                  
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        color: white;
        box-shadow: 0 5px 15px rgba(33, 150, 243, 0.3);
        border-left: 5px solid #ffeb3b;
    }
    .upload-container {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 15px;
        border: 2px dashed rgba(76, 175, 80, 0.5);
        text-align: center;
        margin: 1rem 0;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: rgba(255,255,255,0.1);
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        border-radius: 4px;
        color: white;
    }
    .dashboard-toggle {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 1rem 0 2rem 0;
    }
    .dashboard-btn {
        padding: 0.75rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 1.1rem;
        cursor: pointer;
        transition: all 0.3s;
        border: 2px solid #4CAF50;
        background-color: white;
        color: #4CAF50;
    }
    .dashboard-btn-active {
        background-color: #4CAF50;
        color: white;
    }
    .dashboard-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .vin-input-container {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid rgba(33, 150, 243, 0.5);
        margin: 1rem 0;
        color: white;
    }
    .vehicle-detail-card {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(5px);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .metric-card {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(5px);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
     .stChatMessage {
        background: rgba(255,255,255,0.1) !important;
        backdrop-filter: blur(5px);
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Chat input area */
    .stChatInput {
        background: rgba(255,255,255,0.1) !important;
        backdrop-filter: blur(5px);
        border-radius: 10px;
    }
    
    /* Chat message text content - User and Assistant messages */
    .stChatMessage [data-testid="stMarkdownContainer"] p,
    .stChatMessage div[data-testid="stMarkdownContainer"] p,
    .stChatMessage .st-emotion-cache-1v0mbdj p,
    .stChatMessage .st-emotion-cache-16idsys p {
        color: white !important;
    }
    
    /* Specific styling for user messages */
    .stChatMessage[data-testid="user"] {
        background: rgba(102, 126, 234, 0.2) !important;
    }
    
    /* Specific styling for assistant messages */
    .stChatMessage[data-testid="assistant"] {
        background: rgba(38, 75, 162, 0.2) !important;
    }
    
    /* Chat input text styling */
    .stChatInput textarea,
    .stChatInput input {
        color: black !important;
        background: rgba(255,255,255,0.05) !important;
    }
    
    /* Chat input placeholder */
    .stChatInput textarea::placeholder,
    .stChatInput input::placeholder {
        color: rgba(255,255,255,0.7) !important;
    }
    
    /* Override Streamlit default colors */
    .stApp h1, .stApp h2, .stApp h3, .stApp p {
        color: white !important;
    }
    
    /* Additional selectors for various Streamlit elements */
    .stApp .st-cb {
        color: white;
    }
    
    .stApp .st-emotion-cache-16idsys p {
        color: white !important;
    }
    
    .stApp .st-emotion-cache-1v0mbdj p {
        color: white !important;
    }
    
    .stApp .st-emotion-cache-1v0mbdj {
        color: white !important;
    }
    
    .stApp .st-emotion-cache-1dj0hjr {
        color: white !important;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(105deg, #667eea 0%, #264ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    /* Download button styling */
    .stDownloadButton button {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        border: none;
    }
    
    /* Alert styling */
    .stAlert {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(5px);
        color: white;
        border: 1px solid rgba(255,255,255,0.2);
    }
</style>
""", unsafe_allow_html=True)



# Title
st.markdown("""
<h1 class='main-header'>
    Car Lease AI - Contract Analyzer
</h1>
""", unsafe_allow_html=True)

# Backend URL
BACKEND_URL = "http://localhost:8000"

# Initialize session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Contract Analysis"
if 'vin_report_result' not in st.session_state:
    st.session_state.vin_report_result = None
if 'vin_input' not in st.session_state:
    st.session_state.vin_input = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Test backend connection (silent check)
try:
    response = requests.get(f"{BACKEND_URL}/", timeout=5)
    if response.status_code == 200:
        st.session_state.connection_status = "✅ Connected"
    else:
        st.session_state.connection_status = "❌ Error"
        st.error("❌ Backend server error. Please check if it's running correctly.")
        st.stop()
except requests.exceptions.ConnectionError:
    st.session_state.connection_status = "❌ Cannot connect"
    st.error("❌ Cannot connect to backend. Please make sure it's running on http://localhost:8000")
    st.stop()
except Exception as e:
    st.session_state.connection_status = f"❌ Error"
    st.error(f"❌ Error connecting to backend: {str(e)}")
    st.stop()

# Dashboard Toggle (Centered)
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown("<div class='dashboard-toggle'>", unsafe_allow_html=True)
    dash_col1, dash_col2, dash_col3 = st.columns(3)
    
    with dash_col1:
        if st.button("📄 Contract Analysis", 
                    use_container_width=True,
                    type="primary" if st.session_state.current_page == "Contract Analysis" else "secondary"):
            st.session_state.current_page = "Contract Analysis"
            st.rerun()
    
    with dash_col2:
        if st.button("🔍 VIN Report", 
                    use_container_width=True,
                    type="primary" if st.session_state.current_page == "VIN Report" else "secondary"):
            st.session_state.current_page = "VIN Report"
            st.rerun()
    
    with dash_col3:
        if st.button("🤖 AI Assistant", 
                    use_container_width=True,
                    type="primary" if st.session_state.current_page == "AI Assistant" else "secondary"):
            st.session_state.current_page = "AI Assistant"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Connection status in small text (minimal)
if st.session_state.connection_status:
    if "✅" in st.session_state.connection_status:
        st.caption(f"🟢 {st.session_state.connection_status} to Backend")
    else:
        st.caption(f"🔴 {st.session_state.connection_status}")

# UPDATED: Helper function to count risks by level
def count_risks_by_level(risk_data, level=None):
    """Count risks, optionally filtered by level"""
    if not risk_data:
        return 0
    
    risks = risk_data.get("risks", [])
    
    if not isinstance(risks, list):
        return 0
    
    if level:
        return len([r for r in risks if r.get("level") == level and r.get("message")])
    else:
        return len([r for r in risks if r.get("message")])

# Helper function to safely get numeric value
def get_numeric_value(value):
    """Extract numeric value from various formats"""
    if value is None:
        return None
    try:
        if isinstance(value, str):
            # Remove any non-numeric characters except decimal point
            clean_value = ''.join(c for c in value if c.isdigit() or c == '.')
            if clean_value:
                return float(clean_value)
            else:
                return None
        elif isinstance(value, (int, float)):
            return float(value)
        else:
            return None
    except (ValueError, TypeError):
        return None

# Helper function to format price
def format_price(price_value):
    """Format price value to currency string"""
    if price_value is None:
        return None
    try:
        # Try to convert to float if it's a string
        if isinstance(price_value, str):
            # Remove any non-numeric characters except decimal point
            clean_price = ''.join(c for c in price_value if c.isdigit() or c == '.')
            if clean_price:
                price_float = float(clean_price)
                return f"${price_float:,.2f}"
            else:
                return None
        elif isinstance(price_value, (int, float)):
            return f"${price_value:,.2f}"
        else:
            return None
    except (ValueError, TypeError):
        return None

# Main content area
if st.session_state.current_page == "Contract Analysis":
    
    # Main upload section
    st.markdown("### 📤 Upload Your Document")
    
    st.markdown("<div class='upload-container'>", unsafe_allow_html=True)
    st.markdown("#### Choose a file to analyze")
    st.caption("Supports: PDF, PNG, JPG, JPEG, TIFF, BMP, TXT")
    
    # File uploader with proper label
    uploaded_file = st.file_uploader(
        "Document Upload",
        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'txt'],
        label_visibility="collapsed",
        key="file_uploader"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Selected: {uploaded_file.name} (Size: {uploaded_file.size / 1024:.1f} KB)")
        
        # Analyze button
        if st.button("🚀 Analyze Contract", type="primary", use_container_width=True):
            with st.spinner("🔄 Processing contract... This may take a moment."):
                try:
                    # Prepare file for upload
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                    
                    # Send to backend
                    response = requests.post(f"{BACKEND_URL}/upload", files=files, timeout=60)
                    
                    if response.status_code == 200:
                        st.session_state.analysis_result = response.json()
                        st.success("✅ Analysis complete!")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    else:
        st.info("👆 Please upload a file to begin analysis")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Display results if available
    if st.session_state.analysis_result:
        data = st.session_state.analysis_result
        
        st.markdown("## 📊 Analysis Results")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["🔑 VIN & Vehicle", "⚖️ SLA Data", "📊 Risk Assessment"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<h3 class='section-header'>🔑 VIN Number</h3>", unsafe_allow_html=True)
                vin = data.get('vin', 'Not found')
                st.markdown(f"<div class='vin-box'>{vin}</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<h3 class='section-header'>🚗 Vehicle Details</h3>", unsafe_allow_html=True)
                vehicle_data = data.get('vehicle_data', {})
                if vehicle_data:
                    for key, value in vehicle_data.items():
                        if value:  # Only show non-empty values
                            st.markdown(f"<div class='vehicle-detail-card'><strong>{key}:</strong> {value}</div>", unsafe_allow_html=True)
                else:
                    st.info("No vehicle details found")
        
        with tab2:
            st.markdown("<h3 class='section-header'>⚖️ SLA Information</h3>", unsafe_allow_html=True)
            if data.get('sla_data') and len(data['sla_data']) > 0:
                sla_data = data['sla_data']
                for category, details in sla_data.items():
                    if isinstance(details, dict) and details:
                        with st.expander(f"📋 {category}"):
                            for key, value in details.items():
                                st.markdown(f"<div class='vehicle-detail-card'><strong>{key}:</strong> {value}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='vehicle-detail-card'><strong>{category}:</strong> {details}</div>", unsafe_allow_html=True)
            else:
                st.info("No SLA data found")
        
        with tab3:
            st.markdown("<h3 class='section-header'>📊 Risk Assessment Dashboard</h3>", unsafe_allow_html=True)
            
            risk = data.get("risk_report", {})
            
            if risk:
                score = risk.get("contract_fairness_score")
                risks = risk.get("risks", [])
                
                # Count risks by level
                high_risks = count_risks_by_level(risk, "high")
                medium_risks = count_risks_by_level(risk, "medium")
                low_risks = count_risks_by_level(risk, "low")
                total_risks = len(risks)
                
                st.caption(f"Debug: Found {total_risks} total risks ({high_risks} high, {medium_risks} medium, {low_risks} low)")
                
                # Create columns for metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    if score is not None:
                        st.metric("Fairness Score", f"{score}/100", delta=None)
                        
                        # Create gauge chart for score
                        fig = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = score,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "Score"},
                            gauge = {
                                'axis': {'range': [None, 100]},
                                'bar': {'color': "#4CAF50" if score >= 80 else "#FFC107" if score >= 60 else "#f44336"},
                                'steps': [
                                    {'range': [0, 50], 'color': "#ffebee"},
                                    {'range': [50, 75], 'color': "#fff3e0"},
                                    {'range': [75, 100], 'color': "#e8f5e8"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': score
                                }
                            }
                        ))
                        fig.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', font_color='white')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.metric("Fairness Score", "N/A")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.metric("High Risks", high_risks)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col3:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.metric("Medium Risks", medium_risks)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col4:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.metric("Low Risks", low_risks)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Risk distribution charts
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    # Risk distribution pie chart
                    if total_risks > 0:
                        risk_counts = {
                            'High': high_risks,
                            'Medium': medium_risks,
                            'Low': low_risks
                        }
                        
                        # Filter out zero values
                        risk_counts = {k: v for k, v in risk_counts.items() if v > 0}
                        
                        if risk_counts:
                            fig = go.Figure(data=[go.Pie(
                                labels=list(risk_counts.keys()),
                                values=list(risk_counts.values()),
                                hole=.3,
                                marker_colors=['#f44336', '#ff9800', '#2196F3']
                            )])
                            fig.update_layout(
                                title="Risk Distribution by Severity",
                                height=300,
                                margin=dict(l=10, r=10, t=30, b=10),
                                paper_bgcolor='rgba(0,0,0,0)',
                                font_color='white'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.markdown("### ✅ No Risks")
                        st.markdown("No risks detected in the contract")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    # Risk severity bar chart
                    if total_risks > 0:
                        risk_data = pd.DataFrame({
                            'Severity': ['High', 'Medium', 'Low'],
                            'Count': [high_risks, medium_risks, low_risks]
                        })
                        
                        fig = px.bar(risk_data, x='Severity', y='Count', 
                                   color='Severity',
                                   color_discrete_map={'High': '#f44336', 'Medium': '#ff9800', 'Low': '#2196F3'},
                                   text='Count')
                        fig.update_traces(textposition='outside')
                        fig.update_layout(
                            title="Risk Counts by Severity",
                            height=300,
                            margin=dict(l=10, r=10, t=30, b=10),
                            showlegend=False,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(255,255,255,0.1)',
                            font_color='white'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.markdown("### ✅ No Risks")
                        st.markdown("The contract appears to be risk-free!")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # UPDATED: Display all risks with appropriate styling
                if risks and len(risks) > 0:
                    st.markdown("### ⚠️ Detected Risks")
                    
                    # Sort risks by severity (high first, then medium, then low)
                    sorted_risks = sorted(risks, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x.get('level', 'low'), 3))
                    
                    for risk_item in sorted_risks:
                        level = risk_item.get('level', 'low')
                        message = risk_item.get('message', '')
                        
                        if level == 'high':
                            st.markdown(
                                f"<div class='high-risk'><strong>🔴 HIGH RISK:</strong> {message}</div>",
                                unsafe_allow_html=True
                            )
                        elif level == 'medium':
                            st.markdown(
                                f"<div class='medium-risk'><strong>🟠 MEDIUM RISK:</strong> {message}</div>",
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"<div class='low-risk'><strong>🔵 LOW RISK:</strong> {message}</div>",
                                unsafe_allow_html=True
                            )
                else:
                    st.success("✅ No risks detected in the contract")
            else:
                st.success("✅ No risk analysis available")
        
        # Summary section with enhanced metrics
        st.divider()
        st.markdown("<h3 class='section-header'>📋 Analysis Summary Dashboard</h3>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("VIN Found", "✅" if data.get('vin') else "❌")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            vehicle_count = len(data.get('vehicle_data', {}))
            st.metric("Vehicle Details", vehicle_count)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            sla_count = len(data.get('sla_data', {}))
            st.metric("SLA Fields", sla_count)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col4:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            risk = data.get("risk_report", {})
            total_risks = count_risks_by_level(risk)
            st.metric("Total Risks", total_risks)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Add a risk severity breakdown
        if risk and total_risks > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            
            # Create a stacked bar chart for risk levels
            risk_levels = pd.DataFrame({
                'Risk Level': ['High', 'Medium', 'Low'],
                'Count': [
                    count_risks_by_level(risk, 'high'),
                    count_risks_by_level(risk, 'medium'),
                    count_risks_by_level(risk, 'low')
                ]
            })
            
            fig = px.bar(risk_levels, x='Risk Level', y='Count', 
                        color='Risk Level',
                        color_discrete_map={'High': '#f44336', 'Medium': '#ff9800', 'Low': '#2196F3'},
                        text='Count')
            fig.update_traces(textposition='outside')
            fig.update_layout(
                title="Risk Severity Breakdown",
                height=300,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(255,255,255,0.1)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Download button for analysis report
        st.download_button(
            label="📥 Download Analysis Report",
            data=json.dumps(data, indent=2),
            file_name=f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    else:
        # Welcome message when no data
        st.markdown("""
        <div style='text-align: center; padding: 30px; background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 15px; color: white;'>
            <h3 style='color: white;'>👋 Welcome to Car Lease AI Assistant</h3>
            <p style='color: rgba(255,255,255,0.9);'>
                Upload a contract file above to begin analysis<br>
                The system will extract VIN, vehicle details, SLA information, and identify risks
            </p>
        </div>
        """, unsafe_allow_html=True)


elif st.session_state.current_page == "VIN Report":
    st.markdown("## 🔍 VIN Decoder & Vehicle Report")
    
    st.markdown("""
    <div style='background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; color: white;'>
        <h4 style='margin:0; color: white;'>🔎 Enter a 17-character VIN to get detailed vehicle information</h4>
        <p style='margin:0; color: rgba(255,255,255,0.8);'>Get comprehensive vehicle details including make, model, year, engine specifications, and price estimation.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # VIN Input Section
    st.markdown("<div class='vin-input-container'>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 📝 Enter VIN Number")
        vin_input = st.text_input(
            "VIN Number",
            value=st.session_state.vin_input,
            placeholder="e.g., 1HGCM82633A004352",
            max_chars=17,
            label_visibility="collapsed"
        )
        
        # Validate VIN length
        vin_valid = len(vin_input) == 17 if vin_input else False
        
        if vin_input and not vin_valid:
            st.warning("⚠️ VIN must be exactly 17 characters")
        
        # Decode button
        if st.button("🔍 Decode VIN", type="primary", use_container_width=True, disabled=not vin_valid):
            with st.spinner("🔄 Fetching vehicle information..."):
                try:
                    payload = {"vin": vin_input}
                    response = requests.post(f"{BACKEND_URL}/vin_report", json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        st.session_state.vin_report_result = response.json()
                        st.session_state.vin_input = vin_input
                        st.success("✅ VIN decoded successfully!")
                        st.rerun()
                    else:
                        error_data = response.json()
                        st.error(f"❌ Error: {error_data.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Display VIN Report Results
    if st.session_state.vin_report_result:
        data = st.session_state.vin_report_result
        
        if "error" in data:
            st.error(f"❌ {data['error']}")
        else:
            st.markdown("## 📋 Vehicle Details Report")
            
            # Display VIN in a prominent box
            st.markdown(f"<div class='vin-box'>{data.get('vin', 'N/A')}</div>", unsafe_allow_html=True)
            
            # Create tabs for different sections
            vin_tab1, vin_tab2, vin_tab3 = st.tabs(["🚗 Vehicle Details", "💰 Price Dashboard", "🔍 Raw Data"])
            
            with vin_tab1:
                vehicle_details = data.get('vehicle_details', {})
                
                # Create columns for vehicle details
                col1, col2 = st.columns(2)
                
                # Define which fields to show and their display names
                fields_to_show = {
                    "make": "🏭 Make",
                    "model": "🚗 Model",
                    "year": "📅 Year",
                    "series": "📊 Series",
                    "trim": "✨ Trim",
                    "vehicle_type": "🚘 Vehicle Type",
                    "body_class": "🛞 Body Class",
                    "doors": "🚪 Doors",
                    "drive_type": "⚙️ Drive Type",
                    "engine_cylinders": "🔧 Engine Cylinders",
                    "fuel_type": "⛽ Fuel Type",
                    "manufacturer": "🏢 Manufacturer",
                    "engine_model": "🔧 Engine Model",
                    "engine_manufacturer": "🏭 Engine Manufacturer",
                    "brake_system_type": "🛑 Brake System",
                    "transmission_style": "⚙️ Transmission",
                    "transmission_speeds": "⚡ Transmission Speeds",
                    "fuel_type_primary": "⛽ Primary Fuel",
                    "hybrid": "⚡ Hybrid",
                    "electric_vehicle_type": "🔋 EV Type",
                    "battery_type": "🔋 Battery Type",
                    "battery_voltage": "⚡ Battery Voltage",
                    "battery_capacity": "🔋 Battery Capacity",
                    "range": "📏 Range",
                    "fuel_capacity_gallons": "⛽ Fuel Capacity",
                    "horsepower": "🐎 Horsepower",
                    "engine_displacement": "📏 Engine Displacement",
                    "engine_configuration": "⚙️ Engine Configuration",
                    "valve_design": "🚪 Valve Design",
                    "aspiration": "💨 Aspiration",
                    "fuel_delivery": "⛽ Fuel Delivery"
                }
                
                with col1:
                    st.markdown("<h3 class='section-header'>Basic Information</h3>", unsafe_allow_html=True)
                    basic_fields = ["make", "model", "year", "series", "trim", "vehicle_type", "body_class", "manufacturer"]
                    for field in basic_fields:
                        if field in fields_to_show and vehicle_details.get(field):
                            value = vehicle_details[field]
                            if value and str(value).strip() and str(value).lower() not in ["unknown", "n/a"]:
                                st.markdown(f"""
                                <div class='vehicle-detail-card'>
                                    <strong>{fields_to_show[field]}:</strong><br>
                                    <span style='font-size: 1.1rem;'>{value}</span>
                                </div>
                                """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<h3 class='section-header'>Technical Specifications</h3>", unsafe_allow_html=True)
                    tech_fields = ["doors", "drive_type", "engine_cylinders", "fuel_type", "engine_model", 
                                 "transmission_style", "horsepower", "engine_displacement", "fuel_type_primary",
                                 "electric_vehicle_type", "battery_type", "range"]
                    for field in tech_fields:
                        if field in fields_to_show and vehicle_details.get(field):
                            value = vehicle_details[field]
                            if value and str(value).strip() and str(value).lower() not in ["unknown", "n/a"]:
                                st.markdown(f"""
                                <div class='vehicle-detail-card'>
                                    <strong>{fields_to_show[field]}:</strong><br>
                                    <span style='font-size: 1.1rem;'>{value}</span>
                                </div>
                                """, unsafe_allow_html=True)
            
            with vin_tab2:
                st.markdown("<h3 class='section-header'>💰 Price Dashboard</h3>", unsafe_allow_html=True)
                
                # Check for price data in the root of the response
                estimated_price = data.get('estimated_price')
                confidence_score = data.get('confidence_score')
                
                # Get numeric values for calculations
                numeric_estimated = get_numeric_value(estimated_price)
                numeric_confidence = get_numeric_value(confidence_score)
                
                if numeric_estimated is not None:
                    # Main price display with styling based on confidence
                    confidence = numeric_confidence if numeric_confidence is not None else 70
                    
                    # Create columns for price metrics
                    price_col1, price_col2, price_col3 = st.columns(3)
                    
                    with price_col1:
                        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                        formatted_price = format_price(estimated_price)
                        if formatted_price:
                            st.metric("Estimated Price", formatted_price)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with price_col2:
                        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                        if numeric_confidence is not None:
                            st.metric("Confidence Score", f"{numeric_confidence:.0f}%")
                            
                            # Confidence gauge
                            fig = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = numeric_confidence,
                                domain = {'x': [0, 1], 'y': [0, 1]},
                                title = {'text': "Confidence"},
                                gauge = {
                                    'axis': {'range': [None, 100]},
                                    'bar': {'color': "#4CAF50" if numeric_confidence >= 80 else "#FFC107" if numeric_confidence >= 60 else "#FF9800"},
                                    'steps': [
                                        {'range': [0, 50], 'color': "#ffebee"},
                                        {'range': [50, 75], 'color': "#fff3e0"},
                                        {'range': [75, 100], 'color': "#e8f5e8"}
                                    ]
                                }
                            ))
                            fig.update_layout(height=150, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', font_color='white')
                            st.plotly_chart(fig, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with price_col3:
                        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                        # Vehicle condition
                        vehicle_details = data.get('vehicle_details', {})
                        condition = vehicle_details.get('condition') or data.get('condition', 'Average')
                        condition_emoji = "🟢" if condition and condition.lower() in ["excellent", "good"] else "🟡" if condition and condition.lower() == "fair" else "🔴"
                        st.metric("Condition", f"{condition_emoji} {condition if condition else 'Average'}")
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Price factors visualization
                    price_factors = data.get('price_factors', [])
                    if price_factors:
                        st.markdown("<h4 style='margin-top: 2rem; color: white;'>🎯 Key Price Factors</h4>", unsafe_allow_html=True)
                        
                        if isinstance(price_factors, list):
                            for i, factor in enumerate(price_factors):
                                if factor and str(factor).strip():
                                    st.markdown(f"""
                                    <div style='background: rgba(255,255,255,0.1); backdrop-filter: blur(5px); padding: 0.75rem 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #2196F3; color: white;'>
                                        {factor}
                                    </div>
                                    """, unsafe_allow_html=True)
                        elif isinstance(price_factors, dict):
                            for key, value in price_factors.items():
                                if value and str(value).strip():
                                    st.markdown(f"""
                                    <div style='background: rgba(255,255,255,0.1); backdrop-filter: blur(5px); padding: 0.75rem 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #2196F3; color: white;'>
                                        <strong>{key.replace('_', ' ').title()}:</strong> {value}
                                    </div>
                                    """, unsafe_allow_html=True)
                    
                    # Market trends with visualization
                    market_trends = data.get('market_trends', {})
                    if market_trends:
                        st.markdown("<h4 style='margin-top: 2rem; color: white;'>📈 Market Trends</h4>", unsafe_allow_html=True)
                        
                        trend_col1, trend_col2, trend_col3 = st.columns(3)
                        
                        with trend_col1:
                            trend_value = market_trends.get('trend', 'Stable')
                            if isinstance(trend_value, str):
                                if trend_value.lower() == 'increasing':
                                    trend_color = "#4CAF50"
                                    trend_icon = "📈"
                                    trend_value_num = 75
                                elif trend_value.lower() == 'decreasing':
                                    trend_color = "#f44336"
                                    trend_icon = "📉"
                                    trend_value_num = 25
                                else:
                                    trend_color = "#FFC107"
                                    trend_icon = "📊"
                                    trend_value_num = 50
                                
                                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                                st.metric("Market Trend", f"{trend_icon} {trend_value}")
                                
                                # Trend gauge
                                fig = go.Figure(go.Indicator(
                                    mode = "gauge",
                                    value = trend_value_num,
                                    domain = {'x': [0, 1], 'y': [0, 1]},
                                    title = {'text': "Direction"},
                                    gauge = {
                                        'axis': {'range': [None, 100]},
                                        'bar': {'color': trend_color},
                                        'steps': [
                                            {'range': [0, 33], 'color': "#ffebee"},
                                            {'range': [33, 66], 'color': "#fff3e0"},
                                            {'range': [66, 100], 'color': "#e8f5e8"}
                                        ]
                                    }
                                ))
                                fig.update_layout(height=100, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', font_color='white')
                                st.plotly_chart(fig, use_container_width=True)
                                st.markdown("</div>", unsafe_allow_html=True)
                        
                        with trend_col2:
                            avg_days = market_trends.get('avg_days_on_market')
                            if avg_days:
                                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                                st.metric("Avg Days on Market", avg_days)
                                
                                # Days on market bar
                                fig = go.Figure(go.Bar(
                                    x=['Days'],
                                    y=[avg_days],
                                    marker_color='#2196F3'
                                ))
                                fig.update_layout(
                                    height=100,
                                    margin=dict(l=10, r=10, t=10, b=10),
                                    showlegend=False,
                                    yaxis_title="Days",
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(255,255,255,0.1)',
                                    font_color='white'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                st.markdown("</div>", unsafe_allow_html=True)
                        
                        with trend_col3:
                            supply_demand = market_trends.get('supply_demand')
                            if supply_demand:
                                if isinstance(supply_demand, str):
                                    if 'high' in supply_demand.lower():
                                        supply_color = "#4CAF50"
                                        supply_value = 80
                                    elif 'low' in supply_demand.lower():
                                        supply_color = "#f44336"
                                        supply_value = 20
                                    else:
                                        supply_color = "#FFC107"
                                        supply_value = 50
                                    
                                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                                    st.metric("Supply/Demand", supply_demand)
                                    
                                    # Supply/Demand gauge
                                    fig = go.Figure(go.Indicator(
                                        mode = "gauge",
                                        value = supply_value,
                                        domain = {'x': [0, 1], 'y': [0, 1]},
                                        title = {'text': "Level"},
                                        gauge = {
                                            'axis': {'range': [None, 100]},
                                            'bar': {'color': supply_color},
                                            'steps': [
                                                {'range': [0, 33], 'color': "#ffebee"},
                                                {'range': [33, 66], 'color': "#fff3e0"},
                                                {'range': [66, 100], 'color': "#e8f5e8"}
                                            ]
                                        }
                                    ))
                                    fig.update_layout(height=100, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', font_color='white')
                                    st.plotly_chart(fig, use_container_width=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Price history if available
                    price_history = data.get('price_history', [])
                    if price_history:
                        st.markdown("<h4 style='margin-top: 2rem; color: white;'>📊 Price History</h4>", unsafe_allow_html=True)
                        
                        # Convert price history to DataFrame for plotting
                        history_data = []
                        if isinstance(price_history, list):
                            for entry in price_history:
                                if isinstance(entry, dict):
                                    date = entry.get('date', 'Unknown')
                                    hist_price = get_numeric_value(entry.get('price', 0))
                                    if hist_price:
                                        history_data.append({'Date': date, 'Price': hist_price})
                            if history_data:
                                df_history = pd.DataFrame(history_data)
                                fig = px.line(df_history, x='Date', y='Price', title='Price History')
                                fig.update_layout(
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(255,255,255,0.1)',
                                    font_color='white'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.info("ℹ️ No price estimation data available for this VIN. This could be due to limited market data or the vehicle being too new/rare.")
            
            with vin_tab3:
                st.markdown("<h3 class='section-header'>🔍 Raw VIN Data</h3>", unsafe_allow_html=True)
                
                # Remove error from display if present
                display_data = {k: v for k, v in data.items() if k != "error"}
                
                # Format JSON for better readability
                st.json(display_data)
                
                # Download button for VIN report
                st.download_button(
                    label="📥 Download VIN Report",
                    data=json.dumps(display_data, indent=2),
                    file_name=f"vin_report_{vin_input}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    else:
        # Welcome message for VIN report page
        st.markdown("""
        <div style='text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;'>
            <h3 style='color: white;'>🔍 Enter a VIN to get started</h3>
            <p style='color: rgba(255,255,255,0.9);'>
                Enter a 17-character VIN above to decode and view detailed vehicle information<br>
                The report will include:
            </p>
            <div style='display: flex; justify-content: center; gap: 2rem; margin-top: 1rem;'>
                <div>🚗 Vehicle Details</div>
                <div>💰 Price Dashboard</div>
                <div>📊 Market Analysis</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:  # AI Assistant Page
    st.markdown("## 🤖 AI Contract Assistant")
    
    st.markdown("""
    <div style='background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; color: white;'>
        <h4 style='margin:0; color: white;'>💬 Chat with your contract</h4>
        <p style='margin:0; color: rgba(255,255,255,0.8);'>Ask questions about the uploaded contract. The AI will help you understand terms and answer specific questions.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if contract is uploaded
    if not st.session_state.analysis_result:
        st.warning("⚠️ No contract has been analyzed yet. Please go to the Contract page and upload a document first.")
        
        if st.button("📄 Go to Contract Analysis", use_container_width=True):
            st.session_state.current_page = "Contract Analysis"
            st.rerun()
    else:
        # Display contract info in a compact way
        data = st.session_state.analysis_result
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.info(f"📋 **VIN:** {data.get('vin', 'N/A')}")
                st.markdown("</div>", unsafe_allow_html=True)
            with col2:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                risk = data.get("risk_report", {})
                if risk and risk.get("contract_fairness_score"):
                    score = risk.get("contract_fairness_score")
                    if score >= 80:
                        st.success(f"📊 **Score:** {score}/100")
                    elif score >= 60:
                        st.warning(f"📊 **Score:** {score}/100")
                    else:
                        st.error(f"📊 **Score:** {score}/100")
                st.markdown("</div>", unsafe_allow_html=True)
            with col3:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                # Count total risks
                risk = data.get("risk_report", {})
                total_risks = count_risks_by_level(risk)
                if total_risks > 0:
                    st.error(f"🚩 **Risks:** {total_risks} found")
                else:
                    st.success(f"✅ **Risks:** None")
                st.markdown("</div>", unsafe_allow_html=True)
        
        st.divider()
        
        # Chat interface
        st.markdown("### 💭 Chat")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for chat in st.session_state.chat_history:
                if chat["role"] == "user":
                    with st.chat_message("user"):
                        st.write(chat["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(chat["content"])
        
        # Chat input
        user_question = st.chat_input("Ask something about the contract...")
        
        if user_question:
            # Show user message
            with st.chat_message("user"):
                st.write(user_question)
            
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_question
            })
            
            with st.spinner("🤔 Thinking..."):
                try:
                    payload = {
                        "question": user_question
                    }
                    
                    response = requests.post(
                        f"{BACKEND_URL}/chat",
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        answer = response.json().get("answer", "No response")
                    else:
                        answer = "I'm having trouble connecting to the AI service. Please try again."
                        
                except Exception as e:
                    answer = f"I encountered an error: {str(e)}"
            
            # Show AI response
            with st.chat_message("assistant"):
                st.write(answer)
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })
            
            # Rerun to update chat display
            st.rerun()
        
        # Clear chat button
        if st.session_state.chat_history:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🗑️ Clear Chat History", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()