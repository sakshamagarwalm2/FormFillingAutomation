import streamlit as st
import requests
import json
import ast
from typing import Dict, Optional, List

# FastAPI backend URL
API_URL = "http://localhost:8000"

def parse_list_input(value: str) -> List[str]:
    """Parse list input from string format to actual list"""
    if not value or not isinstance(value, str):
        return []
    
    value = value.strip()
    
    # Handle different list formats
    if value.startswith('[') and value.endswith(']'):
        try:
            # Try to parse as Python list literal
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except (ValueError, SyntaxError):
            pass
    
    # Handle comma-separated values
    if ',' in value:
        return [item.strip().strip("'\"") for item in value.split(',') if item.strip()]
    
    # Single value
    return [value]

def format_list_for_display(value) -> str:
    """Format list for display in text input"""
    if isinstance(value, list):
        return str(value)
    return str(value) if value else ""

def init_session_state():
    """Initialize session state variables"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'form_fields' not in st.session_state:
        st.session_state.form_fields = {}
    if 'errors' not in st.session_state:
        st.session_state.errors = {}
    if 'warning' not in st.session_state:
        st.session_state.warning = {}
    if 'next_field' not in st.session_state:
        st.session_state.next_field = None
    if 'form_complete' not in st.session_state:
        st.session_state.form_complete = False
    if 'current_field' not in st.session_state:
        st.session_state.current_field = None
    if 'missing_fields' not in st.session_state:
        st.session_state.missing_fields = []
    if 'media_type' not in st.session_state:
        st.session_state.media_type = None
    if 'media_urls' not in st.session_state:
        st.session_state.media_urls = []
    if 'edited_fields' not in st.session_state:
        st.session_state.edited_fields = {}
    if 'session_timeoutin' not in st.session_state:
        st.session_state.session_timeoutin = None
    # In init_session_state()
    if 'address_got' not in st.session_state:
        st.session_state.address_got = False


def send_message(message: str, session_id: Optional[str] = None, media_type: Optional[str] = None, media_urls: Optional[List[str]] = None) -> Optional[Dict]:
    """Send message to FastAPI backend /chat endpoint"""
    try:
        # Properly format fields before sending
        formatted_fields = {}
        for field, value in {**st.session_state.form_fields, **st.session_state.edited_fields}.items():
            if isinstance(value, str) and field in ['iab_category', 'iab_id', 'targeting_keywords']:  # Add other list fields as needed
                formatted_fields[field] = parse_list_input(value)
            else:
                formatted_fields[field] = value
        
        payload = {
            "user_input": message,
            "session_id": session_id,
            "fields": formatted_fields,
            "history": st.session_state.chat_history
        }
        if media_type:
            payload["media_type"] = media_type
        if media_urls:
            payload["media_urls"] = media_urls
        response = requests.post(
            f"{API_URL}/chat",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with backend: {e}")
        return None

def start_conversation() -> Optional[Dict]:
    """Start a new conversation using /start endpoint"""
    try:
        response = requests.post(f"{API_URL}/start", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error starting conversation: {e}")
        return None

def ping_session(session_id: str) -> Optional[Dict]:
    """Ping the backend to keep the session alive"""
    try:
        response = requests.post(f"{API_URL}/ping", params={"session_id": session_id}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error pinging session: {e}")
        return None

def check_health():
    """Check the health of the FastAPI backend"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error checking backend health: {e}")
        return None

