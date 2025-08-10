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
if 'has_loaded_form' not in st.session_state:
    st.session_state.has_loaded_form = False  # load guard

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
# Reverse map for loading existing rows
DATA_TYPES_REVERSE = {v: k for k, v in DATA_TYPES.items()}

def get_airtable_api():
    return Api(AIRTABLE_CONFIG["api_key"])

def get_airtable_table(table_name="registration_form"):
    api = get_airtable_api()
    return api.table(AIRTABLE_CONFIG["base_id"], table_name)

def get_event_features_table():
    api = get_airtable_api()
    return api.table(AIRTABLE_CONFIG["base_id"], "event_features")

def add_question():
    qid = f"question_{st.session_state.question_counter}"
    st.session_state.questions.append({
        'id': qid,
        'question': '',
        'type': 'Yazı',
        'is_required': False,
        'options': [],
        'rank': len(st.session_state.questions)
    })
    st.session_state.question_counter += 1

def remove_question(question_id):
    st.session_state.questions = [q for q in st.session_state.questions if q['id'] != question_id]
    for i, q in enumerate(st.session_state.questions):
        q['rank'] = i

def move_question_up(index):
    if index > 0:
        st.session_state.questions[index], st.session_state.questions[index-1] = \
            st.session_state.questions[index-1], st.session_state.questions[index]
        for i, q in enumerate(st.session_state.questions):
            q['rank'] = i

def move_question_down(index):
    if index < len(st.session_state.questions) - 1:
        st.session_state.questions[index], st.session_state.questions[index+1] = \
            st.session_state.questions[index+1], st.session_state.questions[index]
        for i, q in enumerate(st.session_state.questions):
            q['rank'] = i

def add_option(question_id):
    for q in st.session_state.questions:
        if q['id'] == question_id:
            q['options'].append('')
            break

def remove_option(question_id, option_index):
    for q in st.session_state.questions:
        if q['id'] == question_id:
            q['options'].pop(option_index)
            break

# -------- LOAD EXISTING FORM (ordered by rank asc) ----------
def load_existing_form(event_id):
    """Always attempt to load once per page entry; populates builder if rows exist."""
    if st.session_state.has_loaded_form:
        return
    try:
        table = get_airtable_table()
        event_id_int = int(event_id)
        existing = table.all(formula=f"{{event_id}} = {event_id_int}")
        if not existing:
            st.session_state.has_loaded_form = True
            return

        # sort by 'rank' (default 0 if missing)
        existing_sorted = sorted(existing, key=lambda r: r['fields'].get('rank', 0))

        st.session_state.questions = []
        st.session_state.question_counter = 0

        for rec in existing_sorted:
            f = rec.get('fields', {})
            qid = f"question_{st.session_state.question_counter}"

            # type mapping
            saved_type_code = f.get('type', 'text')
            saved_type_label = DATA_TYPES_REVERSE.get(saved_type_code, 'Yazı')

            # possible answers
            options_raw = f.get('possible_answers')
            if isinstance(options_raw, list):
                options_list = options_raw
            elif isinstance(options_raw, str):
                try:
                    parsed = json.loads(options_raw)
                    options_list = parsed if isinstance(parsed, list) else []
                except Exception:
                    options_list = []
            else:
                options_list = []

            st.session_state.questions.append({
                'id': qid,
                'question': f.get('name', ''),
                'type': saved_type_label,
                'is_required': bool(f.get('is_required', False)),
                'options': options_list,
                'rank': int(f.get('rank', len(st.session_state.questions)))
            })
            st.session_state.question_counter += 1

        st.session_state.has_loaded_form = True
        st.info("Mevcut kayıt formu yüklendi. Düzenleyebilirsiniz.")
    except Exception as e:
        st.warning(f"Mevcut form yüklenemedi: {str(e)}")
        st.session_state.has_loaded_form = True  # avoid loops

