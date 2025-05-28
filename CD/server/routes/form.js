const express = require('express');
const router = express.Router();
const verifyToken = require('../middleware/auth');

// Get form fields definition
router.get('/fields', (req, res) => {
  // Complete form fields based on the provided structure
  const formFields = {
    // Basic Campaign Information
    "campaign_name": {
      "required": true,
      "type": "string",
      "description": "Enter a unique name for your campaign"
    },
    "account": {
      "required": true,
      "type": "string",
      "description": "Enter an account name associated with this campaign"
    },
    "start_date": {
      "required": true,
      "type": "string",
      "description": "Start date of the campaign (YYYY-MM-DD)"
    },
    "end_date": {
      "required": true,
      "type": "string",
      "description": "End date of the campaign (YYYY-MM-DD)"
    },
    "campaign_description": {
      "required": false,
      "type": "string",
      "description": "Brief description of your campaign"
    },

    // Network and Goals
    "network": {
      "required": true,
      "type": "enum",
      "values": ["geoad", "facebook", "instagram", "tiktok", "google", "youtube", "snapchat", "twitter"],
      "description": "Select the network for your campaign"
    },
    "campaign_goal": {
      "required": true,
      "type": "enum",
      "values": ["reach", "awareness", "high_ctr", "visit", "conversion", "app_install", "lead_generation", "engagement"],
      "description": "Select the primary goal of your campaign"
    },
    "secondary_goal": {
      "required": false,
      "type": "enum",
      "values": ["brand_awareness", "traffic", "engagement", "app_promotion", "lead_generation", "sales"],
      "description": "Select a secondary goal (optional)"
    },

    // Targeting Settings
    "targeting_type": {
      "required": true,
      "type": "enum",
      "values": ["location", "poi", "audience", "ip_targeting", "re_targeting", "dynamic_audience"],
      "description": "Select how you want to target your campaign"
    },
    "iab_category": {
      "required": true,
      "type": "enum",
      "values": ["automotive", "business", "education", "entertainment", "finance", "food_drink", "health", "hobbies", "home", "lifestyle", "news", "shopping", "sports", "technology", "travel"],
      "description": "Select the most suitable IAB category that resembles your campaign"
    },
    "target_device_type": {
      "required": true,
      "type": "enum",
      "values": ["mobile", "desktop", "tablet", "ott_ctv", "mobile+desktop", "all_devices"],
      "description": "Select the devices you want to target"
    },
    "target_os": {
      "required": false,
      "type": "enum",
      "values": ["android", "ios", "windows", "macos", "all"],
      "description": "Select operating systems to target"
    },
    "media_type": {
      "required": true,
      "type": "enum",
      "values": ["image", "video", "carousel", "collection", "story", "js_html"],
      "description": "Select the type of media for your ads"
    },
    "age_range": {
      "required": false,
      "type": "string",
      "description": "Target age range (e.g., 18-35)"
    },
    "gender": {
      "required": false,
      "type": "enum",
      "values": ["all", "male", "female", "other"],
      "description": "Target gender"
    },
    "language": {
      "required": false,
      "type": "string",
      "description": "Target language(s)"
    },

    // Pricing and Budget
    "pricing_type": {
      "required": true,
      "type": "enum",
      "values": ["cpm", "cpc", "cpa", "cpi"],
      "description": "Select the pricing model for your campaign"
    },
    "impression_count": {
      "required": false,
      "type": "number",
      "min_value": 2500,
      "description": "Enter the total number of ad views to be delivered (minimum 2500)"
    },
    "budget": {
      "required": true,
      "type": "number",
      "min_value": 50,
      "description": "Enter your campaign budget (minimum $50)"
    },
    "daily_budget": {
      "required": false,
      "type": "number",
      "min_value": 5,
      "description": "Daily budget cap (optional)"
    },
    "bid_amount": {
      "required": false,
      "type": "number",
      "min_value": 0.01,
      "description": "Bid amount for CPC/CPM campaigns"
    },

    // Additional Settings
    "advertiser_domain": {
      "required": true,
      "type": "string",
      "description": "URL associated with your advertiser"
    },
    "partner_campaign_id": {
      "required": false,
      "type": "string",
      "description": "If you have a partner campaign ID you can enter here"
    },
    "max_impressions_per_user_per_day": {
      "required": false,
      "type": "number",
      "min_value": 1,
      "description": "Maximum number of times the ad is displayed to a user every day"
    },
    "deliver_to_completion": {
      "required": false,
      "type": "boolean",
      "default": false,
      "description": "Ensure that the impression count is delivered even after campaign end date"
    },
    "frequency_cap": {
      "required": false,
      "type": "number",
      "min_value": 1,
      "description": "Maximum number of times to show ad to the same user"
    },

    // Location-based fields (dependent on targeting_type)
    "radius": {
      "required": false,
      "type": "number",
      "min_value": 0.1,
      "max_value": 100,
      "depends_on": {"targeting_type": "location"},
      "description": "Enter radius for location targeting (0.1 to 100 miles)"
    },
    "country": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "location"},
      "description": "Enter country for location targeting"
    },
    "state": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "location"},
      "description": "Enter state for location targeting"
    },
    "city": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "location"},
      "description": "Enter city for location targeting"
    },
    "zip_code": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "location"},
      "description": "Enter ZIP code for location targeting"
    },
    "dma": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "location"},
      "description": "Enter Designated Market Area for targeting"
    },

    // POI targeting fields
    "poi_brands": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "poi"},
      "description": "Enter brand locations to target based on visitor behavior"
    },
    "poi_categories": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "poi"},
      "description": "Enter categories of places to target"
    },
    "poi_visit_frequency": {
      "required": false,
      "type": "enum",
      "values": ["frequent", "occasional", "rare"],
      "depends_on": {"targeting_type": "poi"},
      "description": "Select visit frequency for POI targeting"
    },

    // Audience targeting fields
    "audience_type": {
      "required": false,
      "type": "enum",
      "values": ["iab_category", "custom", "third_party", "lookalike"],
      "depends_on": {"targeting_type": "audience"},
      "description": "Select the type of audience to target"
    },
    "audience_interest": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "audience", "audience_type": "custom"},
      "description": "Enter interests for custom audience targeting"
    },
    "audience_behavior": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "audience", "audience_type": "custom"},
      "description": "Enter behaviors for custom audience targeting"
    },

    // IP Targeting fields
    "street_address": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "ip_targeting"},
      "description": "Enter street address for IP targeting"
    },
    "ip_list": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "ip_targeting"},
      "description": "Enter comma-separated list of IP addresses to target"
    },

    // Retargeting fields
    "previous_campaign_id": {
      "required": false,
      "type": "string",
      "depends_on": {"targeting_type": "re_targeting"},
      "description": "Enter the ID of the previous campaign to retarget users"
    },
    "retargeting_days": {
      "required": false,
      "type": "number",
      "min_value": 1,
      "max_value": 180,
      "depends_on": {"targeting_type": "re_targeting"},
      "description": "Number of days to retarget users (1-180)"
    },

    // Dynamic Audience fields
    "dynamic_audience_type": {
      "required": false,
      "type": "enum",
      "values": ["device", "ip_address", "browser_cookie"],
      "depends_on": {"targeting_type": "dynamic_audience"},
      "description": "Select the basis for dynamic audience creation"
    },
    "dynamic_audience_refresh": {
      "required": false,
      "type": "enum",
      "values": ["daily", "weekly", "monthly"],
      "depends_on": {"targeting_type": "dynamic_audience"},
      "description": "How often to refresh the dynamic audience"
    },
    
    // Creative Assets
    "ad_headline": {
      "required": false,
      "type": "string",
      "description": "Main headline for your advertisement"
    },
    "ad_description": {
      "required": false,
      "type": "string",
      "description": "Description text for your advertisement"
    },
    "call_to_action": {
      "required": false,
      "type": "enum",
      "values": ["learn_more", "shop_now", "sign_up", "download", "contact_us", "book_now", "get_offer"],
      "description": "Call to action button text"
    },
    "landing_page_url": {
      "required": false,
      "type": "string",
      "description": "URL where users will be directed after clicking"
    }
  };
  
  res.json(formFields);
});

// Get user's form data
router.get('/', verifyToken, (req, res) => {
  const forms = req.app.locals.forms;
  const userForm = forms.find(form => form.userId === req.user.id);
  
  if (!userForm) {
    return res.json({ formData: {} });
  }
  
  res.json({ formData: userForm.data });
});

// Save form data
router.post('/', verifyToken, (req, res) => {
  try {
    const { formData } = req.body;
    const forms = req.app.locals.forms;
    
    // Find if user already has a form
    const formIndex = forms.findIndex(form => form.userId === req.user.id);
    
    if (formIndex !== -1) {
      // Update existing form
      forms[formIndex].data = { ...forms[formIndex].data, ...formData };
    } else {
      // Create new form
      forms.push({
        userId: req.user.id,
        data: formData
      });
    }
    
    res.status(200).json({ message: 'Form data saved successfully' });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

module.exports = router;