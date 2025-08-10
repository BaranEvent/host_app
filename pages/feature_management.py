import streamlit as st
import json
import uuid
from typing import List, Dict, Any
from pyairtable import Api
from datetime import datetime
import urllib.parse

# Page configuration
st.set_page_config(
    page_title="Event Features Management",
    page_icon="⚙️",
    layout="wide"
)

# Initialize session state
if 'selected_features' not in st.session_state:
    st.session_state.selected_features = {}
if 'event_id' not in st.session_state:
    st.session_state.event_id = None
if 'redirect_url' not in st.session_state:
    st.session_state.redirect_url = None

# Airtable configuration
AIRTABLE_CONFIG = {
    "base_id": "applJyRTlJLvUEDJs",
    "api_key": "patJHZQyID8nmSaxh.1bcf08f100bd723fd85d67eff8534a19f951b75883d0e0ae4cc49743a9fb3131"
}

# Feature definitions
FEATURES = {
    "registration_form": {
        "name": "Kayıt Formu",
        "description": "Etkinliğiniz için özelleştirilebilir kayıt formu oluşturun. Katılımcıların bilgilerini toplayın ve yönetin.",
        "category": "before_event",
        # Explicit mapping to Airtable's feature_id for clarity
        "feature_id": 1
    }
    # Future features can be added here:
    # "live_polling": {
    #     "name": "Canlı Anket",
    #     "description": "Etkinlik sırasında katılımcılarla canlı anket yapın.",
    #     "category": "during_event",
    #     "feature_id": 2
    # },
    # "feedback_survey": {
    #     "name": "Geri Bildirim Anketi",
    #     "description": "Etkinlik sonrası katılımcılardan geri bildirim toplayın.",
    #     "category": "after_event",
    #     "feature_id": 3
    # }
}

def get_airtable_api():
    """Get Airtable API instance"""
    return Api(AIRTABLE_CONFIG["api_key"])

def get_airtable_table(table_name):
    """Get Airtable table instance"""
    api = get_airtable_api()
    return api.table(AIRTABLE_CONFIG["base_id"], table_name)

# --- NEW HELPERS for (event_id, feature_id=1) flow ---

def get_event_feature_record(event_id: Any, feature_id: int):
    """
    Fetch a single record from 'event_features' for given event_id and feature_id.
    Returns dict {'record': {...}, 'is_active': bool} if found, else None.
    """
    try:
        table = get_airtable_table("event_features")
        # Airtable formula: assume event_id stored as text; quote it.
        # If your event_id field in Airtable is numeric, Airtable will still match string-literal to number.
        formula = f"AND({{event_id}}='{str(event_id)}', {{feature_id}}={feature_id})"
        records = table.all(formula=formula, max_records=1)
        if records:
            rec = records[0]
            is_active = bool(rec['fields'].get('is_active', False))
            return {"record": rec, "is_active": is_active}
        return None
    except Exception as e:
        st.error(f"Özellik durumu alınırken hata oluştu: {str(e)}")
        return None

def update_event_feature_is_active(record_id: str, is_active: bool) -> bool:
    """Update 'is_active' on the given record_id in Airtable. Returns True on success."""
    try:
        table = get_airtable_table("event_features")
        table.update(record_id, {"is_active": is_active})
        return True
    except Exception as e:
        st.error(f"Özellik güncellenirken hata oluştu: {str(e)}")
        return False

def is_feature_active(event_id: Any, feature_id: int) -> bool:
    """Convenience: check if a feature is active for summary section."""
    data = get_event_feature_record(event_id, feature_id)
    return bool(data and data.get("is_active", False))

# --- Existing function kept (used for other parts) ---
def load_event_features(event_id):
    """Load existing features for an event (legacy path; uses feature_key/enabled if present)."""
    try:
        table = get_airtable_table("event_features")
        # Kept as-is for minimal change; quoting event_id for safety
        records = table.all(formula=f"{{event_id}} = '{str(event_id)}'")
        features = {}
        for record in records:
            feature_key = record['fields'].get('feature_key', '')
            if feature_key:
                features[feature_key] = {
                    'id': record['id'],
                    # Backward-compatible; many bases used 'enabled'. We don't rely on this for registration_form.
                    'enabled': record['fields'].get('enabled', False)
                }
        return features
    except Exception as e:
        st.error(f"Özellikler yüklenirken hata oluştu: {str(e)}")
        return {}

def redirect_to_form_builder(event_id, feature_key):
    """Store event_id and feature in session state for form builder"""
    # Store event_id and feature in session state
    st.session_state.event_id = event_id
    st.session_state.feature_key = feature_key
    st.session_state.redirect_to_form = True
    st.rerun()

