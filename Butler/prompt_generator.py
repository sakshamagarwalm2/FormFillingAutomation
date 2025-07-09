from typing import Dict, Optional, List, Union
from datetime import datetime, timedelta
import json
from form_config import FORM_FIELDS, DEPENDENCY_RULES

class PromptGenerator:
    """Handles all prompt generation for the form filling assistant"""
    
    def __init__(self):
        self.current_year = datetime.now().date().strftime("%d-%m-%Y")
        self.days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    def _calculate_campaign_days(self, start_date: str, end_date: str) -> List[str]:
        """Calculate unique days of the week between start_date and end_date"""
        try:
            start = datetime.strptime(start_date, "%d-%m-%Y")
            end = datetime.strptime(end_date, "%d-%m-%Y")
            delta = (end - start).days + 1
            
            unique_days = []
            for i in range(min(delta, 7)):
                day = (start + timedelta(days=i)).strftime("%A")
                if day not in unique_days:
                    unique_days.append(day)
            
            return unique_days if unique_days else self.days_of_week
        except ValueError:
            return self.days_of_week
    
    def generate_initial_prompt(self, missing_fields: list) -> str:
        """Generate initial prompt for the LLM based on missing fields"""
        if not missing_fields:
            return "✅ All required fields are complete! Ready to review your form."
        
        next_field = missing_fields[0]
        
        if next_field not in FORM_FIELDS:
            raise ValueError(f"Field {next_field} not found in FORM_FIELDS")
            
        field_config = FORM_FIELDS[next_field]
        
        # Create concise, friendly opening
        prompt = f"Let's get started! First, I need your **{next_field.replace('_', ' ')}**."
        
        # Add description if available
        if field_config.get('description'):
            prompt += f"\n\n{field_config['description']}"
        
        # Add options in a clean format
        if "values" in field_config and field_config["values"]:
            options = field_config["values"]
            if len(options) <= 3:
                prompt += f"\n\nChoose from: **{' | '.join(options)}**"
            else:
                prompt += f"\n\nOptions:\n" + "\n".join([f"• {opt}" for opt in options])
        
        return prompt
    
    def _get_current_field_info(self, field_name: str) -> Dict[str, Union[str, List[str]]]:
        """Get detailed information about the current field"""
        if field_name not in FORM_FIELDS:
            return {}
            
        config = FORM_FIELDS[field_name]
        field_info = {
            "field_name": field_name,
            "description": config.get("description", ""),
            "type": config.get("type", "text"),
        }
        
        if config.get("type") == "enum" and "values" in config:
            field_info["allowed_values"] = config["values"]
        if "default" in config:
            field_info["default"] = config["default"]
            
        return field_info
    
    def _format_user_friendly_prompt(self, field_name: str, field_info: Dict) -> str:
        """Format a user-friendly prompt for a specific field"""
        display_name = field_name.replace('_', ' ').title()
        
        # Base question
        prompt = f"What's your **{display_name}**?"
        
        # Add description if helpful
        if field_info.get('description') and len(field_info['description']) < 100:
            prompt += f"\n\n{field_info['description']}"
        
        # Handle options elegantly
        if field_info.get('allowed_values'):
            options = field_info['allowed_values']
            if len(options) <= 4:
                prompt += f"\n\nOptions: **{' | '.join(options)}**"
            else:
                prompt += f"\n\nChoose from:\n" + "\n".join([f"• {opt}" for opt in options])
        
        # Show default if available
        if field_info.get('default'):
            prompt += f"\n\n💡 Default: **{field_info['default']}**"
        
        return prompt
    
    def generate_iab_classification_prompt(self, media_urls: List[str], media_type: str) -> str:
        """Generate prompt for classifying media into IAB category and ID"""
        json_format = '''[
        {
            "url": "string",
            "iab_category": "string", 
            "iab_id": "string"
        }
        ]'''
        
        urls_text = "\n".join([f"- {url}" for url in media_urls])
    
        return f"""You are a chat assistant AI tasked with classifying the provided media URLs into IAB categories and IDs.
            The media type is '{media_type}' for all URLs.            
            Analyze each URL and its content to classify into the most appropriate IAB category and provide the corresponding IAB ID.
            URLs to analyze:
            {urls_text}            
            Return the result as a JSON array in the following format:
            {json_format}            
            Only return the JSON array, nothing else."""
    
    def generate_timing_prompt(self, form_fields: Dict[str, Optional[Union[str, List[str]]]], missing_fields: List[str]) -> str:
        """Generate prompt for collecting daily timing schedules"""
        if "start_date" not in form_fields or "end_date" not in form_fields:
            return ""
        
        campaign_days = self._calculate_campaign_days(form_fields["start_date"], form_fields["end_date"])
        default_timing = FORM_FIELDS["Timing"]["default"]
        json_format = '''{
            "day": ["start_hour-end_hour"]
        }'''

        prompt_parts = [
            "You can optionally set the daily schedule for your campaign's ad display.",
            f"The campaign runs from {form_fields['start_date']} to {form_fields['end_date']}, covering these days: {', '.join(campaign_days)}.",
            "",
            "**IMPORTANT TIMING RULES**:",
            "- Provide time range in `start_hour-end_hour` format. For example: '9-18'.",
            "- Only hour values are allowed. No AM/PM or minutes. Hours must be integers from 1 to 24.",
            f"- You can say '{default_timing}' to use '7-24' (7 AM to 12 midnight) for that day.",
            "- You can say 'skip' to skip that day's timing. It won't be added.",
            "- If no timing is provided at all, use default for **every** campaign day.",
            "- If timing is provided for days outside campaign period, ignore and inform the user.",
            "- If a single timing is mentioned with multiple days, apply to those days only if within campaign period.",
            "",
            "**FIELD VALUE HANDLING**:",
            "- Extract the timing as a JSON object in the format: <EXTRACTED>{'Timing': {'day': ['start_hour-end_hour']}}</EXTRACTED>.",
            "- Strictly ignore minutes or AM/PM formats. Only 1–24 integers are valid.",
            "- Validate that start_hour is less than end_hour, and both in 1–24 range.",
            "- If user says 'default', apply '7-24' to the relevant days.",
            "- If user says 'skip', don't extract that day.",
            "- If no input is given for some campaign days, **default must be applied to them** (no missing days).",
            "",
            f"Return the extracted timing in the following JSON format: {json_format}",
        ]
        
        return "\n".join(prompt_parts)

    
    def generate_chat_prompt(self, 
                           user_input: str,
                           form_fields: Dict[str, Optional[Union[str, List[str]]]],
                           conversation_history: List[str],
                           missing_fields: List[str],
                           media_urls: Optional[List[str]] = None,
                           media_type: Optional[str] = None) -> str:
        """Generate the main chat prompt for form processing"""
        
        # Determine next field and its details
        next_field_to_ask = missing_fields[0] if missing_fields else None
        current_field_detailed_info = {}
        
        # Check if URLs are provided
        has_media_urls = bool(media_urls)

        
        if next_field_to_ask and not has_media_urls:
            current_field_detailed_info = self._get_current_field_info(next_field_to_ask)
        
        # Build prompt parts
        prompt_parts = [
            "You are an AI assistant helping to fill out an advertising campaign form.",
            "",
            "Available form fields:",
            json.dumps({k: v.get('description', '') for k, v in FORM_FIELDS.items()}, indent=2),
            "",
        ]
        # Only trigger IAB prompt if current or next field is media_type, iab_category, or iab_id
        iab_related_fields = {"media_type", "iab_category", "iab_id"}
        relevant_field_triggered = bool(iab_related_fields & set(missing_fields[:3]))  # current + next 2

        if has_media_urls and relevant_field_triggered:
            if all(form_fields.get(f) for f in ["media_type", "iab_category", "iab_id"]):
                # Skip if already filled
                pass
            else:       
                # Handle media URLs for IAB classification
                prompt_parts.extend([
                    "The user has provided media URLs to classify.",
                    f"Media Type: {media_type or 'image'}",
                    f"Media URLs: {', '.join(media_urls)}",
                    "Your task is to:",
                    "1. Validate or infer the 'media_type' ('image', 'video', 'js_html').",
                    "2. Classify each URL's content to determine the appropriate IAB category and ID.",
                    "3. Return the extracted 'media_type', 'iab_category' (array), and 'iab_id' (array) in the EXTRACTED section.",
                    "4. In the USER_MESSAGE, confirm the IAB categories with the user and ask for the next field or if they want to proceed.",
                    "",
                    self.generate_iab_classification_prompt(media_urls, media_type or 'image'),
                    "",
                    "FIELD VALUE HANDLING FOR media URLs:",
                    "- Validate that 'media_type' is one of: ['image', 'video', 'js_html'].",
                    "- If invalid or missing, assume 'image' and extract accordingly.",
                    "- For iab_category and iab_id, append new classifications to any existing values in the form_fields arrays, ensuring no duplicates.",
                    "- If an IAB classification for a URL already exists in form_fields, skip reclassification for that URL unless explicitly requested.",
                    "",
                ])
        elif "start_date" in form_fields and "end_date" in form_fields:
            # Handle timing opportunistically if start_date and end_date are set
            timing_prompt = self.generate_timing_prompt(form_fields, missing_fields)
            if timing_prompt:
                prompt_parts.extend([
                    f"You can set the daily schedule for your campaign, which runs from {form_fields['start_date']} to {form_fields['end_date']}. and date and day should strictly exsist between this dates only",
                    timing_prompt,
                    "",
                    "Extract timing data if provided, even if it's not the current field, but only for days within the campaign period.",
                    "If timing is provided for a day outside the period, inform the user and do not extract it.",
                    f"If no timing is provided, set the default timing 7-24 (7 AM to 12 midnight) for all days in the range ({form_fields['start_date']} to {form_fields['end_date']}) and strictly do not leave any day blank set them default (7-24) focus on the next field to ask.",
                    "",
                ])
        # Suggest and explain dependency handling
        if next_field_to_ask in DEPENDENCY_RULES:
            dependency_fields = list(DEPENDENCY_RULES[next_field_to_ask].keys())
            prompt_parts.append(
                "Note: This field depends on the following fields being filled first: "
                f"{', '.join(dependency_fields)}. If the user provides information that implies any of these, extract them accordingly."
            )

        # Add reverse dependency suggestion
        # E.g., if the user says "Jaipur" -> infer targeting_type=location
        reverse_dependencies = []
        for field, deps in DEPENDENCY_RULES.items():
            for dep_field, expected_val in deps.items():
                reverse_dependencies.append((dep_field, expected_val, field))

        if reverse_dependencies:
            prompt_parts.append("DEPENDENCY INFERENCE RULES:")
            for dep_field, expected_val, child_field in reverse_dependencies:
                if expected_val:
                    prompt_parts.append(
                        f"- If the user provides or implies '{child_field}', ensure '{dep_field}' is set to '{expected_val}'"
                    )
                else:
                    prompt_parts.append(
                        f"- If the user provides or implies '{child_field}', ensure '{dep_field}' is also collected"
                    )

        if next_field_to_ask:
            prompt_parts.extend([
                f"The current field the user is expected to provide information for is '{next_field_to_ask}'.",
                "Here are its specific details (type, allowed values, default, etc.):",
                json.dumps(current_field_detailed_info, indent=2),
                
                "FIELD VALUE HANDLING:",
                f"- If this field has a '{current_field_detailed_info.get('default', '')}' value, present it as a recommendation along with other allowed_values as options. If not provided, send default value in EXTRACT and ask next field.",
                f"- If this field has '{current_field_detailed_info.get('allowed_values',[])}', extract the user's input by matching it against these allowed values (exact match or closest semantic match) and show exactly same options.Example: if user say insta itmeans Facebook+Instagram.",
                f"- For enum fields, guide the user to choose from the {current_field_detailed_info.get('allowed_values',[])} exactly this options to show. If the user provides a value not in the list, respond with a USER_MESSAGE asking them to choose from the available options.",
                "- For 'landingpage_url', ensure the input is a valid domain (e.g., example.com, www.example.com, https://example.com) and not an image or video URL. The domain must be resolvable (exists via DNS). If invalid, respond with a USER_MESSAGE asking for a valid domain and do not extract it.",
                "",
                "Prioritize guiding the user to provide information for this specific field.",
                "However, if the user provides information for *other* fields (even if not the current focus), extract that information, including timing if valid.",
                "If the user provides a URL, check if it's meant for 'landingpage_url' (e.g., 'my website is example.com') or a media URL (e.g., 'image: example.com/image.jpg' or 'video: youtu.be/video').",
                "If the user indicates they want to 'skip' or 'do it later' for the current field, acknowledge that and move to the next logical step (e.g., ask for the next missing field).",
                "",
            ])
        else:
            prompt_parts.extend([
                "All required fields have been filled. The user might be reviewing or ready to submit.",
                "Confirm completion of all fields or ask if they want to review/submit the form if next field is available then ask for it.",
                "",
            ])

        prompt_parts.extend([
            "Current conversation history:",
            json.dumps(conversation_history[-5:], indent=2),
            "",
            "Current form state:",
            json.dumps(form_fields, indent=2),
            "",
            "User's latest message:",
            user_input,
            "",
        ])
        
        # Add response format instructions
        prompt_parts.extend(self._get_response_format_instructions(next_field_to_ask))
        
        return "\n".join(prompt_parts)
    
    def _get_response_format_instructions(self, next_field_to_ask: Optional[str]) -> List[str]:
        """Get the response format instructions for the LLM"""
        field_details = self._get_current_field_info(next_field_to_ask) if next_field_to_ask else {}
        return [
            "CRITICAL INSTRUCTIONS:",
            "You must structure your response in exactly 3 sections:",
            "",
            "1. USER_MESSAGE: The main response to show the user (conversational, helpful, guiding)",
            "2. EXTRACTED: JSON format for any field values you extract: <EXTRACTED>{\"field_name\": \"value\"}</EXTRACTED>",
            "3. NEXT_FIELD_NAME: The name of the field the AI is currently prompting the user for. If all fields are complete, output 'None'. Example: <NEXT_FIELD_NAME>campaign_name</NEXT_FIELD_NAME>",
            "4. CUR_FIELD: The name of the current field being asked for. Example: <CUR_FIELD>{next_field_to_ask if next_field_to_ask else 'None'}</CUR_FIELD>",
            "5. EXIT: If the user wants to exit, reset, restart, kill, start over, end the session, new conversation or anything meaning similar to exit (interpret contextually), first ask for confirmation and respond with the tag <EXIT>exit</EXIT>. Otherwise, do not include this tag in your response.",
            "",
            "USER_MESSAGE FORMATTING RULES:",
            "- Keep responses SHORT and ENGAGING (2-3 sentences max for questions)",
            "- Use bullet points for options when there are 3+ choices",
            "- Use **bold** for important terms and options",
            "- Use emojis sparingly but effectively (✅ ❌ 💡 🎯)",
            "- Break long explanations into digestible chunks",
            "- Ask ONE clear question at a time",
            "",
            "EXAMPLES OF GOOD USER_MESSAGE FORMAT in proper md formate:",
            "✅ GOOD: 'What's your main **Campaign Objective**?\n'",
            "Options:\n",
            "• Brand Awareness\n",
            "• Lead Generation \n ",
            "• Website Traffic\n",
            "• Sales\n",
            "",
            "WHEN TO EXTRACT:",
            "- EXTRACT: When user provides clear field information (names, dates, accounts, etc.) for *any* available field.",
            f"- For fields with '{field_details.get('allowed_values',[])}': Match user input to the closest allowed value from the list.",
            f"- For fields with '{field_details.get('default', '')}' values: If user says 'default', 'recommended', or similar, use the default value.",
            "- For media_type, iab_category, and iab_id: If media_urls are provided, classify the content and extract all three fields together, appending new values to existing iab_category and iab_id lists without duplicates.",
            "- For Timing: Extract as a JSON object {'day': ['start_hour-end_hour']} if provided (e.g., {'Monday': ['8-16']}), only if the day exists in the campaign period and the time is valid (1–24 only). If missing or invalid, use '7-24' for all days. Do not use minutes or AM/PM.",
            "",
            "RESPONSE FORMAT:",
            "[Your SHORT conversational response to user]",
            "",
            "<EXTRACTED>{\"field_name\": \"value\"}</EXTRACTED>",
            f"<NEXT_FIELD_NAME>{next_field_to_ask if next_field_to_ask else 'None'}</NEXT_FIELD_NAME>",
            f"<CUR_FIELD>{next_field_to_ask if next_field_to_ask else 'None'}</CUR_FIELD>",
            "<EXIT>exit</EXIT>",
            "",
            "EXIT HANDLING:",
            "If the user says anything that indicates they want to exit, reset, restart, end the session, or start a new conversation (e.g., start over, reset, restart, kill the session, new chat, etc.), then:",
            "- First, ask: 'Are you sure you want to exit?'",
            "- If the user confirms, respond with:<EXIT>exit</EXIT>",
            "- and absolutely NOTHING else. Do NOT include any user message, greeting, instruction, or next prompt.",
            "- Do NOT extract any fields or continue the form until the user explicitly confirms they want to exit.",
            "",
            f"Current date is {self.current_year}. All dates should be in the future and date cannot be in the past.",
            "Keep responses short, direct, and conversational.",
            f"If options are provided as values strictly give output from them only and extract value based on the options in '{field_details.get('allowed_values',[])}'.",
            f"If a field like 'city', 'state', or 'zip_code' is provided, assume the user intends 'targeting_type' to be 'location'. Extract this dependency accordingly. and set other fields like 'country', 'state', 'city', 'zip_code' and 'Street , etc if extraction is possible. '{DEPENDENCY_RULES}'",
            "While confirming about iab_category make current field as <CUR_FIELD>iab_category</CUR_FIELD>",
            "For Timing, accept input opportunistically if provided, validating against the campaign period and 1-24 range.",
            "If you don't understand the user's input, ask for clarification while asking for the next field.",
            "Don't ask for confirmation or validation of the extracted data if it is clear. Just extract and move on.",
            "Ask for conformation befor exit and do not exit without user confirmation.",
            "PRIORITIZE BREVITY AND CLARITY IN USER_MESSAGE - users prefer quick, focused interactions over lengthy explanations.",
        ]