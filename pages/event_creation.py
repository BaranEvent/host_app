import streamlit as st
import json
import uuid
from typing import List, Dict, Any
from pyairtable import Api
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Event Creation",
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

def get_record_by_host_id(host_id):
    """Get record by host_id to retrieve the ID column value"""
    try:
        table = get_airtable_table("events")
        # Search for records with the specific host_id
        # Try different formula syntax
        try:
            records = table.all(formula=f"{{host_id}} = '{host_id}'")
        except:
            # Fallback: get all records and filter
            records = table.all()
            records = [r for r in records if r.get('fields', {}).get('host_id') == host_id]
        
        if records and len(records) > 0:
            # Get the most recent record (last created)
            latest_record = records[-1]
            fields = latest_record.get('fields', {})
            
            # Look for ID column in fields
            if 'ID' in fields:
                return fields['ID']
            elif 'id' in fields:
                return fields['id']
            elif 'Id' in fields:
                return fields['Id']
            else:
                return None
        
        return None
    except Exception as e:
        st.error(f"ID Column Value alınırken hata oluştu: {e}")
        return None



def save_event(event_data):
    """Save event data to Airtable"""
    try:
        table = get_airtable_table("events")  # Assuming you have an events table
        
        record_data = {
            "name": event_data['name'],
            "description": event_data['description'],
            "type": event_data['type'],
            "host_id": event_data['host_id'],
            "location_name": event_data['location_name'],
            "detailed_address": event_data['detailed_address'],
            "start_date": event_data['start_date'].isoformat(),
            "end_date": event_data['end_date'].isoformat(),
            "capacity": event_data['capacity'],
            "is_visible": event_data['is_visible']
        }
        
        # Create the record
        response = table.create(record_data)
        
        if response:
            st.success("✅ Etkinlik başarıyla kaydedildi!")
            
            # Handle different response structures
            record_id = None
            
            # If response is a dict, it might contain the record directly
            if isinstance(response, dict):
                # Check if it has a 'fields' field with ID column
                if 'fields' in response:
                    fields = response['fields']
                    # Look for ID column in fields
                    if 'ID' in fields:
                        record_id = fields['ID']
                        st.success(f"📋 ID Column Value (from response): {record_id}")
                        return record_id
                    elif 'id' in fields:
                        record_id = fields['id']
                        st.success(f"📋 ID Column Value (from response): {record_id}")
                        return record_id
                    elif 'Id' in fields:
                        record_id = fields['Id']
                        st.success(f"📋 ID Column Value (from response): {record_id}")
                        return record_id
                # Check if it has a 'records' field
                elif 'records' in response and len(response['records']) > 0:
                    record = response['records'][0]
                    if isinstance(record, dict) and 'fields' in record:
                        fields = record['fields']
                        if 'ID' in fields:
                            record_id = fields['ID']
                            st.success(f"📋 ID Column Value (from response): {record_id}")
                            return record_id
                        elif 'id' in fields:
                            record_id = fields['id']
                            st.success(f"📋 ID Column Value (from response): {record_id}")
                            return record_id
                        elif 'Id' in fields:
                            record_id = fields['Id']
                            st.success(f"📋 ID Column Value (from response): {record_id}")
                            return record_id
            
            # If response is a list
            elif isinstance(response, list) and len(response) > 0:
                record = response[0]
                if isinstance(record, dict) and 'fields' in record:
                    fields = record['fields']
                    if 'ID' in fields:
                        record_id = fields['ID']
                        st.success(f"📋 ID Column Value (from response): {record_id}")
                        return record_id
                    elif 'id' in fields:
                        record_id = fields['id']
                        st.success(f"📋 ID Column Value (from response): {record_id}")
                        return record_id
                    elif 'Id' in fields:
                        record_id = fields['Id']
                        st.success(f"📋 ID Column Value (from response): {record_id}")
                        return record_id
            
            # If we can't get ID from response, try to read it from the database
            if not record_id:
                st.info("🔄 Record ID alınıyor...")
                try:
                    record_id = get_record_by_host_id(event_data['host_id'])
                    
                    if record_id:
                        st.success(f"📋 ID Column Value (from database): {record_id}")
                        return record_id
                    else:
                        st.error("❌ ID Column Value alınamadı")
                        return None
                except Exception as e:
                    st.error(f"❌ Record ID alınırken hata: {e}")
                    return None
        
        st.error("❌ Kayıt oluşturulamadı")
        return None
        
    except Exception as e:
        st.error(f"❌ Etkinlik kaydedilirken hata oluştu: {e}")
        st.error(f"❌ Hata detayı: {type(e).__name__}")
        return None