def render_feature_section(title, features, category, event_id):
    """Render a section of features"""
    st.header(f"📋 {title}")
    
    if not features:
        st.info("Bu kategoride henüz özellik bulunmuyor.")
        return
    
    for feature_key, feature_info in features.items():
        with st.container():
            st.markdown("---")
            
            col1, col2 = st.columns([1, 4])
            
            with col1:
                if st.button(
                    "⚙️ Yapılandır",
                    key=f"config_{feature_key}",
                    help=f"{feature_info['name']} özelliğini yapılandır"
                ):
                    redirect_to_form_builder(event_id, feature_key)
            
            with col2:
                st.markdown(f"**{feature_info['name']}**")
                st.markdown(f"*{feature_info['description']}*")

                # --- SPECIAL HANDLING for 'Kayıt Formu' (feature_id=1) ---
                if feature_key == "registration_form":
                    feature_id = feature_info.get("feature_id", 1)
                    ef = get_event_feature_record(event_id, feature_id)

                    if ef is None:
                        # No record exists -> keep original messaging ("henüz yapılandırılmamış")
                        st.info("ℹ️ Bu özellik henüz yapılandırılmamış")
                    else:
                        # Show toggle UI using a form to require explicit 'Apply'
                        current_active = ef["is_active"]
                        rec_id = ef["record"]["id"]

                        with st.form(key=f"{feature_key}_activation_form"):
                            new_active = st.checkbox(
                                "Bu özelliği etkinleştir",
                                value=current_active,
                                key=f"{feature_key}_active_checkbox"
                            )
                            applied = st.form_submit_button("Uygula")
                            if applied:
                                if update_event_feature_is_active(rec_id, new_active):
                                    # Immediate feedback
                                    if new_active:
                                        st.success("✅ Kayıt Formu etkinleştirildi.")
                                    else:
                                        st.warning("⏹️ Kayıt Formu devre dışı bırakıldı.")
                                    # Rerun to reflect the latest state cleanly
                                    st.rerun()
                        # Status line under the form
                        if current_active:
                            st.success("✅ Bu özellik etkinliğiniz için aktif")
                        else:
                            st.info("ℹ️ Bu özellik şu anda devre dışı")
                else:
                    # Legacy path for other features (if any are added later)
                    existing_features = load_event_features(event_id)
                    if feature_key in existing_features and existing_features[feature_key]['enabled']:
                        st.success("✅ Bu özellik etkinliğiniz için aktif")
                    else:
                        st.info("ℹ️ Bu özellik henüz yapılandırılmamış")

def main():
    st.title("⚙️ Etkinlik Özellikleri Yönetimi")
    st.markdown("Etkinliğiniz için hangi özellikleri yapılandırmak istediğinizi seçin.")
    
    # Back to home button
    if st.sidebar.button("🏠 Ana Sayfaya Dön", key="sidebar_home_features"):
        st.switch_page("app.py")
    
    # Check if we need to redirect to form builder
    if 'redirect_to_form' in st.session_state and st.session_state.redirect_to_form:
        st.success("Form Builder sayfasına yönlendiriliyorsunuz...")
        
        # Create navigation buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 Form Builder'a Git", type="primary", use_container_width=True, key="nav_to_form_builder"):
                # Clear the redirect flag
                del st.session_state.redirect_to_form
                st.switch_page("pages/form_builder.py")
        
        with col2:
            if st.button("❌ İptal", type="secondary", use_container_width=True, key="cancel_redirect"):
                # Clear the redirect flag
                del st.session_state.redirect_to_form
                st.rerun()
        
        st.info("💡 Yukarıdaki butonlardan birini seçerek devam edebilirsiniz.")
        return
    
    # Get event_id from session state or default to 0
    event_id = st.session_state.get('event_id', 0)
    
    if event_id == 0:
        st.warning("⚠️ Event ID belirtilmedi. Varsayılan olarak 0 kullanılıyor.")
    
    st.info(f"**Etkinlik ID:** {event_id}")
    
    # Load existing features (legacy usage)
    existing_features = load_event_features(event_id)
    
    # Update session state with existing features (legacy usage)
    for feature_key, feature_data in existing_features.items():
        st.session_state.selected_features[feature_key] = feature_data['enabled']
    
    st.markdown("---")
    
    # Before Event Features
    before_event_features = {k: v for k, v in FEATURES.items() if v['category'] == 'before_event'}
    render_feature_section("Etkinlik Öncesi Özellikler", before_event_features, "before_event", event_id)
    
    # During Event Features
    during_event_features = {k: v for k, v in FEATURES.items() if v['category'] == 'during_event'}
    render_feature_section("Etkinlik Sırası Özellikler", during_event_features, "during_event", event_id)
    
    # After Event Features
    after_event_features = {k: v for k, v in FEATURES.items() if v['category'] == 'after_event'}
    render_feature_section("Etkinlik Sonrası Özellikler", after_event_features, "after_event", event_id)
    
    # Summary
    st.markdown("---")
    st.header("📊 Özet")
    
    # Legacy summary list, plus explicit check for registration_form is_active
    active_features = [k for k, v in existing_features.items() if v['enabled']]
    # Ensure registration_form reflects the new is_active field if a record exists
    reg = FEATURES.get("registration_form")
    if reg and is_feature_active(event_id, reg.get("feature_id", 1)):
        if "registration_form" not in active_features:
            active_features.append("registration_form")
    
    if active_features:
        st.success(f"**{len(active_features)}** özellik aktif:")
        for feature_key in active_features:
            if feature_key in FEATURES:
                st.markdown(f"• {FEATURES[feature_key]['name']}")
    else:
        st.warning("Henüz hiç özellik aktif edilmedi.")
    
    # Refresh button
    st.markdown("---")
    
    if st.button("🔄 Sayfayı Yenile", type="secondary", use_container_width=True):
        st.rerun()

if __name__ == "__main__":
    main()
