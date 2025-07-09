from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, computed_field
from typing import Dict, Optional, List, Union, Tuple
import os
import json
import re
import uuid
import asyncio
import socket
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv
from dateutil import parser

from form_config import FORM_FIELDS, get_required_fields
from llm_client import LLMClient
from prompt_generator import PromptGenerator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize LLM client and prompt generator
llm_client = LLMClient()
prompt_generator = PromptGenerator()

# In-memory session storage with cleanup
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "1800"))  # Default to 30 minutes
sessions: Dict[str, Dict] = {}

class ChatRequest(BaseModel):
    user_input: Optional[str] = None
    session_id: Optional[str] = None
    history: Optional[List[str]] = None
    fields: Optional[Dict[str, Optional[Union[str, List[str], int, float, Dict[str, List[str]]]]]] = None
    media_urls: Optional[List[str]] = None
    media_type: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    fields: Dict[str, Optional[Union[str, List[str], int, float, Dict[str, List[str]]]]]
    session_id: str
    errors: Dict[str, str] = {}
    warning: Dict[str, str] = {}
    next_field: Optional[str] = None
    current_field: Optional[str] = None
    is_complete: bool = False
    missing_fields: List[str] = []
    ai_provider: str = ""
    model_name: str = ""
    session_timeoutin: int = SESSION_TIMEOUT
    address_got: bool = False 

class FormState(BaseModel):
    fields: Dict[str, Optional[Union[str, List[str], int, float, Dict[str, List[str]]]]]
    conversation_history: List[str]
    timing_days_filled: List[str] = []
    address_sent: bool = False
    
    @computed_field
    @property
    def missing_fields(self) -> List[str]:
        """Compute missing required fields dynamically"""
        return get_required_fields(self.fields)
    
    @computed_field
    @property
    def is_complete(self) -> bool:
        """Check if form is complete"""
        return len(self.missing_fields) == 0

class SessionData(BaseModel):
    form_state: FormState
    last_accessed: datetime
    created_at: datetime

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return str(uuid.uuid4())

def get_or_create_session(session_id: Optional[str] = None, 
                         history: Optional[List[str]] = None,
                         fields: Optional[Dict[str, Optional[Union[str, List[str], int, float]]]] = None) -> tuple[str, SessionData]:
    """Get existing session or create new one"""
    current_time = datetime.now()
    
    if session_id and session_id in sessions:
        # Check if session is still valid
        session_data = sessions[session_id]
        if current_time - session_data.last_accessed < timedelta(seconds=SESSION_TIMEOUT):
            session_data.last_accessed = current_time
            return session_id, session_data
        else:
            # Session expired, remove it
            del sessions[session_id]
    
    # Create new session
    new_session_id = generate_session_id()
    
    # Initialize form state with provided data or defaults
    initial_fields = fields if fields else {}
    initial_history = history if history else []
    
    form_state = FormState(
        fields=initial_fields,
        conversation_history=initial_history,
        timing_days_filled=[],
    )
    
    session_data = SessionData(
        form_state=form_state,
        last_accessed=current_time,
        created_at=current_time
    )
    
    sessions[new_session_id] = session_data
    return new_session_id, session_data

async def cleanup_expired_sessions():
    """Remove expired sessions"""
    current_time = datetime.now()
    expired_sessions = [
        session_id for session_id, session_data in sessions.items()
        if current_time - session_data.last_accessed > timedelta(seconds=SESSION_TIMEOUT)
    ]
    
    for session_id in expired_sessions:
        del sessions[session_id]
        logger.info(f"Cleaned up expired session: {session_id}")

# Background task to cleanup expired sessions
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_cleanup())

async def periodic_cleanup():
    """Periodically cleanup expired sessions"""
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        await cleanup_expired_sessions()

def clean_response_for_user(response: str) -> str:
    """Clean response by removing extraction tags for user display"""
    if not response or not isinstance(response, str):
        return ""
    
    # Remove EXTRACTED and FUTURE_TRACKING tags
    response = re.sub(r'<EXTRACTED>.*?</EXTRACTED>', '', response, flags=re.DOTALL)
    response = re.sub(r'<NEXT_FIELD_NAME>.*?</NEXT_FIELD_NAME>', '', response, flags=re.DOTALL)
    response = re.sub(r'<CUR_FIELD>.*?</CUR_FIELD>', '', response, flags=re.DOTALL)
    response = re.sub(r'<EXIT>.*?</EXIT>', '', response, flags=re.DOTALL)

    # Remove unwanted prefixes like USER_MESSAGE:
    response = re.sub(r'^\s*USER_MESSAGE:\s*', '', response, flags=re.IGNORECASE)

    return response.strip()

