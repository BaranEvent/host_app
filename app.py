import streamlit as st
import json
import uuid
import random
from typing import List, Dict, Any
from pyairtable import Api
from datetime import datetime, timedelta
import urllib.parse

# Page configuration
st.set_page_config(
    page_title="Event Management Dashboard",
    page_icon="🎉",
    layout="wide"
)

# Initialize session state
if 'event_data' not in st.session_state:
    st.session_state.event_data = {}

# Airtable configuration
AIRTABLE_CONFIG = {
    "base_id": "applJyRTlJLvUEDJs",
    "api_key": "patJHZQyID8nmSaxh.1bcf08f100bd723fd85d67eff8534a19f951b75883d0e0ae4cc49743a9fb3131"
}

def get_airtable_api():
    """Get Airtable API instance"""
    return Api(AIRTABLE_CONFIG["api_key"])

def get_airtable_table(table_name):
    """Get Airtable table instance"""
    api = get_airtable_api()
    return api.table(AIRTABLE_CONFIG["base_id"], table_name)

def get_host_events(host_id):
    """Get all events for a specific host"""
    try:
        table = get_airtable_table("events")
        records = table.all(formula=f"{{host_id}} = {host_id}")
        
        events = []
        for record in records:
            fields = record.get('fields', {})
            events.append({
                'id': record['id'],
                'name': fields.get('name', ''),
                'description': fields.get('description', ''),
                'type': fields.get('type', ''),
                'host_id': fields.get('host_id', ''),
                'location_name': fields.get('location_name', ''),
                'detailed_address': fields.get('detailed_address', ''),
                'start_date': fields.get('start_date', ''),
                'end_date': fields.get('end_date', ''),
                'capacity': fields.get('capacity', 0),
                'is_visible': fields.get('is_visible', False),
                'ID': fields.get('ID', '')
            })
        
        return events
    except Exception as e:
        st.error(f"Etkinlikler yüklenirken hata oluştu: {e}")
        return []

def categorize_events(events):
    """Categorize events into current, upcoming, and past"""
    current_timestamp = datetime.now()
    
    current_events = []
    upcoming_events = []
    past_events = []
    
    for event in events:
        try:
            start_date = datetime.fromisoformat(event['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(event['end_date'].replace('Z', '+00:00'))
            
            if start_date <= current_timestamp <= end_date:
                current_events.append(event)
            elif start_date > current_timestamp:
                upcoming_events.append(event)
            elif end_date < current_timestamp:
                past_events.append(event)
        except Exception as e:
            st.warning(f"Tarih ayrıştırma hatası: {e}")
    
    # Sort by end_date descending
    current_events.sort(key=lambda x: x['end_date'], reverse=True)
    upcoming_events.sort(key=lambda x: x['end_date'], reverse=True)
    past_events.sort(key=lambda x: x['end_date'], reverse=True)
    
    return current_events, upcoming_events, past_events

def render_event_card(event, event_type):
    """Render an event card"""
    with st.container():
        st.markdown("---")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {event['name']}")
            st.markdown(f"**Tür:** {event['type']}")
            st.markdown(f"**Mekan:** {event['location_name']}")
            st.markdown(f"**Kapasite:** {event['capacity']} kişi")
            
            try:
                start_date = datetime.fromisoformat(event['start_date'].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(event['end_date'].replace('Z', '+00:00'))
                st.markdown(f"**Başlangıç:** {start_date.strftime('%d/%m/%Y %H:%M')}")
                st.markdown(f"**Bitiş:** {end_date.strftime('%d/%m/%Y %H:%M')}")
            except:
                st.markdown(f"**Başlangıç:** {event['start_date']}")
                st.markdown(f"**Bitiş:** {event['end_date']}")
            
            st.markdown(f"**Adres:** {event['detailed_address']}")
            
            if event['is_visible']:
                st.success("✅ Uygulamada görünür")
            else:
                st.warning("⚠️ Uygulamada gizli")
        
        with col2:
            st.markdown(f"**Event ID:** {event['ID']}")
            st.markdown(f"**Host ID:** {event['host_id']}")
            
            # Action buttons
            if st.button("⚙️ Özellikler", key=f"features_{event['id']}"):
                # Store event_id in session state and navigate to feature management
                st.session_state.event_id = event['ID']
                st.switch_page("pages/feature_management.py")

def clear_session_state():
    """Clear session state when returning to main page"""
    keys_to_clear = ['event_id', 'feature_key', 'questions', 'question_counter', 'show_preview', 'selected_features', 'event_created', 'redirect_to_form']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    # Note: We don't clear 'host_id' as it should persist from the main page

def main():
    st.title("🎉 Event Management Dashboard")
    st.markdown("Etkinliklerinizi yönetin ve yeni etkinlikler oluşturun.")
    
    # Clear session state when returning to main page
    clear_session_state()
    
    # Host ID input (in a real app, this would come from authentication)
    # Store host_id in session state to persist across reruns
    if 'current_host_id' not in st.session_state:
        st.session_state.current_host_id = 1000
    
    host_id = st.sidebar.number_input(
        "Host ID",
        min_value=1000,
        max_value=9999,
        value=st.session_state.current_host_id,
        help="Etkinliklerinizi görüntülemek için Host ID'nizi girin",
        key="host_id_input"
    )
    
    # Update session state with current host_id
    st.session_state.current_host_id = host_id
    
    # Create Event Section
    st.header("🚀 Yeni Etkinlik Oluştur")
    
    if st.button("➕ Etkinlik Oluştur", type="primary", use_container_width=True):
        # Store the current host_id in session state for event creation
        st.session_state.host_id = host_id
        # Navigate to event creation page
        st.switch_page("pages/event_creation.py")
    
    st.markdown("---")
    
    # Load events for the host
    events = get_host_events(host_id)
    
    if not events:
        st.info("Bu Host ID için henüz etkinlik bulunmuyor. Yeni bir etkinlik oluşturun!")
        return
    
    # Categorize events
    current_events, upcoming_events, past_events = categorize_events(events)
    
    # Current Events Section
    st.header("🎯 Güncel Etkinlikler")
    if current_events:
        for event in current_events:
            render_event_card(event, "current")
    else:
        st.info("Şu anda aktif etkinlik bulunmuyor.")
    
    # Upcoming Events Section
    st.header("📅 Yaklaşan Etkinlikler")
    if upcoming_events:
        for event in upcoming_events:
            render_event_card(event, "upcoming")
    else:
        st.info("Yaklaşan etkinlik bulunmuyor.")
    
    # Past Events Section
    st.header("📚 Geçmiş Etkinlikler")
    if past_events:
        for event in past_events:
            render_event_card(event, "past")
    else:
        st.info("Geçmiş etkinlik bulunmuyor.")
    
    # Summary
    st.markdown("---")
    st.header("📊 Özet")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Güncel Etkinlikler", len(current_events))
    
    with col2:
        st.metric("Yaklaşan Etkinlikler", len(upcoming_events))
    
    with col3:
        st.metric("Geçmiş Etkinlikler", len(past_events))
    
    # Refresh button
    st.markdown("---")
    
    if st.button("🔄 Sayfayı Yenile", type="secondary", use_container_width=True):
        st.rerun()

if __name__ == "__main__":
    main() 