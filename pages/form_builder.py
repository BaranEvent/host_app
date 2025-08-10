import streamlit as st
import json
import uuid
from typing import List, Dict, Any
from pyairtable import Api
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Form Builder Dashboard",
    page_icon="📝",
    layout="wide"
)

# Initialize session state
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'question_counter' not in st.session_state:
    st.session_state.question_counter = 0
if 'show_preview' not in st.session_state:
    st.session_state.show_preview = False
if 'event_id' not in st.session_state:
    st.session_state.event_id = None

# Airtable configuration
AIRTABLE_CONFIG = {
    "base_id": "applJyRTlJLvUEDJs",
    "api_key": "patJHZQyID8nmSaxh.1bcf08f100bd723fd85d67eff8534a19f951b75883d0e0ae4cc49743a9fb3131"
}

# Data type options in Turkish
DATA_TYPES = {
    "Yazı": "text",
    "Sayı": "number", 
    "Virgüllü sayı": "float",
    "Tarih": "date",
    "Saat ve tarih": "datetime",
    "Doğru yanlış": "boolean",
    "Çoktan seçmeli": "single_choice",
    "Çoktan seçmeli çoklu cevap": "multiple_choice"
}

def get_airtable_api():
    """Get Airtable API instance"""
    return Api(AIRTABLE_CONFIG["api_key"])

def get_airtable_table(table_name="registration_form"):
    """Get Airtable table instance"""
    api = get_airtable_api()
    return api.table(AIRTABLE_CONFIG["base_id"], table_name)

def get_event_features_table():
    """Get event_features table instance"""
    api = get_airtable_api()
    return api.table(AIRTABLE_CONFIG["base_id"], "event_features")

def add_question():
    """Add a new question to the form"""
    question_id = f"question_{st.session_state.question_counter}"
    st.session_state.questions.append({
        'id': question_id,
        'question': '',
        'type': 'Yazı',
        'is_required': False,
        'options': [],
        'rank': len(st.session_state.questions)
    })
    st.session_state.question_counter += 1

def remove_question(question_id):
    """Remove a question from the form"""
    st.session_state.questions = [q for q in st.session_state.questions if q['id'] != question_id]
    # Reorder ranks
    for i, question in enumerate(st.session_state.questions):
        question['rank'] = i

def move_question_up(index):
    """Move a question up in the list"""
    if index > 0:
        st.session_state.questions[index], st.session_state.questions[index-1] = \
            st.session_state.questions[index-1], st.session_state.questions[index]
        # Update ranks
        for i, question in enumerate(st.session_state.questions):
            question['rank'] = i

def move_question_down(index):
    """Move a question down in the list"""
    if index < len(st.session_state.questions) - 1:
        st.session_state.questions[index], st.session_state.questions[index+1] = \
            st.session_state.questions[index+1], st.session_state.questions[index]
        # Update ranks
        for i, question in enumerate(st.session_state.questions):
            question['rank'] = i

def add_option(question_id):
    """Add an option to a multiple choice question"""
    for question in st.session_state.questions:
        if question['id'] == question_id:
            question['options'].append('')
            break

def remove_option(question_id, option_index):
    """Remove an option from a multiple choice question"""
    for question in st.session_state.questions:
        if question['id'] == question_id:
            question['options'].pop(option_index)
            break

