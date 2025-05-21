import os
import json
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains import LLMChain
from form_guide import FORM_FIELDS

# --- SETUP ---
# Initialize Streamlit session state
if "form_state" not in st.session_state:
    st.session_state.form_state = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Get Groq API key
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    groq_api_key = st.text_input("Enter your Groq API key:", type="password")
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key
    else:
        st.warning("Please enter your Groq API key to proceed.")
        st.stop()

# Initialize the Groq Llama model
llm = ChatGroq(temperature=0.4, model_name="llama3-70b-8192")

# Define the conversation prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a polite chatbot assisting users to fill an advertising form.
Extract structured data from natural language input and ensure all required fields are filled.
Form fields: {fields_info}
User's current form data: {form_state}
Missing required fields: {missing_fields}
Relevant dependent fields: {dependent_fields}

IMPORTANT:
- YOUR PRIMARY GOAL IS TO EXTRACT VALUES FOR FORM FIELDS FROM THE USER'S INPUT
- When you extract values, ONLY RESPOND WITH A JSON OBJECT containing the extracted field names and values
- Do not include explanatory text or conversation in your JSON responses
- If you cannot extract values and need to ask questions, respond with normal conversational text (not JSON)
- Validate values (e.g., enum options must match allowed values)
- If required fields are missing, politely ask for them in a natural sentence
- If dependent fields are relevant and not filled, ask for them
- Keep responses concise, natural, and conversational when not returning JSON
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{user_input}")
])

# Create the conversation chain
conversation_chain = LLMChain(llm=llm, prompt=prompt)

# --- HELPERS ---
def is_field_relevant(field):
    """Check if a field is relevant based on its dependencies."""
    field_info = FORM_FIELDS[field]
    if "depends_on" not in field_info:
        return True
    for dep_field, dep_value in field_info["depends_on"].items():
        if st.session_state.form_state.get(dep_field) != dep_value:
            return False
    return True

def get_missing_required_fields():
    """Identify required fields that haven't been filled and are relevant."""
    return [
        field for field, props in FORM_FIELDS.items()
        if props["required"] and field not in st.session_state.form_state and is_field_relevant(field)
    ]

def get_relevant_dependent_fields():
    """Identify non-required, relevant dependent fields that haven't been filled."""
    return [
        field for field, props in FORM_FIELDS.items()
        if not props["required"] and field not in st.session_state.form_state and is_field_relevant(field)
    ]

def validate_extracted_fields(extracted):
    """Validate extracted field values against field definitions."""
    validated = {}
    issues = []

    for field, value in extracted.items():
        if field in FORM_FIELDS:
            field_info = FORM_FIELDS[field]
            if not is_field_relevant(field):
                continue

            # Validate enum values
            if field_info["type"] == "enum" and value not in field_info["values"]:
                issues.append(f"Invalid value '{value}' for {field}. Choose from: {', '.join(field_info['values'])}")
                continue

            # Validate number fields
            if field_info["type"] == "number":
                try:
                    value = float(value)
                    if "min_value" in field_info and value < field_info["min_value"]:
                        issues.append(f"Value for {field} must be at least {field_info['min_value']}")
                    if "max_value" in field_info and value > field_info["max_value"]:
                        issues.append(f"Value for {field} must not exceed {field_info['max_value']}")
                except ValueError:
                    issues.append(f"Invalid number format for {field}")
                    continue

            validated[field] = value

    if issues:
        return False, "\n".join(issues)
    return True, validated

def format_fields_info():
    """Format field definitions for the prompt."""
    return json.dumps(FORM_FIELDS, indent=2)

def is_json(text):
    """Check if a string is valid JSON."""
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

# --- STREAMLIT UI ---
st.title("AI Form-Filling Chatbot")
st.write("Talk naturally to fill out your advertising campaign form.")

# Sidebar to display form state
with st.sidebar:
    st.header("Current Form State")
    if st.session_state.form_state:
        st.json(st.session_state.form_state)
    else:
        st.write("No fields filled yet.")

# Chat interface
st.header("Chat with the Assistant")
if not st.session_state.chat_history:
    st.session_state.chat_history.append(AIMessage(content="Hi! I'll help you fill out your ad form. Please provide details about your ad campaign like campaign name, network, goal, and targeting preferences."))

# Display chat history
for message in st.session_state.chat_history:
    if isinstance(message, HumanMessage):
        st.write(f"**You**: {message.content}")
    else:
        st.write(f"**AI**: {message.content}")

# User input
user_input = st.text_input("Your message:", key="user_input")
if st.button("Send"):
    if user_input:
        st.session_state.chat_history.append(HumanMessage(content=user_input))

        # Check if form is complete
        missing_required = get_missing_required_fields()
        dependent_fields = get_relevant_dependent_fields()

        if not missing_required and not dependent_fields:
            st.success("✅ Form complete! Here's your data:")
            st.json(st.session_state.form_state)
            with open("form_data.json", "w") as f:
                json.dump(st.session_state.form_state, f, indent=2)
            st.info("Data saved to 'form_data.json'")
        else:
            # Run the conversation chain
            response = conversation_chain.run(
                fields_info=format_fields_info(),
                form_state=json.dumps(st.session_state.form_state),
                missing_fields=", ".join(missing_required),
                dependent_fields=", ".join(dependent_fields),
                user_input=user_input,
                chat_history=st.session_state.chat_history[-10:]
            )

            # Process the response
            if is_json(response):
                try:
                    response_json = json.loads(response)
                    is_valid, result = validate_extracted_fields(response_json)
                    if is_valid:
                        st.session_state.form_state.update(result)
                        updated_missing = get_missing_required_fields()
                        updated_dependent = get_relevant_dependent_fields()
                        if not updated_missing and not updated_dependent:
                            response_text = "Great! All required information has been provided. Your form is complete."
                            with open("form_data.json", "w") as f:
                                json.dump(st.session_state.form_state, f, indent=2)
                            st.success("Data saved to 'form_data.json'")
                        elif updated_missing:
                            response_text = f"Thanks! I still need the following: {', '.join(updated_missing)}."
                        else:
                            response_text = f"Thanks! Your required fields are complete. You can also provide {', '.join(updated_dependent)} if applicable."
                    else:
                        response_text = f"I found some issues: {result}"
                except json.JSONDecodeError:
                    response_text = "I had trouble processing that. Could you please provide your information clearly?"
            else:
                response_text = response

            st.session_state.chat_history.append(AIMessage(content=response_text))
            st.write(f"**AI**: {response_text}")

            # Refresh the page to update the UI
            st.rerun()