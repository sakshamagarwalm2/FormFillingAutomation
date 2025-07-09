from typing import Dict, Any

FORM_FIELDS = {
    "campaign_name": {
        "required": True,
        "type": "string",
        "description": "Enter a unique name for your campaign",
    },
    "account": {
        "required": True,
        "type": "string",
        "description": "Enter an account name associated with this campaign"
    },
    "media_type": {
        "required": True,
        "type": "enum",
        "values": ["image", "video", "js_html"],
        "description": "Select the type of media for your ads"
    },
    "iab_category": {
        "required": True,
        "type": "list",
        "description": "Select one or more IAB categories that resemble your campaign",
        "item_type": "string"
    },
    "iab_id": {
        "required": False,
        "type": "list",
        "description": "Enter one or more IAB IDs for your campaign",
        "item_type": "string"
    },
    "start_date": {
        "required": True,
        "type": "string",
        "description": "Start date of the campaign (DD-MM-YYYY)"
    },
    "end_date": {
        "required": True,
        "type": "string",
        "description": "End date of the campaign (DD-MM-YYYY)"
    },
    "Timing": {
        "required": True,
        "type": "json",
        "description": "Daily schedule for the campaign in the format {'day': ['start_hour-end_hour']} using 1–24 hour format. Example: {'Monday': ['7-24']}",
        "default": {
            "Monday": ["7-24"],
            "Tuesday": ["7-24"],
            "Wednesday": ["7-24"],
            "Thursday": ["7-24"],
            "Friday": ["7-24"],
            "Saturday": ["7-24"],
            "Sunday": ["7-24"]
        },
        "depends_on": {"start_date": None, "end_date": None}
    },
    "landingpage_url": {
        "required": True,
        "type": "string",
        "description": "URL associated with your advertiser"
    },
    "advertiser_domain": {
        "required": False,
        "type": "string",
        "description": "Domain of the advertiser for this campaign",
        "default": ""
    },
    "network": {
        "required": True,
        "type": "enum",
        "values": ["Geoad", "Facebook + Instagram"],
        "description": "Select the network for your campaign",
        "default": "Geoad"
    },
    "campaign_goal": {
        "required": True,
        "type": "enum",
        "values": ["reach", "awareness", "high_ctr", "visit"],
        "description": "Select the primary goal of your campaign"
    },
    "targeting_type": {
        "required": True,
        "type": "enum",
        "values": ["location", "poi"],
        "description": "Select how you want to target your campaign"
    },
    "country": {
        "required": True,
        "type": "string",
        "depends_on": {"targeting_type": "location"},
        "description": "Enter country for location targeting"
    },
    "state": {
        "required": True,
        "type": "string",
        "depends_on": {"targeting_type": "location"},
        "description": "Enter state for location targeting"
    },
    "city": {
        "required": True,
        "type": "string",
        "depends_on": {"targeting_type": "location"},
        "description": "Enter city for location targeting"
    },
    "Street":{
        "required": True,
        "type": "string",
        "depends_on": {"targeting_type": "location"},
        "description": "Enter street address for location targeting"
    },
    "radius": {
        "required": True,
        "type": "number",
        "min_value": 0.1,
        "max_value": 100,
        "depends_on": {"targeting_type": "location"},
        "description": "Enter radius for location targeting (0.1 to 100 miles)",
        "default": 5
    },
    "zip_code": {
        "required": True,
        "type": "string",
        "depends_on": {"targeting_type": "location"},
        "description": "Enter ZIP code for location targeting",
        "default": ""
    },
    "dma": {
        "required": True,
        "type": "string",
        "depends_on": {"targeting_type": "location"},
        "description": "Enter Designated Market Area for targeting",
        "default": ""
    },
    "target_device_type": {
        "required": True,
        "type": "enum",
        "values": ["mobile", "desktop", "ott_ctv", "mobile+desktop"],
        "description": "Select the devices you want to target"
    },
    "budget": {
        "required": True,
        "type": "number",
        "min_value": 50,
        "description": "Enter your campaign budget (minimum $50)"
    },
    "billing_type": {
        "required": True,
        "type": "enum",
        "values": ["recurring", "non_recurring"],
        "description": "Select the billing type for your campaign",
        "default": "non_recurring"
    },
    # "partner_campaign_id": {
    #     "required": True,
    #     "type": "string",
    #     "description": "If you have a partner campaign ID you can enter here",
    #     "default": ""
    # },
    # "pricing_type": {
    #     "required": True,
    #     "type": "enum",
    #     "values": ["cpm"],
    #     "description": "Select the pricing model for your campaign",
    #     "default": "cpm"
    # },
    "max_impressions_per_user_per_day": {
        "required": True,
        "type": "number",
        "min_value": 1,
        "description": "Maximum number of times the ad is displayed to a user every day",
        "default": 5
    },
    # "poi_brands": {
    #     "required": True,
    #     "type": "string",
    #     "depends_on": {"targeting_type": "poi"},
    #     "description": "Enter brand locations to target based on visitor behavior",
    #     "default": ""
    # },
    # "poi_categories": {
    #     "required": True,
    #     "type": "string",
    #     "depends_on": {"targeting_type": "poi"},
    #     "description": "Enter categories of places to target",
    #     "default": ""
    # },
    # "poi_visit_frequency": {
    #     "required": True,
    #     "type": "enum",
    #     "values": ["frequent", "occasional", "rare"],
    #     "depends_on": {"targeting_type": "poi"},
    #     "description": "Select visit frequency for POI targeting",
    #     "default": "frequent"
    # },
    "trafic_type": {
        "required": True,
        "type": "enum",
        "values": ["Web", "App"],
        "description": "Select the traffic type for your campaign",
        "default": "Web"
    },
    "gender": {
        "required": True,
        "type": "enum",
        "values": ["male", "female"],
        "description": "Select the gender for your campaign",
        "default": "male"
    },
    "language": {
        "required": True,
        "type": "enum",
        "values": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Russian", "Chinese", "Japanese", "Korean", "Hindi"],
        "description": "Select the language for your campaign",
        "default": "English"
    },
    "os": {
        "required": True,
        "type": "enum",
        "values": ["iOS", "Android", "Other"],
        "description": "Select the OS for your campaign",
        "default": "Android"
    },
    "age": {
        "required": True,
        "type": "enum",
        "values": ["17-20", "21-30", "31-40", "41-50", "51-60", ">61"],
        "description": "Select the age range for your campaign",
        "default": "21-30"
    },
    # "audience_type": {
    #     "required": True,
    #     "type": "enum",
    #     "values": ["iab_category", "custom", "third_party", "lookalike"],
    #     "depends_on": {"targeting_type": "audience"},
    #     "description": "Select the type of audience to target",
    #     "default": "iab_category"
    # },
    # "audience_interest": {
    #     "required": True,
    #     "type": "string",
    #     "depends_on": {"targeting_type": "audience", "audience_type": "custom"},
    #     "description": "Enter interests for custom audience targeting",
    #     "default": "audience"
    # },
    # "audience_behavior": {
    #     "required": True,
    #     "type": "string",
    #     "depends_on": {"targeting_type": "audience", "audience_type": "custom"},
    #     "description": "Enter behaviors for custom audience targeting",
    #     "default": "audience"
    # },
    # "ip_list": {
    #     "required": True,
    #     "type": "string",
    #     "depends_on": {"targeting_type": "ip_targeting"},
    #     "description": "Enter comma-separated list of IP addresses to target",
    #     "default": ""
    # },
    # "previous_campaign_id": {
    #     "required": True,
    #     "type": "string",
    #     "depends_on": {"targeting_type": "re_targeting"},
    #     "description": "Enter the ID of the previous campaign to retarget users",
    #     "default": ""
    # },
    # "retargeting_days": {
    #     "required": True,
    #     "type": "number",
    #     "min_value": 1,
    #     "max_value": 180,
    #     "depends_on": {"targeting_type": "re_targeting"},
    #     "description": "Number of days to retarget users (1-180)",
    #     "default": 1
    # },
}