def save_form():
    """Save the form to Airtable"""
    if not st.session_state.questions:
        st.error("Lütfen en az bir soru ekleyin!")
        return
    
    # Use event_id from session state or default to "0"
    event_id = st.session_state.event_id or "0"
    
    try:
        table = get_airtable_table()
        
        for question in st.session_state.questions:
            # Prepare the record data
            record_data = {
                "event_id": event_id,
                "name": question['question'],
                "type": DATA_TYPES[question['type']],
                "is_required": question['is_required'],
                "rank": question['rank']
            }
            
            # Add possible_answers for multiple choice questions
            if question['type'] in ['Çoktan seçmeli', 'Çoktan seçmeli çoklu cevap']:
                record_data["possible_answers"] = json.dumps(question['options'])
            
            # Create record in Airtable
            table.create(record_data)
        
        st.success(f"Form başarıyla kaydedildi! Event ID: {event_id}")
        
        # Update event_features table
        try:
            event_features_table = get_event_features_table()
            
            # Convert event_id to integer for comparison
            # Handle both string and integer event_id
            if isinstance(event_id, str):
                event_id_int = int(event_id) if event_id.isdigit() else 0
            else:
                event_id_int = int(event_id) if event_id else 0
                
            st.info(f"Looking for event_id: {event_id_int}, feature_id: 1")
            
            # Look for existing record with same event_id and feature_id = 1
            records = event_features_table.all(formula=f"AND({{event_id}} = {event_id_int}, {{feature_id}} = 1)")
            st.info(f"Found {len(records)} existing records")
            
            if records:
                # Update existing record
                record_id = records[0]['id']
                event_features_table.update(record_id, {"is_active": True})
                st.info("Event features table updated successfully!")
            else:
                # Create new record
                event_features_table.create({
                    "event_id": event_id_int,
                    "feature_id": 1,
                    "is_active": True
                })
                st.info("New event features record created successfully!")
                
        except Exception as e:
            st.warning(f"Event features table update failed: {str(e)}")
            st.error(f"Error details: {str(e)}")
        
        # Clear the form and reset counters
        st.session_state.questions = []
        st.session_state.question_counter = 0
        st.session_state.show_preview = False
        
        # Show success message and navigation options
        st.success("✅ Form başarıyla kaydedildi!")
        st.info("Form Builder'ı temizledik. Yeni sorular ekleyebilir veya ana sayfaya dönebilirsiniz.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🏠 Ana Sayfaya Dön", type="primary", use_container_width=True, key="nav_to_home_form"):
                st.switch_page("app.py")
        with col2:
            if st.button("⚙️ Özellik Yönetimi", type="secondary", use_container_width=True, key="nav_to_features_form"):
                st.switch_page("pages/feature_management.py")
        with col3:
            if st.button("📝 Yeni Form Oluştur", type="secondary", use_container_width=True, key="new_form"):
                st.rerun()
        
    except Exception as e:
        st.error(f"Form kaydedilirken hata oluştu: {str(e)}")

def render_question_preview(question):
    """Render a preview of how the question will look"""
    st.markdown(f"**{question['question']}**")
    
    if question['type'] == 'Yazı':
        st.text_input("Cevap", key=f"preview_{question['id']}", disabled=True)
    elif question['type'] == 'Sayı':
        st.number_input("Cevap", key=f"preview_{question['id']}", disabled=True)
    elif question['type'] == 'Virgüllü sayı':
        st.number_input("Cevap", key=f"preview_{question['id']}", step=0.1, disabled=True)
    elif question['type'] == 'Tarih':
        st.date_input("Cevap", value=datetime.now().date(), key=f"preview_{question['id']}", disabled=True)
    elif question['type'] == 'Saat ve tarih':
        st.text_input("Cevap", value=datetime.now().strftime("%Y-%m-%d %H:%M"), key=f"preview_{question['id']}", disabled=True)
    elif question['type'] == 'Doğru yanlış':
        st.radio("Cevap", ["Evet", "Hayır"], key=f"preview_{question['id']}", disabled=True)
    elif question['type'] in ['Çoktan seçmeli', 'Çoktan seçmeli çoklu cevap']:
        if question['options']:
            if question['type'] == 'Çoktan seçmeli':
                st.radio("Cevap", question['options'], key=f"preview_{question['id']}", disabled=True)
            else:
                st.multiselect("Cevap", question['options'], key=f"preview_{question['id']}", disabled=True)
        else:
            st.info("Seçenek ekleyin")