def start_new_session_with_reset(session_id: Optional[str] = None) -> Optional[Dict]:
    """Start a new session and destroy the old one using /start endpoint with reset"""
    try:
        params = {"reset_session_id": session_id} if session_id else {}
        response = requests.post(f"{API_URL}/start", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error starting new session: {e}")
        return None

def update_session_state_from_response(response_data: Dict):
    """Update session state from API response"""
    st.session_state.session_id = response_data.get('session_id')
    st.session_state.form_fields = response_data.get('fields', {})
    st.session_state.errors = response_data.get('errors', {})
    st.session_state.warning = response_data.get('warning', {})
    st.session_state.current_field = response_data.get('current_field')
    st.session_state.next_field = response_data.get('next_field')
    st.session_state.form_complete = response_data.get('is_complete', False)
    st.session_state.missing_fields = response_data.get('missing_fields', [])
    st.session_state.edited_fields = {}  # Clear edited fields after response
    st.session_state.session_timeoutin = response_data.get('session_timeoutin')
    # In update_session_state_from_response()
    st.session_state.address_got = response_data.get('address_got', False)


def reset_session_state():
    """Reset all session state variables"""
    st.session_state.session_id = None
    st.session_state.form_fields = {}
    st.session_state.chat_history = []
    st.session_state.errors = {}
    st.session_state.warning = {}
    st.session_state.next_field = None
    st.session_state.form_complete = False
    st.session_state.current_field = None
    st.session_state.missing_fields = []
    st.session_state.media_type = None
    st.session_state.media_urls = []
    st.session_state.edited_fields = {}
    

# Initialize session state
init_session_state()

# Streamlit UI
st.title("AI-Powered Form Assistant")
st.subheader("Let me help you fill out your advertising campaign form!")

# Sidebar for form status, actions, and manual field editing
with st.sidebar:
    if st.button("Check Backend Health", type="secondary"):
        health_status = check_health()
        if health_status:
            st.success("Backend is healthy!")
            st.json(health_status)
        else:
            st.error("Failed to retrieve backend health status.")

    st.header("Form Progress")

    if st.button("📶 Ping Session"):
        try:
            ping_response = requests.post(
                f"{API_URL}/ping",
                params={"session_id": st.session_state.session_id},
                timeout=10
            )
            ping_response.raise_for_status()
            data = ping_response.json()

            # Save relevant data to session_state
            st.session_state.session_timeoutin = data.get("refreshed_at")
            st.session_state.remaining_seconds = data.get("remaining_seconds_before_ping")  # before the refresh
            st.session_state.time_since_last_ping = data.get("time_since_last_ping_seconds")
            st.session_state.time_since_creation = data.get("time_since_creation_seconds")
            st.session_state.new_expiry_time = data.get("new_expiry_time")

            # Display success message with full info
            st.success(f"""
            ✅ Session Refreshed!  
            - Refreshed at: `{data.get("refreshed_at")}`  
            - Time since last ping: `{data.get("time_since_last_ping_seconds")}s`  
            - Time since session started: `{data.get("time_since_creation_seconds")}s`  
            - Time remaining before ping: `{data.get("remaining_seconds_before_ping")}s`  
            - New expiry: `{data.get("new_expiry_time")}`
            """)

        except requests.exceptions.RequestException as e:
            st.error(f"Error pinging session: {e}")

    st.subheader("📍 Address Flag")
    if st.session_state.address_got:
        st.success("✅ Address has been captured!")
    else:
        st.warning("⚠️ Address not yet captured.")

    if st.session_state.form_fields:
        st.subheader("Filled Fields:")
        for field, value in st.session_state.form_fields.items():
            if value:
                display_value = format_list_for_display(value)
                st.write(f"**{field}:** {display_value}")
    
    if st.session_state.errors:
        st.subheader("Errors:")
        for field, error in st.session_state.errors.items():
            st.error(f"{field}: {error}")
    if st.session_state.warning:
        st.subheader("Warnings:")
        for field, warning in st.session_state.warning.items():
            st.warning(f"{field}: {warning}")
    
    if st.session_state.current_field and st.session_state.current_field != "None":
        st.subheader("🎯 Current Field:")
        st.info(f"**{st.session_state.current_field}**")
    else:
        st.subheader("🎯 Current Field:")
        st.info("No field currently being requested.")
    
    if st.session_state.next_field and st.session_state.next_field != "None":
        st.subheader("⏭️ Next Field:")
        st.info(f"**{st.session_state.next_field}**")
    else:
        st.subheader("⏭️ Next Field:")
        st.info("No next field available.")
    
    if st.session_state.form_complete:
        st.success("✅ Form Complete!")
    else:
        total_possible_fields = len(st.session_state.form_fields) + len(st.session_state.missing_fields)
        filled_fields = len([v for v in st.session_state.form_fields.values() if v])
        if total_possible_fields > 0:
            progress = filled_fields / total_possible_fields
            st.progress(progress)
            st.write(f"Progress: {filled_fields}/{total_possible_fields} fields")
        else:
            st.write("Starting form...")
    
    # Manual Field Editing Section
    st.header("Edit Form Fields")
    with st.form(key="edit_fields_form"):
        edited_fields = {}
        for field in st.session_state.form_fields.keys():
            current_value = st.session_state.form_fields.get(field, "")
            display_value = format_list_for_display(current_value)
            
            # Add help text for list fields
            help_text = None
            if field in ['iab_category', 'iab_id', 'targeting_keywords']:
                help_text = "Enter as a list: ['item1', 'item2'] or comma-separated: item1, item2"
            
            edited_value = st.text_input(
                f"{field}", 
                value=display_value, 
                key=f"edit_{field}",
                help=help_text
            )
            
            if edited_value != display_value:
                # Parse list fields properly
                if field in ['iab_category', 'iab_id', 'targeting_keywords']:
                    edited_fields[field] = parse_list_input(edited_value)
                else:
                    edited_fields[field] = edited_value
        
        submit_edit_button = st.form_submit_button("Apply Field Changes")
        if submit_edit_button:
            st.session_state.edited_fields = edited_fields

            # Send empty message to trigger backend update with edited fields
            response = send_message(
                message="",  # Empty user input to trigger backend update
                session_id=st.session_state.session_id
            )

            if response:
                update_session_state_from_response(response)
                st.session_state.chat_history.append("User: (edited fields updated)")
                st.session_state.chat_history.append(f"AI: {response.get('response', '')}")
                st.success("Field changes applied and backend updated.")
                st.rerun()
            else:
                st.error("Failed to apply field changes.")


    if st.session_state.session_id:
        st.markdown("---")
        if st.button("🔄 Start New Session", type="secondary"):
            new_session_response = start_new_session_with_reset(st.session_state.session_id)
            if new_session_response:
                reset_session_state()
                update_session_state_from_response(new_session_response)
                st.session_state.chat_history = [f"AI: {new_session_response.get('response', '')}"]
                st.success("Started a new session!")
                st.rerun()

# Main chat interface
st.header("Chat Interface")

# Display chat history
for message in st.session_state.chat_history:
    if message.startswith("User:"):
        with st.chat_message("user"):
            st.write(message[5:].strip())
    elif message.startswith("AI:"):
        with st.chat_message("assistant"):
            st.write(message[3:].strip())
    else:
        with st.chat_message("assistant"):
            st.write(message.strip())

# Conditional input for media_type
if st.session_state.next_field == "media_type":
    st.subheader("Provide Media Details")
    with st.form(key="media_form"):
        media_type = st.selectbox(
            "Select Media Type",
            options=["image", "video", "js_html"],
            index=0,
            help="Choose the type of media for your ads"
        )
        st.write("Enter Media URLs (one per line)")
        media_urls_input = st.text_area("Media URLs", placeholder="https://example.com/image1.jpg\nhttps://example.com/image2.jpg", help="Enter one or more URLs for your media")
        submit_button = st.form_submit_button("Submit Media")
        
        if submit_button:
            media_urls = [url.strip() for url in media_urls_input.split('\n') if url.strip()]
            if not media_urls:
                st.error("Please provide at least one valid media URL.")
            else:
                user_input = f"Media type: {media_type}, URLs: {', '.join(media_urls)}"
                st.session_state.media_type = media_type
                st.session_state.media_urls = media_urls
                response = send_message(
                    user_input,
                    st.session_state.session_id,
                    media_type=media_type,
                    media_urls=media_urls
                )
                if response:
                    update_session_state_from_response(response)
                    st.session_state.chat_history.append(f"User: {user_input}")
                    st.session_state.chat_history.append(f"AI: {response.get('response', '')}")
                    st.rerun()
else:
    # Standard chat input for other fields
    user_input = st.chat_input("Type your message here...")
    if user_input:
        st.session_state.chat_history.append(f"User: {user_input}")
        response = send_message(user_input, st.session_state.session_id)
        if response:
            update_session_state_from_response(response)
            st.session_state.chat_history.append(f"AI: {response.get('response', '')}")
            st.rerun()

# Start conversation button
if not st.session_state.session_id:
    if st.button("🚀 Start Conversation", type="primary"):
        start_response = start_conversation()
        if start_response:
            update_session_state_from_response(start_response)
            st.session_state.chat_history.append(f"AI: {start_response.get('response', '')}")
            st.rerun()

# Display current form state in expandable section
with st.expander("🔍 Debug: Current Form State", expanded=False):
    st.json({
        "session_id": st.session_state.session_id,
        "fields": st.session_state.form_fields,
        "edited_fields": st.session_state.edited_fields,
        "errors": st.session_state.errors,
        "warning": st.session_state.warning,
        "next_field": st.session_state.next_field,
        "current_field": st.session_state.current_field,
        "form_complete": st.session_state.form_complete,
        "missing_fields": st.session_state.missing_fields,
        "chat_history_length": len(st.session_state.chat_history),
        "media_urls": st.session_state.media_urls,
        "session_timeoutin": st.session_state.session_timeoutin
    })

# Additional information panel
if st.session_state.session_id:
    with st.expander("📊 Session Information", expanded=False):
        st.write(f"**Session ID:** {st.session_state.session_id}")
        st.write(f"**Total Messages:** {len(st.session_state.chat_history)}")
        st.write(f"**Fields Filled:** {len([v for v in st.session_state.form_fields.values() if v])}")
        st.write(f"**Fields Remaining:** {len(st.session_state.missing_fields)}")
        if st.session_state.edited_fields:
            st.write(f"**Edited Fields (Pending):** {', '.join(st.session_state.edited_fields.keys())}")
        if st.session_state.current_field and st.session_state.current_field != "None":
            st.write(f"**Current Field:** {st.session_state.current_field}")
        if st.session_state.next_field and st.session_state.next_field != "None":
            st.write(f"**Next Field:** {st.session_state.next_field}")
        if st.session_state.form_complete:
            st.success("🎉 All required fields have been completed!")
            st.balloons()
        elif st.session_state.missing_fields:
            st.info(f"Still need: {', '.join(st.session_state.missing_fields)}")