def extract_json_from_response(response: str) -> Optional[Dict]:
    """Extract JSON from LLM response if present"""
    if not response or not isinstance(response, str):
        return None
        
    # Look for JSON in various formats
    patterns = [
        r'<json>(.*?)</json>',
        r'<EXTRACTED>(.*?)</EXTRACTED>',
        r'\{[^{}]*"[^"]*":[^{}]*\}',  # Simple JSON pattern
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            json_str = match.group(1).strip() if len(match.groups()) > 0 else match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue
    return None
    
def extract_next_field_name(response: str) -> Optional[str]:
    """Extract the next field name from LLM response if present in tag"""
    match = re.search(r'<NEXT_FIELD_NAME>(.*?)</NEXT_FIELD_NAME>', response, re.DOTALL)
    return match.group(1).strip() if match else None

def extract_current_field(response: str) -> Optional[str]:
    """Extract the current field name from LLM response if present in tag"""
    match = re.search(r'<CUR_FIELD>(.*?)</CUR_FIELD>', response, re.DOTALL)
    return match.group(1).strip() if match else None

def extract_exit_command(response: str) -> bool:
    """Extract exit command from LLM response if present"""
    match = re.search(r'<EXIT>(.*?)</EXIT>', response, re.DOTALL)
    if match:
        exit_value = match.group(1).strip().lower()
        return exit_value == 'exit'
    return False

def is_valid_domain(domain: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate if domain (including subdomain) is structurally valid and DNS-resolvable."""
    original_domain = domain.strip()
    only_domain = None

    # Remove protocol using urlparse
    if original_domain.startswith(('http://', 'https://')):
        parsed = urlparse(original_domain)
        domain = parsed.netloc or parsed.path
    else:
        domain = original_domain

    # Remove 'www.' if present
    if domain.startswith('www.'):
        domain = domain[4:]

    # Basic checks
    if not domain or len(domain) > 253:
        return False, f"Domain '{original_domain}' is too long or empty.", only_domain

    if domain.startswith('.') or domain.endswith('.'):
        return False, f"Domain '{original_domain}' starts or ends with a dot.", only_domain

    labels = domain.split('.')
    if len(labels) < 2:
        return False, f"Domain '{original_domain}' is incomplete (needs at least one dot).", only_domain

    # Validate each label
    for label in labels:
        if not label or len(label) > 63:
            return False, f"Label '{label}' in domain '{original_domain}' is invalid length.", only_domain
        if label.startswith('-') or label.endswith('-'):
            return False, f"Label '{label}' in domain '{original_domain}' starts/ends with hyphen.", only_domain
        if not re.match(r'^[a-zA-Z0-9-]+$', label):
            return False, f"Label '{label}' in domain '{original_domain}' contains invalid characters.", only_domain

    # Validate TLD (last label) - at least 2 letters
    tld = labels[-1]
    if not re.match(r'^[a-zA-Z]{2,}$', tld):
        return False, f"TLD '{tld}' in domain '{original_domain}' is invalid.", only_domain

    # DNS resolution check for full subdomain
    try:
        socket.gethostbyname(domain)
        only_domain = domain
        return True, None, only_domain
    except socket.gaierror:
        return False, f"Domain '{original_domain}' is not reachable or does not resolve.", only_domain

def validate_time_range(time_range: str) -> Tuple[bool, Optional[str]]:
    """
    Validate hour-only time range like '7-24'. Start and end must be integers 1–24, and start ≤ end.
    """
    pattern = r'^\s*(\d{1,2})\s*-\s*(\d{1,2})\s*$'
    match = re.match(pattern, time_range)
    
    if not match:
        return False, "Time range must be in the format 'start-end' using 1–24 hours, e.g., '7-22'."
    
    try:
        start_hour = int(match.group(1))
        end_hour = int(match.group(2))
        
        if not (1 <= start_hour <= 24 and 1 <= end_hour <= 24):
            return False, "Hours must be between 1 and 24."

        if start_hour > end_hour:
            return False, f"Start hour {start_hour} must not be greater than end hour {end_hour}."

        return True, None
    except ValueError:
        return False, "Invalid input. Use integers between 1 and 24 like '7-22'."


def extract_urls_from_text(text: str, current_field: Optional[str] = None) -> Tuple[List[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Extract URLs from user input, classify them as media or landingpage_url, and infer media_type.
    Handles protocol-less domains, validates domains, and distinguishes media types.
    """
    url_pattern = r'\b(?:https?://)?(?:www\.)?[a-zA-Z0-9-]{1,63}(?:\.[a-zA-Z0-9-]{1,63})+\b(?:/[^\s]*)?'
    urls = re.findall(url_pattern, text)

    cleaned_urls = []
    media_urls = []
    valid_domains = []
    landingpage_url = None
    inferred_media_type = None
    domain_errors = []
    advertiser_domain = None
    warn=None

    text_lower = text.lower()
    is_media_context = any(keyword in text_lower for keyword in ["image", "photo", "picture", "media", "upload", "video"])
    is_domain_context = any(keyword in text_lower for keyword in ["website", "domain", "site", "advertiser", "company", "brand", "domain name", "landing", "landingpage"])
    is_video_context = "video" in text_lower

    image_pattern = r'\.(jpg|jpeg|png|gif|webp|svg|bmp)$'
    video_pattern = r'(youtu\.be|youtube\.com|vimeo\.com)'

    for url in urls:
        full_url = url if url.startswith(('http://', 'https://')) else f"https://{url}"
        parsed = urlparse(full_url)
        domain_only = parsed.netloc or parsed.path.split('/')[0]

        is_image = re.search(image_pattern, parsed.path, re.IGNORECASE)
        is_video = re.search(video_pattern, parsed.netloc or '', re.IGNORECASE)

        if is_video_context or is_video:
            inferred_media_type = inferred_media_type or 'video'
            media_urls.append(full_url)
            cleaned_urls.append(full_url)
        elif is_media_context or is_image:
            inferred_media_type = inferred_media_type or 'image'
            media_urls.append(full_url)
            cleaned_urls.append(full_url)
        elif is_domain_context or current_field == "landingpage_url":
            
            if not url.startswith(('http://', 'https://')):
                warn = f'You have used {url} as the landing page but to ensure your ad is delivered on all devices, it is suggested to use HTTPS whenever possible. \nConsider updating it to https://{url}.'
            is_valid, error_msg, only_domain = is_valid_domain(domain_only)
            if is_valid:
                landingpage_url = domain_only
                advertiser_domain = only_domain
                valid_domains.append(domain_only)
                cleaned_urls.append(full_url)
            else:
                domain_errors.append(f"{domain_only}: {error_msg}")
        else:
            inferred_media_type = inferred_media_type or 'image'
            media_urls.append(full_url)
            cleaned_urls.append(full_url)

    if domain_errors:
        return [], None, None, domain_errors[0],None,warn

    return media_urls, landingpage_url, inferred_media_type, None, advertiser_domain,warn

@app.get("/health")
async def health_check():
    """Health check endpoint with AI provider information"""
    llm_status = llm_client.get_status()
    
    return {
        "status": "healthy" if llm_status["ai_status"] == "healthy" else "degraded",
        **llm_status,
        "active_sessions": len(sessions)
    }


@app.post("/ping")
async def ping_session(session_id: str):
    """Ping endpoint to keep session alive (refresh session timeout)"""
    current_time = datetime.now()

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session ID not found")

    session = sessions[session_id]

    # Time info BEFORE refresh
    time_since_creation = (current_time - session.created_at).total_seconds()
    time_since_last_access = (current_time - session.last_accessed).total_seconds()
    expires_at = session.last_accessed + timedelta(seconds=SESSION_TIMEOUT)
    remaining_seconds_before_ping = max(0, int((expires_at - current_time).total_seconds()))

    # Refresh
    session.last_accessed = current_time
    new_expiry = current_time + timedelta(seconds=SESSION_TIMEOUT)

    return {
        "status": "session refreshed",
        "session_id": session_id,
        "refreshed_at": current_time.isoformat(),
        "session_started_at": session.created_at.isoformat(),
        "time_since_creation_seconds": int(time_since_creation),
        "time_since_last_ping_seconds": int(time_since_last_access),
        "remaining_seconds_before_ping": remaining_seconds_before_ping,
        "new_expiry_time": new_expiry.isoformat()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages with session management and data extraction"""
    # Validate inputs
    # Check: If neither user_input nor fields are provided, it's an invalid request
    if (not request.user_input or request.user_input.strip() == "") and not request.fields:
        raise HTTPException(status_code=400, detail="Either user_input or fields must be provided.")

    
    # Check if AI client is available
    if not llm_client.is_available():
        raise HTTPException(status_code=500, detail=f"{llm_client.ai_provider} AI service unavailable")
    
    # Get or create session
    session_id, session_data = get_or_create_session(
        request.session_id, 
        request.history, 
        request.fields
    )
    
    form_state = session_data.form_state

   #  Handle frontend-provided field updates
    if request.fields:
        for field_name, value in request.fields.items():
            if field_name in FORM_FIELDS:
                # Skip invalid/empty values
                if value is None or (isinstance(value, str) and str(value).lower().strip() in ["null", "none", "skip", "later", "n/a", ""]):
                    continue
                
                # Validate field value if it has constraints
                field_config = FORM_FIELDS[field_name]
                
                if field_config.get("type") == "enum" and "values" in field_config:
                    if value not in field_config["values"]:
                        form_state.fields[field_name] = None
                        continue
                
                elif field_config.get("type") == "list":
                    # For list fields, REPLACE the entire list instead of appending
                    if isinstance(value, list):
                        # Direct list assignment - replaces the entire list
                        form_state.fields[field_name] = value
                    elif isinstance(value, str) and value.strip():
                        # Convert string to list if needed
                        form_state.fields[field_name] = [value.strip()]
                    else:
                        # Handle other types by converting to string and putting in list
                        form_state.fields[field_name] = [str(value)]
                
                else:
                    # For non-list fields, direct assignment
                    form_state.fields[field_name] = value
        # Early return if fields were updated but no user message was sent
        if not request.user_input or request.user_input.strip() == "":
            sessions[session_id] = session_data
            return ChatResponse(
                response="Fields updated.",
                fields=form_state.fields,
                session_id=session_id,
                errors={}, 
                warning={},
                current_field=None,
                next_field=form_state.missing_fields[0] if form_state.missing_fields else None,
                is_complete=form_state.is_complete,
                missing_fields=form_state.missing_fields,
                ai_provider=llm_client.get_status()["ai_provider"],
                model_name=llm_client.get_status()["model_name"],
                session_timeoutin=SESSION_TIMEOUT,
                address_got=form_state.address_sent
            )




    # Update conversation history
    form_state.conversation_history.append(f"User: {request.user_input}")
    
    # Get campaign days for Timing field
    campaign_days = prompt_generator.days_of_week
    if "start_date" in form_state.fields and "end_date" in form_state.fields:
        campaign_days = prompt_generator._calculate_campaign_days(
            form_state.fields["start_date"], form_state.fields["end_date"]
        )
    
    # Get next field
    next_field = form_state.missing_fields[0] if form_state.missing_fields else None
    
    # Handle Timing field specifically
    current_timing_day = None
    if next_field == "Timing":
        current_timing_day = next(
            (day for day in campaign_days if day not in form_state.timing_days_filled),
            None
        )
        if not current_timing_day and form_state.fields.get("Timing"):
            # All days filled, remove Timing from missing fields
            form_state.timing_days_filled = []
            next_field = form_state.missing_fields[1] if len(form_state.missing_fields) > 1 else None
    
    # Extract URLs, landingpage_url, and inferred media_type from user input
    extracted_media_urls, extracted_landingpage_url, inferred_media_type, domain_error, extracted_advertiser_domain,warn = extract_urls_from_text(request.user_input, next_field)
    
    if domain_error:
        return ChatResponse(
            response=domain_error,
            fields=form_state.fields,
            session_id=session_id,
            errors={"landingpage_url": domain_error},
            warning={"landingpage_url": warn} if warn else {},
            current_field="landingpage_url",
            next_field=next_field,
            is_complete=form_state.is_complete,
            missing_fields=form_state.missing_fields,
            ai_provider=llm_client.get_status()["ai_provider"],
            model_name=llm_client.get_status()["model_name"],
            session_timeoutin=SESSION_TIMEOUT
        )
    
    # Combine with request.media_urls (if any) and append to existing media_urls
    current_media_urls = form_state.fields.get("media_urls", []) or []
    new_media_urls = (request.media_urls or []) + extracted_media_urls
    combined_media_urls = list(dict.fromkeys(current_media_urls + new_media_urls))
    
    # Determine media_type
    media_type = request.media_type or inferred_media_type
    if not media_type and combined_media_urls:
        for url in combined_media_urls:
            url_lower = url.lower()
            if any(url_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                media_type = 'image'
                break
            elif any(url_lower.endswith(ext) for ext in ['.mp4', '.webm', '.mov', '.avi', '.mkv']):
                media_type = 'video'
                break
            elif re.search(r'\b(video|stream|media)\b', url_lower):  # broad check for streaming platforms or links
                media_type = 'video'
                break
        media_type = media_type or 'image'


    # Generate LLM prompt
    prompt = None
    if combined_media_urls:
        prompt = prompt_generator.generate_chat_prompt(
            user_input=request.user_input,
            form_fields=form_state.fields,
            conversation_history=form_state.conversation_history,
            missing_fields=form_state.missing_fields,
            media_urls=combined_media_urls,
            media_type=media_type
        )
    elif extracted_landingpage_url and next_field == "landingpage_url":
        prompt = prompt_generator.generate_chat_prompt(
            user_input=request.user_input,
            form_fields=form_state.fields,
            conversation_history=form_state.conversation_history,
            missing_fields=form_state.missing_fields
        )
    elif next_field == "Timing" and current_timing_day:
        prompt = prompt_generator.generate_timing_prompt(
            form_fields=form_state.fields,
            missing_fields=form_state.missing_fields
        )
    else:
        prompt = prompt_generator.generate_chat_prompt(
            user_input=request.user_input,
            form_fields=form_state.fields,
            conversation_history=form_state.conversation_history,
            missing_fields=form_state.missing_fields
        )
    
    # Get AI response
    try:
        response = await llm_client.get_response(prompt)
    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        raise HTTPException(status_code=500, detail="AI service error")
    
    # Extract structured data from response
    extracted_data = extract_json_from_response(response)
    user_message = clean_response_for_user(response)
    extracted_next_field_name = extract_next_field_name(response)
    extracted_current_field_name = extract_current_field(response)
    should_exit = extract_exit_command(response)

    # Handle exit command - reset form state
    if should_exit:
        logger.info(f"Exit command detected for session {session_id} - resetting form state")
        form_state.fields = {}
        form_state.conversation_history = []
        form_state.timing_days_filled = []
        try:
            initial_prompt = prompt_generator.generate_initial_prompt(form_state.missing_fields)
            form_state.conversation_history.append(f"AI: {initial_prompt}")
            user_message = initial_prompt
        except ValueError:
            user_message = "Let's start fresh! Please provide the campaign name."

    # Update form fields with extracted data
    errors = {}

    # Check if extracted_data is a valid dictionary
    if extracted_data and isinstance(extracted_data, dict):
        for field_name, value in extracted_data.items():
            # Only process known fields
            if field_name in FORM_FIELDS:
                # Ensure value is not empty or invalid (like "none", "skip", etc.)
                if value and str(value).lower().strip() not in ["null", "none", "skip", "later", "n/a", "na", ""]:
                    field_config = FORM_FIELDS[field_name]

                    # Special handling for the "Timing" field
                    if field_name == "Timing" and isinstance(value, dict):
                        current_timing = form_state.fields.get("Timing", {})  # Get current stored timing info
                        out_of_range_days = []  # Track days outside the campaign period

                        # Loop over each day and time range provided
                        for day, time_range in value.items():
                            # Case 1: A specific time range is given (e.g., ["09:00-17:00"])
                            if isinstance(time_range, list) and len(time_range) == 1:
                                is_valid, error_msg = validate_time_range(time_range[0])

                                # If the day is not part of the campaign days, report error
                                if day not in campaign_days:
                                    out_of_range_days.append(day)
                                    errors[day] = f"Day '{day}' is outside the campaign period ({form_state.fields['start_date']} to {form_state.fields['end_date']})."
                                    user_message = f"Day '{day}' is outside the campaign period ({form_state.fields['start_date']} to {form_state.fields['end_date']}). Please provide timings for valid days ({', '.join(campaign_days)})."

                                # If the time range is valid, update the form state
                                elif is_valid:
                                    current_timing[day] = time_range
                                    if day not in form_state.timing_days_filled:
                                        form_state.timing_days_filled.append(day)

                                # If the time range is invalid, capture the error
                                elif error_msg:
                                    errors[day] = error_msg
                                    user_message = f"Invalid time range for {day}: {error_msg}"

                            # Case 2: Time range is marked as "default"
                            elif time_range == ["default"]:
                                # Validate if the day is within campaign range
                                if day not in campaign_days:
                                    out_of_range_days.append(day)
                                    errors[day] = f"Day '{day}' is outside the campaign period ({form_state.fields['start_date']} to {form_state.fields['end_date']})."
                                    user_message = f"Day '{day}' is outside the campaign period ({form_state.fields['start_date']} to {form_state.fields['end_date']}). Please provide timings for valid days ({', '.join(campaign_days)})."
                                else:
                                    # Use the predefined default timing from the form config
                                    current_timing[day] = FORM_FIELDS["Timing"]["default"][day]
                                    if day not in form_state.timing_days_filled:
                                        form_state.timing_days_filled.append(day)

                        # Update the form state with new or modified timing
                        form_state.fields["Timing"] = current_timing

                        # Update user_message if there were out-of-range days
                        if out_of_range_days:
                            return ChatResponse(
                                response=user_message,
                                fields=form_state.fields,
                                session_id=session_id,
                                errors=errors,
                                warning={},
                                current_field=extracted_current_field_name,
                                next_field=extracted_next_field_name,
                                is_complete=form_state.is_complete,
                                missing_fields=form_state.missing_fields,
                                ai_provider=llm_client.get_status()["ai_provider"],
                                model_name=llm_client.get_status()["model_name"],
                                session_timeoutin=SESSION_TIMEOUT
                            )
                    elif field_config.get("type") == "enum" and "values" in field_config:
                        if value not in field_config["values"]:
                            continue
                        form_state.fields[field_name] = value
                    elif field_config.get("type") == "list":
                        current_value = form_state.fields.get(field_name, []) or []
                        if isinstance(value, list):
                            current_value.extend([v for v in value if v not in current_value])
                        else:
                            if value not in current_value:
                                current_value.append(value)
                        form_state.fields[field_name] = current_value
                    else:
                        form_state.fields[field_name] = value
                    if field_name == "media_type" and combined_media_urls:
                        form_state.fields["media_urls"] = combined_media_urls

    # Address fields handling (transient flag: address_got)
    address_fields = ["targeting_type", "country", "state", "city", "Street","radius"]
    address_got_flag = False
    
    # Check if any address field was updated in this request
    address_field_updated = False
    if extracted_data and isinstance(extracted_data, dict):
        for field_name in address_fields:
            if field_name in extracted_data:
                address_field_updated = True
                break

    # Check if targeting_type is location and all address fields are filled
    if form_state.fields.get("targeting_type") == "location":
        if all(form_state.fields.get(field) for field in address_fields[1:]):  # skip targeting_type itself
            if not form_state.address_sent or address_field_updated:
                address_got_flag = True
                form_state.address_sent = True  # prevent repeat sends
        else:
            form_state.address_sent = False  # reset if any required field becomes empty
    else:
        form_state.address_sent = False  # reset if not targeting_type=location

    # Handle landingpage_url if extracted from user input
    if extracted_landingpage_url and next_field == "landingpage_url":
        if not extracted_landingpage_url.startswith(("http://", "https://")):
            extracted_landingpage_url = "https://" + extracted_landingpage_url
        form_state.fields["landingpage_url"] = extracted_landingpage_url
        if extracted_advertiser_domain:
            form_state.fields["advertiser_domain"] = extracted_advertiser_domain
    
    if extracted_advertiser_domain and not form_state.fields.get("advertiser_domain"):
        # Suggest confirmation if advertiser domain is newly extracted and not yet confirmed
        user_message = f"We detected **{extracted_advertiser_domain}** as your advertiser domain. Can you please confirm if this is correct?"
        form_state.fields["advertiser_domain"] = extracted_advertiser_domain
        form_state.conversation_history.append(f"AI: {user_message}")

    
    # Update conversation history with clean user message
    if not should_exit:
        form_state.conversation_history.append(f"AI: {user_message}")
    
    # Update session
    sessions[session_id] = session_data
    
    # Get LLM status for response
    llm_status = llm_client.get_status()
    
    # Add 'address_got' to ChatResponse and reset after sending
    response_data = ChatResponse(
        response=user_message,
        fields=form_state.fields,
        session_id=session_id,
        errors=errors,
        warning={"landingpage_url": warn} if warn else {},
        current_field=extracted_current_field_name,
        next_field=extracted_next_field_name,
        is_complete=form_state.is_complete,
        missing_fields=form_state.missing_fields,
        ai_provider=llm_status["ai_provider"],
        model_name=llm_status["model_name"],
        session_timeoutin=SESSION_TIMEOUT
    )

    # Dynamically inject 'address_got' for one-time flag
    response_data_dict = response_data.dict()
    response_data_dict["address_got"] = address_got_flag
    return ChatResponse(**response_data_dict)


if __name__ == "__main__":
    import uvicorn
    
    PORT = int(os.getenv("PORT", "9999"))
    uvicorn.run(app, host="0.0.0.0", port=PORT)