# Main app
def main():
    st.title("📝 Form Builder Dashboard")
    st.markdown("Kayıt formu oluşturmak için aşağıdaki araçları kullanın.")
    
    # Back to home button
    if st.sidebar.button("🏠 Ana Sayfaya Dön", key="sidebar_home"):
        st.switch_page("app.py")
    
    # Get event_id from session state
    event_id = st.session_state.get('event_id', None)
    feature_key = st.session_state.get('feature_key', None)
    
    if event_id is None:
        st.error("Event ID bulunamadı. Lütfen ana sayfadan tekrar başlayın.")
        if st.button("🏠 Ana Sayfaya Dön", key="error_home"):
            st.switch_page("app.py")
        return
    
    st.info(f"Event ID: {event_id}")
    if feature_key:
        st.info(f"Özellik: {feature_key}")
    
    # Main content area
    st.header("Form Oluşturucu")
    
    if not st.session_state.questions:
        st.info("Soru eklemek için aşağıdaki 'Yeni Soru Ekle' butonuna tıklayın.")
    
    for i, question in enumerate(st.session_state.questions):
        with st.container():
            st.markdown("---")
            
            # Question controls - using containers instead of nested columns
            control_container = st.container()
            with control_container:
                col_delete, col_up, col_down = st.columns([2, 1, 1])
                
                with col_delete:
                    if st.button(f"🗑️ Sil", key=f"delete_{question['id']}"):
                        remove_question(question['id'])
                        st.rerun()
                
                with col_up:
                    if st.button("⬆️", key=f"up_{question['id']}"):
                        move_question_up(i)
                        st.rerun()
                
                with col_down:
                    if st.button("⬇️", key=f"down_{question['id']}"):
                        move_question_down(i)
                        st.rerun()
            
            # Question form
            question['question'] = st.text_input(
                "Soru:", 
                value=question['question'],
                key=f"question_text_{question['id']}"
            )
            
            # Type and required fields
            type_container = st.container()
            with type_container:
                col_type, col_required = st.columns(2)
                
                with col_type:
                    question['type'] = st.selectbox(
                        "Veri Tipi:",
                        options=list(DATA_TYPES.keys()),
                        index=list(DATA_TYPES.keys()).index(question['type']),
                        key=f"type_{question['id']}"
                    )
                
                with col_required:
                    question['is_required'] = st.checkbox(
                        "Zorunlu alan",
                        value=question['is_required'],
                        key=f"required_{question['id']}"
                    )
            
            # Multiple choice options
            if question['type'] in ['Çoktan seçmeli', 'Çoktan seçmeli çoklu cevap']:
                st.markdown("**Seçenekler:**")
                
                for j, option in enumerate(question['options']):
                    option_container = st.container()
                    with option_container:
                        col_option, col_remove = st.columns([4, 1])
                        with col_option:
                            question['options'][j] = st.text_input(
                                f"Seçenek {j+1}:",
                                value=option,
                                key=f"option_{question['id']}_{j}"
                            )
                        with col_remove:
                            if st.button("❌", key=f"remove_option_{question['id']}_{j}"):
                                remove_option(question['id'], j)
                                st.rerun()
                
                if st.button("➕ Seçenek Ekle", key=f"add_option_{question['id']}"):
                    add_option(question['id'])
                    st.rerun()
    
    # Add question button below the last question
    if st.button("➕ Yeni Soru Ekle", type="primary", use_container_width=True):
        add_question()
    
    # Preview and Apply buttons
    st.markdown("---")
    
    if st.session_state.questions:
        col_preview, col_apply = st.columns(2)
        
        with col_preview:
            if st.button("👁️ Formu Önizle", type="secondary", use_container_width=True):
                st.session_state.show_preview = not st.session_state.show_preview
        
        with col_apply:
            if st.button("✅ Formu Uygula", type="primary", use_container_width=True):
                save_form()
    
    # Preview section
    if st.session_state.show_preview and st.session_state.questions:
        st.markdown("---")
        st.header("Form Önizleme")
        st.markdown("**Oluşturulan Form:**")
        
        for question in st.session_state.questions:
            with st.container():
                st.markdown("---")
                
                # Show required indicator
                required_text = " *" if question['is_required'] else ""
                st.markdown(f"**Soru {question['rank'] + 1}{required_text}**")
                
                # Render preview
                render_question_preview(question)

if __name__ == "__main__":
    main() 