DEPENDENCY_RULES = {
    "country": {"targeting_type": "location"},
    "state": {"targeting_type": "location", "country": None,},
    "city": {"targeting_type": "location", "country": None, "state": None,"zip_code": None},
    "Street": {"targeting_type": "location", "country": None, "state": None, "city": None, "zip_code": None},
    "radius": {"targeting_type": "location"},
    "zip_code": {"targeting_type": "location", "country": None, "state": None, "city": None, "Street": None},
    # "dma": {"targeting_type": "location"},
    # "poi_brands": {"targeting_type": "poi"},
    # "poi_categories": {"targeting_type": "poi"},
    # "poi_visit_frequency": {"targeting_type": "poi"},
    # "audience_type": {"targeting_type": "audience"},
    # "audience_interest": {"targeting_type": "audience", "audience_type": "custom"},
    # "audience_behavior": {"targeting_type": "audience", "audience_type": "custom"},
    # "ip_list": {"targeting_type": "ip_targeting"},
    # "previous_campaign_id": {"targeting_type": "re_targeting"},
    # "retargeting_days": {"targeting_type": "re_targeting"},
    "Timing": {"start_date": None, "end_date": None}
}

def get_required_fields(filled_fields: Dict[str, Any]) -> list:
    """Return the list of required fields that are not yet filled and whose dependencies are satisfied"""
    required_fields = []

    for field_name, config in FORM_FIELDS.items():
        if not config.get("required"):
            continue  # Skip non-required fields

        # Skip already filled fields (even if partially filled)
        if field_name in filled_fields and filled_fields[field_name] not in [None, "", [], {}]:
            continue

        # Check dependency rules if present
        if field_name in DEPENDENCY_RULES:
            dependencies = DEPENDENCY_RULES[field_name]
            dependency_satisfied = True
            for dep_field, expected_value in dependencies.items():
                if expected_value is None:
                    if dep_field not in filled_fields:
                        dependency_satisfied = False
                        break
                elif filled_fields.get(dep_field) != expected_value:
                    dependency_satisfied = False
                    break
            if not dependency_satisfied:
                continue  # Don't include field if dependencies not met

        # If all conditions are met, consider this field still missing
        required_fields.append(field_name)

    return required_fields