def validate_event_data(event_data):
    """Validate event data"""
    errors = []
    
    if not event_data.get('name'):
        errors.append("Etkinlik adı zorunludur")
    
    if not event_data.get('description'):
        errors.append("Etkinlik açıklaması zorunludur")
    
    if not event_data.get('type'):
        errors.append("Etkinlik türü zorunludur")
    
    if not event_data.get('location_name'):
        errors.append("Mekan adı zorunludur")
    
    if not event_data.get('detailed_address'):
        errors.append("Detaylı adres zorunludur")
    
    if not event_data.get('start_date'):
        errors.append("Başlangıç tarihi zorunludur")
    
    if not event_data.get('end_date'):
        errors.append("Bitiş tarihi zorunludur")
    
    if event_data.get('start_date') and event_data.get('end_date'):
        if event_data['start_date'] >= event_data['end_date']:
            errors.append("Bitiş tarihi başlangıç tarihinden sonra olmalıdır")
    
    if not event_data.get('capacity') or event_data['capacity'] <= 0:
        errors.append("Beklenen Katılım Miktarı 0'dan büyük olmalıdır")
    
    if 'is_visible' not in event_data:
        errors.append("Uygulama içerisinde etkinliğinizin gözükmesini ister misiniz seçeneği zorunludur")
    
    return errors

