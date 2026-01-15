"""
Trend Hunter Dashboard (Milestone 6)
Streamlit web application for visualizing trending keywords
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db_utils import get_db


# Page configuration
st.set_page_config(
    page_title="Trend Hunter Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_flags(label_filter=None, min_score=0, max_results=50):
    """Load flags from database with filters"""
    db = get_db()
    
    query = '''
        SELECT 
            f.id,
            f.term_id,
            k.canonical_term,
            f.trend_score,
            f.label,
            f.confidence,
            f.reason_codes,
            f.date_time,
            k.first_seen
        FROM flags f
        JOIN keywords k ON f.term_id = k.id
        WHERE f.trend_score >= ?
    '''
    
    params = [min_score]
    
    if label_filter and label_filter != "All":
        query += ' AND f.label = ?'
        params.append(label_filter)
    
    query += ' ORDER BY f.trend_score DESC LIMIT ?'
    params.append(max_results)
    
    df = db.query_to_df(query, params=params)
    
    if not df.empty:
        df['date_time'] = pd.to_datetime(df['date_time'])
        df['first_seen'] = pd.to_datetime(df['first_seen'])
    
    return df


def load_time_series(term_id):
    """Load time series data for a keyword"""
    db = get_db()
    
    query = '''
        SELECT 
            date_time,
            iot_value,
            mentions_total
        FROM time_series_metrics
        WHERE term_id = ?
        ORDER BY date_time ASC
    '''
    
    df = db.query_to_df(query, params=[term_id])
    
    if not df.empty:
        df['date_time'] = pd.to_datetime(df['date_time'])
    
    return df


def load_features(term_id):
    """Load feature data for a keyword"""
    db = get_db()
    
    query = '''
        SELECT 
            slope,
            acceleration,
            ma3,
            ma7,
            pct_change_24h,
            novelty_score,
            velocity,
            volatility,
            date_time
        FROM features
        WHERE term_id = ?
        ORDER BY date_time DESC
        LIMIT 1
    '''
    
    result = db.execute_query(query, params=[term_id])
    
    if result:
        row = result[0]
        return {
            'slope': row['slope'],
            'acceleration': row['acceleration'],
            'ma3': row['ma3'],
            'ma7': row['ma7'],
            'pct_change_24h': row['pct_change_24h'],
            'novelty_score': row['novelty_score'],
            'velocity': row['velocity'],
            'volatility': row['volatility'],
            'date_time': row['date_time']
        }
    
    return None


def plot_iot_chart(df_ts, term):
    """Create IOT time series chart"""
    if df_ts.empty:
        st.info("No time series data available")
        return
    
    fig = go.Figure()
    
    # IOT line
    fig.add_trace(go.Scatter(
        x=df_ts['date_time'],
        y=df_ts['iot_value'],
        mode='lines+markers',
        name='IOT Value',
        line=dict(color='#FF4B4B', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f"Google Trends IOT: {term}",
        xaxis_title="Date",
        yaxis_title="IOT Value (0-100)",
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_mentions_chart(df_ts, term):
    """Create mentions bar chart"""
    if df_ts.empty or 'mentions_total' not in df_ts.columns:
        st.info("No mentions data available")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_ts['date_time'],
        y=df_ts['mentions_total'],
        name='Mentions',
        marker=dict(color='#0068C9')
    ))
    
    fig.update_layout(
        title=f"Social Media Mentions: {term}",
        xaxis_title="Date",
        yaxis_title="Mention Count",
        hovermode='x unified',
        height=300,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_features_table(features):
    """Display features as a formatted table"""
    if not features:
        st.info("No feature data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Slope", f"{features['slope']:.3f}")
        st.metric("Acceleration", f"{features['acceleration']:.3f}")
        st.metric("MA3", f"{features['ma3']:.1f}")
        st.metric("MA7", f"{features['ma7']:.1f}")
    
    with col2:
        st.metric("% Change 24h", f"{features['pct_change_24h']:.1f}%")
        st.metric("Velocity", f"{features['velocity']:.3f}")
        st.metric("Volatility", f"{features['volatility']:.3f}")
        st.metric("Novelty Score", f"{features['novelty_score']:.1f}")


def get_label_color(label):
    """Get color for label badge"""
    colors = {
        'Breakout': '#FF4B4B',
        'Hidden Gem': '#FFA500',
        'Rising': '#00CC00',
        'Stable': '#0068C9',
        'Dying': '#999999'
    }
    return colors.get(label, '#666666')


def main():
    """Main dashboard application"""
    
    # Header
    st.title("🔥 Trend Hunter Dashboard")
    st.markdown("**Real-time trend detection and analysis**")
    st.markdown("---")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    label_filter = st.sidebar.selectbox(
        "Label",
        ["All", "Breakout", "Hidden Gem", "Rising", "Stable", "Dying"]
    )
    
    min_score = st.sidebar.slider(
        "Minimum Score",
        min_value=0,
        max_value=100,
        value=0,
        step=5
    )
    
    max_results = st.sidebar.number_input(
        "Max Results",
        min_value=10,
        max_value=200,
        value=50,
        step=10
    )
    
    refresh = st.sidebar.button("🔄 Refresh Data")
    
    # Load data
    df_flags = load_flags(label_filter, min_score, max_results)
    
    # Summary metrics
    st.header("📊 Summary")
    
    if not df_flags.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Flags", len(df_flags))
        
        with col2:
            avg_score = df_flags['trend_score'].mean()
            st.metric("Avg Score", f"{avg_score:.1f}")
        
        with col3:
            high_conf = len(df_flags[df_flags['confidence'] >= 0.7])
            st.metric("High Confidence", high_conf)
        
        with col4:
            breakouts = len(df_flags[df_flags['label'] == 'Breakout'])
            st.metric("Breakout Trends", breakouts)
    else:
        st.info("No flags found. Try adjusting filters.")
        return
    
    st.markdown("---")
    
    # Top Flags Table
    st.header("🎯 Top Trending Keywords")
    
    # Format dataframe for display
    df_display = df_flags.copy()
    df_display['trend_score'] = df_display['trend_score'].round(1)
    df_display['confidence'] = (df_display['confidence'] * 100).round(1).astype(str) + '%'
    df_display['date_time'] = df_display['date_time'].dt.strftime('%Y-%m-%d %H:%M')
    
    # Color-code labels
    def highlight_label(row):
        color = get_label_color(row['label'])
        return [f'background-color: {color}30' if i == df_display.columns.get_loc('label') else '' 
                for i in range(len(row))]
    
    st.dataframe(
        df_display[['canonical_term', 'trend_score', 'label', 'confidence', 'reason_codes', 'date_time']],
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Detail View
    st.header("🔍 Detailed Analysis")
    
    if not df_flags.empty:
        # Select keyword
        selected_term = st.selectbox(
            "Select a keyword to analyze:",
            df_flags['canonical_term'].tolist(),
            key='term_select'
        )
        
        if selected_term:
            # Get term_id
            term_row = df_flags[df_flags['canonical_term'] == selected_term].iloc[0]
            term_id = term_row['term_id']
            
            # Display flag info
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Trend Score", f"{term_row['trend_score']:.1f}")
            
            with col2:
                label_color = get_label_color(term_row['label'])
                st.markdown(f"**Label:** <span style='color:{label_color};font-size:20px;font-weight:bold'>{term_row['label']}</span>", unsafe_allow_html=True)
            
            with col3:
                st.metric("Confidence", f"{term_row['confidence']:.0%}")
            
            st.markdown(f"**Reason Codes:** {term_row['reason_codes']}")
            st.markdown(f"**Flagged:** {term_row['date_time'].strftime('%Y-%m-%d %H:%M')}")
            
            st.markdown("---")
            
            # Charts
            col_left, col_right = st.columns([2, 1])
            
            with col_left:
                # IOT Chart
                df_ts = load_time_series(term_id)
                plot_iot_chart(df_ts, selected_term)
                
                # Mentions Chart
                plot_mentions_chart(df_ts, selected_term)
            
            with col_right:
                # Features
                st.subheader("📈 Features")
                features = load_features(term_id)
                display_features_table(features)
    
    # Footer
    st.markdown("---")
    st.markdown("**Trend Hunter** | Built with Streamlit | Data updates every hour")


if __name__ == "__main__":
    main()