# -------- SAVE: DELETE ALL THEN CREATE FRESH ----------
def save_form():
    if not st.session_state.questions:
        st.error("Lütfen en az bir soru ekleyin!")
        return

    raw_event_id = st.session_state.event_id if st.session_state.event_id is not None else 0
    try:
        event_id_int = int(raw_event_id)
    except Exception:
        st.error("Geçersiz Event ID.")
        return

    try:
        table = get_airtable_table()

        # 1) delete all existing rows for this event_id
        try:
            to_delete = table.all(formula=f"{{event_id}} = {event_id_int}")
            ids = [r['id'] for r in to_delete]
            if ids:
                # batch_delete if available, else fallback to loop
                try:
                    table.batch_delete(ids)
                except Exception:
                    for rid in ids:
                        table.delete(rid)
        except Exception as e_del:
            st.warning(f"Eski form silinirken uyarı: {str(e_del)}")

        # 2) create fresh rows from the builder (respect rank)
        questions_sorted = sorted(st.session_state.questions, key=lambda q: q['rank'])
        for q in questions_sorted:
            record_data = {
                "event_id": event_id_int,
                "name": q['question'],
                "type": DATA_TYPES[q['type']],
                "is_required": q['is_required'],
                "rank": q['rank']
            }
            if q['type'] in ['Çoktan seçmeli', 'Çoktan seçmeli çoklu cevap']:
                record_data["possible_answers"] = json.dumps(q['options'])

            try:
                table.create(record_data)
            except Exception as e_new:
                st.error(f"Oluşturma hatası (soru: {q['question']}): {str(e_new)}")

        st.success(f"Form başarıyla kaydedildi! Event ID: {event_id_int}")

        # Keep event_features toggled ON for this event
        try:
            ef_table = get_event_features_table()
            records = ef_table.all(formula=f"AND({{event_id}} = {event_id_int}, {{feature_id}} = 1)")
            if records:
                ef_table.update(records[0]['id'], {"is_active": True})
            else:
                ef_table.create({"event_id": event_id_int, "feature_id": 1, "is_active": True})
        except Exception as e:
            st.warning(f"Event features güncelleme uyarısı: {str(e)}")

        st.session_state.show_preview = False
        st.info("Değişiklikleriniz kaydedildi.")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🏠 Ana Sayfaya Dön", type="primary", use_container_width=True, key="nav_to_home_form"):
                st.switch_page("app.py")
        with col2:
            if st.button("⚙️ Özellik Yönetimi", type="secondary", use_container_width=True, key="nav_to_features_form"):
                st.switch_page("pages/feature_management.py")
        with col3:
            if st.button("🔄 Formu Yeniden Yükle", type="secondary", use_container_width=True, key="reload_form"):
                st.session_state.has_loaded_form = False
                st.rerun()

    except Exception as e:
        st.error(f"Form kaydedilirken hata oluştu: {str(e)}")

def render_question_preview(question):
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

# ---------------- MAIN ----------------
def main():
    st.title("📝 Form Builder Dashboard")
    st.markdown("Kayıt formu oluşturmak / düzenlemek için aşağıdaki araçları kullanın.")

    if st.sidebar.button("🏠 Ana Sayfaya Dön", key="sidebar_home"):
        st.switch_page("app.py")

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

    # Load existing schema (once per entry)
    load_existing_form(event_id)

    st.header("Form Oluşturucu")

    if not st.session_state.questions:
        st.info("Mevcut form bulunamadı. Yeni bir soru ekleyebilirsiniz.")

    for i, q in enumerate(st.session_state.questions):
        with st.container():
            st.markdown("---")
            ctrl = st.container()
            with ctrl:
                c1, c2, c3 = st.columns([2,1,1])
                with c1:
                    if st.button("🗑️ Sil", key=f"delete_{q['id']}"):
                        remove_question(q['id'])
                        st.rerun()
                with c2:
                    if st.button("⬆️", key=f"up_{q['id']}"):
                        move_question_up(i)
                        st.rerun()
                with c3:
                    if st.button("⬇️", key=f"down_{q['id']}"):
                        move_question_down(i)
                        st.rerun()

            q['question'] = st.text_input("Soru:", value=q['question'], key=f"question_text_{q['id']}")

            with st.container():
                ctype, creq = st.columns(2)
                with ctype:
                    q['type'] = st.selectbox(
                        "Veri Tipi:",
                        options=list(DATA_TYPES.keys()),
                        index=list(DATA_TYPES.keys()).index(q['type']),
                        key=f"type_{q['id']}"
                    )
                with creq:
                    q['is_required'] = st.checkbox("Zorunlu alan", value=q['is_required'], key=f"required_{q['id']}")

            if q['type'] in ['Çoktan seçmeli', 'Çoktan seçmeli çoklu cevap']:
                st.markdown("**Seçenekler:**")
                for j, opt in enumerate(q['options']):
                    with st.container():
                        co, cr = st.columns([4,1])
                        with co:
                            q['options'][j] = st.text_input(f"Seçenek {j+1}:", value=opt, key=f"option_{q['id']}_{j}")
                        with cr:
                            if st.button("❌", key=f"remove_option_{q['id']}_{j}"):
                                remove_option(q['id'], j)
                                st.rerun()
                if st.button("➕ Seçenek Ekle", key=f"add_option_{q['id']}"):
                    add_option(q['id'])
                    st.rerun()

    if st.button("➕ Yeni Soru Ekle", type="primary", use_container_width=True):
        add_question()

    st.markdown("---")
    if st.session_state.questions:
        cprev, capply = st.columns(2)
        with cprev:
            if st.button("👁️ Formu Önizle", type="secondary", use_container_width=True):
                st.session_state.show_preview = not st.session_state.show_preview
        with capply:
            if st.button("✅ Formu Uygula", type="primary", use_container_width=True):
                save_form()

    if st.session_state.show_preview and st.session_state.questions:
        st.markdown("---")
        st.header("Form Önizleme")
        for q in sorted(st.session_state.questions, key=lambda x: x['rank']):
            st.markdown("---")
            req = " *" if q['is_required'] else ""
            st.markdown(f"**Soru {q['rank'] + 1}{req}**")
            render_question_preview(q)

if __name__ == "__main__":
    main()