def main():
    st.title("🎉 Etkinlik Kayıt Formu")
    st.markdown("Etkinliğinizi kaydetmek için aşağıdaki formu doldurun.")
    
    # Back to home button
    if st.sidebar.button("🏠 Ana Sayfaya Dön"):
        st.switch_page("app.py")
    
    # Check if we have a successful event creation
    if 'event_created' in st.session_state and st.session_state.event_created:
        st.success("✅ Etkinlik başarıyla kaydedildi!")
        st.info(f"📋 Record ID: {st.session_state.event_id}")
        
        st.markdown("---")
        st.markdown("### 🔗 Yönlendirme")
        st.markdown("**Özellik Yönetimi sayfasına yönlendiriliyorsunuz...**")
        
        # Create navigation buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⚙️ Özellik Yönetimi Sayfasına Git", type="primary", use_container_width=True, key="nav_to_features"):
                st.switch_page("pages/feature_management.py")
        
        with col2:
            if st.button("🏠 Ana Sayfaya Dön", type="secondary", use_container_width=True, key="nav_to_home_success"):
                # Clear success state
                del st.session_state.event_created
                st.switch_page("app.py")
        
        st.info("💡 Yukarıdaki butonlardan birini seçerek devam edebilirsiniz.")
        return
    
    # Get host_id from session state (passed from main page)
    host_id = st.session_state.get('host_id', None)
    
    if host_id is None:
        st.error("Host ID bulunamadı. Lütfen ana sayfadan tekrar başlayın.")
        if st.button("🏠 Ana Sayfaya Dön", key="nav_to_home_error"):
            st.switch_page("app.py")
        return
    
    st.info(f"**Host ID:** {host_id} (Ana sayfadan alındı)")
    
    # Form sections
    with st.container():
        st.header("📝 Etkinlik Bilgileri")
        
        # Event name and description
        col1, col2 = st.columns(2)
        
        with col1:
            event_name = st.text_input(
                "Etkinlik Adı *",
                placeholder="Örn: Teknoloji Konferansı 2024",
                help="Etkinliğinizin adını girin"
            )
        
        with col2:
            event_type = st.selectbox(
                "Etkinlik Türü *",
                options=[
                    "",
                    "Konferans, Zirve & Seminer",
                    "Kongre, Fuar & Sergi",
                    "Kurumsal & İş Etkinlikleri",
                    "Atölye, Eğitim & Networking",
                    "Teknoloji Etkinlikleri & Hackathon",
                    "Festival, Panayır & Kutlama",
                    "Konser, Müzik & Sahne Sanatları",
                    "Spor, Espor & Yarışmalar",
                    "Sağlık, Wellness & Hayır Etkinlikleri",
                    "Yiyecek, İçecek & Gastronomi",
                    "Gece Hayatı & Parti",
                    "Seyahat, Tur & Gezi",
                    "Aile, Çocuk & Topluluk Etkinlikleri",
                    "Sanal & Hibrit Etkinlikler"
                ],
                help="Etkinliğinizin türünü seçin"
            )
        
        # Capacity field in a new row
        capacity = st.number_input(
            "Beklenen Katılım Miktarı *",
            min_value=1,
            value=50,
            help="Etkinliğinizin beklenen katılımcı sayısı"
        )
        
        # Description
        description = st.text_area(
            "Etkinlik Açıklaması *",
            placeholder="Etkinliğiniz hakkında detaylı bilgi verin...",
            height=100,
            help="Etkinliğinizin detaylı açıklamasını girin"
        )
        
        st.markdown("---")
        
        # Location information
        st.header("📍 Mekan Bilgileri")
        
        col3, col4 = st.columns(2)
        
        with col3:
            location_name = st.text_input(
                "Mekan Adı *",
                placeholder="Örn: İstanbul Kongre Merkezi",
                help="Etkinliğinizin gerçekleşeceği mekanın adı"
            )
        
        with col4:
            detailed_address = st.text_input(
                "Detaylı Adres *",
                placeholder="Örn: Harbiye Mah. Darülbedai Cad. No:3 Şişli/İstanbul",
                help="Etkinliğinizin tam adresi"
            )
        
        st.markdown("---")
        
        # Date and time information
        st.header("📅 Tarih ve Saat Bilgileri")
        
        col5, col6 = st.columns(2)
        
        with col5:
            start_date = st.date_input(
                "Başlangıç Tarihi *",
                value=datetime.now().date(),
                help="Etkinliğinizin başlangıç tarihi"
            )
            
            start_time = st.time_input(
                "Başlangıç Saati *",
                value=datetime.now().time(),
                help="Etkinliğinizin başlangıç saati"
            )
        
        with col6:
            end_date = st.date_input(
                "Bitiş Tarihi *",
                value=(datetime.now() + timedelta(days=1)).date(),
                help="Etkinliğinizin bitiş tarihi"
            )
            
            end_time = st.time_input(
                "Bitiş Saati *",
                value=(datetime.now() + timedelta(hours=2)).time(),
                help="Etkinliğinizin bitiş saati"
            )
        
        # Combine date and time
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)
        
        st.markdown("---")
        
        # Host information
        st.header("👤 Host Bilgileri")
        
        st.info(f"**Host ID:** {host_id} (Ana sayfadan alındı)")
        
        # Visibility checkbox with enhanced styling
        st.markdown("---")
        st.markdown("### 🌟 **Etkinlik Görünürlüğü**")
        
        col_visibility1, col_visibility2 = st.columns([1, 3])
        
        with col_visibility1:
            is_visible = st.checkbox(
                "**Uygulamada Görünür** *",
                value=True,
                help="Bu seçenek işaretlenirse etkinliğiniz uygulama içerisinde görünür olacaktır"
            )
        
        with col_visibility2:
            if is_visible:
                st.success("✅ Etkinliğiniz uygulamada görünür olacak")
            else:
                st.warning("⚠️ Etkinliğiniz uygulamada gizli olacak")
        
        # Preview section
        st.markdown("---")
        st.header("👁️ Önizleme")
        
        if event_name and description and event_type and location_name and detailed_address:
            st.markdown("**Etkinlik Özeti:**")
            
            col_preview1, col_preview2 = st.columns(2)
            
            with col_preview1:
                st.markdown(f"**Etkinlik Adı:** {event_name}")
                st.markdown(f"**Etkinlik Türü:** {event_type}")
                st.markdown(f"**Mekan:** {location_name}")
                st.markdown(f"**Beklenen Katılım Miktarı:** {capacity} kişi")
                st.markdown(f"**Host ID:** {host_id}")
                st.markdown(f"**Uygulamada Görünür:** {'Evet' if is_visible else 'Hayır'}")
            
            with col_preview2:
                st.markdown(f"**Başlangıç:** {start_datetime.strftime('%d/%m/%Y %H:%M')}")
                st.markdown(f"**Bitiş:** {end_datetime.strftime('%d/%m/%Y %H:%M')}")
                st.markdown(f"**Adres:** {detailed_address}")
        
        # Submit button
        st.markdown("---")
        
        if st.button("🚀 Etkinliği Kaydet", type="primary", use_container_width=True):
            # Prepare event data
            event_data = {
                'name': event_name,
                'description': description,
                'type': event_type,
                'host_id': host_id,
                'location_name': location_name,
                'detailed_address': detailed_address,
                'start_date': start_datetime,
                'end_date': end_datetime,
                'capacity': capacity,
                'is_visible': is_visible
            }
            
            # Validate data
            errors = validate_event_data(event_data)
            
            if errors:
                st.error("Lütfen aşağıdaki hataları düzeltin:")
                for error in errors:
                    st.error(f"• {error}")
            else:
                record_id = save_event(event_data)
                if record_id:
                    # Clear form and session state
                    st.session_state.event_data = {}
                    
                    # Store the event_id in session state for feature management
                    st.session_state.event_id = record_id
                    
                    # Mark event as created successfully
                    st.session_state.event_created = True
                    
                    # Rerun to show success page
                    st.rerun()

if __name__ == "__main__":
    main() 