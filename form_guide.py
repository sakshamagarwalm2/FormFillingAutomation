# form_guide.py
# Defines the structure of the advertising campaign form with fields, requirements, types, and dependencies

FORM_FIELDS = {
    # Basic Campaign Information
    "campaign_name": {
        "required": True,
        "type": "string",
        "description": "Enter a unique name for your campaign"
    },
    "account": {
        "required": True,
        "type": "string",
        "description": "Enter an account name associated with this campaign"
    },

    # Network and Goals
    "network": {
        "required": True,
        "type": "enum",
        "values": ["geoad", "facebook+instagram"],
        "description": "Select the network for your campaign"
    },
    "campaign_goal": {
        "required": True,
        "type": "enum",
        "values": ["reach", "awareness", "high_ctr", "visit"],
        "description": "Select the primary goal of your campaign"
    },

    # Targeting Settings
    "targeting_type": {
        "required": True,
        "type": "enum",
        "values": ["location", "poi", "audience", "ip_targeting", "re_targeting", "dynamic_audience"],
        "description": "Select how you want to target your campaign"
    },
    "iab_category": {
        "required": True,
        "type": "string",
        "description": "Select the most suitable IAB category that resembles your campaign"
    },
    "target_device_type": {
        "required": True,
        "type": "enum",
        "values": ["mobile", "desktop", "ott_ctv", "mobile+desktop"],
        "description": "Select the devices you want to target"
    },
    "media_type": {
        "required": True,
        "type": "enum",
        "values": ["image", "video", "js_html"],
        "description": "Select the type of media for your ads"
    },

    # Pricing and Budget
    "pricing_type": {
        "required": True,
        "type": "enum",
        "values": ["cpm"],
        "description": "Select the pricing model for your campaign"
    },
    "impression_count": {
        "required": True,
        "type": "number",
        "min_value": 2500,
        "description": "Enter the total number of ad views to be delivered (minimum 2500)"
    },
    "budget": {
        "required": False,  # Alternative to impression_count via toggle
        "type": "number",
        "min_value": 0,
        "description": "Enter your campaign budget (alternative to impression count)"
    },

    # Additional Settings
    "advertiser_domain": {
        "required": True,
        "type": "string",
        "description": "URL associated with your advertiser"
    },
    "partner_campaign_id": {
        "required": False,
        "type": "string",
        "description": "If you have a partner campaign ID you can enter here"
    },
    "max_impressions_per_user_per_day": {
        "required": False,
        "type": "number",
        "min_value": 1,
        "description": "Maximum number of times the ad is displayed to a user every day"
    },
    "deliver_to_completion": {
        "required": False,
        "type": "boolean",
        "default": False,
        "description": "Ensure that the impression count is delivered even after campaign end date"
    },

    # Location-based fields (dependent on targeting_type)
    "radius": {
        "required": False,
        "type": "number",
        "min_value": 0.1,
        "max_value": 100,
        "depends_on": {"targeting_type": "location"},
        "description": "Enter radius for location targeting (0.1 to 100 miles)"
    },
    "country": {
        "required": False,
        "type": "string",
        "depends_on": {"targeting_type": "location"},
        "description": "Enter country for location targeting"
    },
    "state": {
        "required": False,
        "type": "string",
        "depends_on": {"targeting_type": "location"},
        "description": "Enter state for location targeting"
    },
    "city": {
        "required": False,
        "type": "string",
        "depends_on": {"targeting_type": "location"},
        "description": "Enter city for location targeting"
    },
    "zip_code": {
        "required": False,
        "type": "string",
        "depends_on": {"targeting_type": "location"},
        "description": "Enter ZIP code for location targeting"
    },
    "dma": {
        "required": False,
        "type": "string",
        "depends_on": {"targeting_type": "location"},
        "description": "Enter Designated Market Area for targeting"
    },

    # POI targeting fields
    "poi_brands": {
        "required": False,
        "type": "string",
        "depends_on": {"targeting_type": "poi"},
        "description": "Enter brand locations to target based on visitor behavior"
    },

    # Audience targeting fields
    "audience_type": {
        "required": False,
        "type": "enum",
        "values": ["iab_category", "custom", "third_party"],
        "depends_on": {"targeting_type": "audience"},
        "description": "Select the type of audience to target"
    },

    # IP Targeting fields
    "street_address": {
        "required": False,
        "type": "string",
        "depends_on": {"targeting_type": "ip_targeting"},
        "description": "Enter street address for IP targeting"
    },

    # Retargeting fields
    "previous_campaign_id": {
        "required": False,
        "type": "string",
        "depends_on": {"targeting_type": "re_targeting"},
        "description": "Enter the ID of the previous campaign to retarget users"
    },

    # Dynamic Audience fields
    "dynamic_audience_type": {
        "required": False,
        "type": "enum",
        "values": ["device", "ip_address"],
        "depends_on": {"targeting_type": "dynamic_audience"},
        "description": "Select the basis for dynamic audience creation"
    }
}