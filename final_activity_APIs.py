import requests
import json
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
 
api_token = 'api_token'
 
# Functions for Pipedrive API interactions
def get_all_activities(api_token):
    url = f'https://api.pipedrive.com/v1/activities?api_token={api_token}'
    response = requests.get(url)
    return response.json()
 
def get_activity_by_id(api_token, activity_id):
    url = f'https://api.pipedrive.com/v1/activities/{activity_id}?api_token={api_token}'
    response = requests.get(url)
    return response.json()
 
def create_activity(api_token, data):
    url = f'https://api.pipedrive.com/v1/activities?api_token={api_token}'
    print("Data being sent to API:", json.dumps(data, indent=4))  # Debugging line
    response = requests.post(url, json=data)
    if response.status_code != 201:  # Pipedrive typically uses 201 for created
        print(f"Error {response.status_code}: {response.text}")
    return response.json()
 
def update_activity(api_token, activity_id, data):
    url = f'https://api.pipedrive.com/v1/activities/{activity_id}?api_token={api_token}'
    print("Data being sent to API:", json.dumps(data, indent=4))  # Debugging line
    response = requests.put(url, json=data)
    return response.json()
 
def delete_activity(api_token, activity_id):
    url = f'https://api.pipedrive.com/v1/activities/{activity_id}?api_token={api_token}'
    response = requests.delete(url)
    return response.json()
 
# Mapping between user intents and functions
intent_to_function = {
    "get all activities": get_all_activities,
    "get activity by id": get_activity_by_id,
    "create activity": create_activity,
    "update activity": update_activity,
    "delete activity": delete_activity
}
 
# LLM Prompt Template
prompt_template = """
You are an AI assistant for interacting with the Pipedrive API. Based on the user's query, return the exact method name and any relevant parameters as a comma-separated list. Only use the following method names:
- "get all activities"
- "get activity by id"
- "create activity"
- "update activity"
- "delete activity"
 
For example:
- "Get all activities" -> get all activities
- "Show details for activity 25" -> get activity by id, 25
- "Create an activity for deal 2" -> create activity, deal_id=2
- "Update activity 52" -> update activity, 52
- "Delete activity 30" -> delete activity, 30
 
User query: "{user_query}"
 
Method and parameters:
"""
 
def create_llm_chain(api_key, user_query):
    prompt = ChatPromptTemplate.from_template(template=prompt_template)
    llm = ChatGroq(model="llama3-8b-8192", temperature=0.2, groq_api_key=api_key)
 
    chain = LLMChain(
        prompt=prompt,
        llm=llm,
        output_parser=StrOutputParser()
    )
    return chain
 
def parse_llm_response(llm_response):
    llm_response = llm_response.strip().lower()
    method_name, *params = map(str.strip, llm_response.split(","))
 
    # Allow minor variations in method names
    synonyms = {
        "get activities": "get all activities",
        "get activity": "get activity by id",
        "create activity": "create activity",
        "update activity": "update activity",
        "delete activity": "delete activity"
    }
 
    method_name = synonyms.get(method_name, method_name)
    return method_name, params
 
def ask_for_missing_details(activity_details, selected_options):
    prompts = {
        'subject': "Please provide the subject of the activity.",
        'deal_id': "Please provide the deal ID associated with this activity.",
        'person_id': "Please provide the person ID associated with this activity.",
        'org_id': "Please provide the organization ID associated with this activity.",
        'due_date': "Please provide the due date for this activity (format YYYY-MM-DD).",
        'type': "Please specify the type of activity (e.g., call, meeting).",
        'due_time': "Please provide the due time for this activity (format HH:MM).",
        'participants': "Please provide a list of participants (format: person_id=5, primary_flag=True; person_id=7, primary_flag=False)."
    }
 
    field_options = {
        '1': 'subject',
        '2': 'deal_id',
        '3': 'person_id',
        '4': 'org_id',
        '5': 'due_date',
        '6': 'type',
        '7': 'due_time',
        '8': 'participants'
    }
 
    for option in selected_options:
        field = field_options.get(option)
        if field:
            activity_details[field] = input(prompts[field])
    
    # Handle participants input separately to match the expected format
    if 'participants' in activity_details:
        participants = []
        for participant in activity_details['participants'].split(';'):
            person_id, primary_flag = participant.split(',')
            person_id = int(person_id.split('=')[1].strip())
            primary_flag = primary_flag.split('=')[1].strip().lower() == 'true'
            participants.append({"person_id": person_id, "primary_flag": primary_flag})
        activity_details['participants'] = participants
    
    return activity_details
 
def execute_function(method_name, params):
    if method_name == "create activity":
        # Create a data dictionary from the params
        activity_details = {}
        if params:
            for param in params:
                key, value = param.split('=')
                activity_details[key.strip()] = value.strip()
        
        # Ask if user wants to add or modify details
        print("Select options to add or modify details:")
        print("1. Subject")
        print("2. Deal ID")
        print("3. Person ID")
        print("4. Organization ID")
        print("5. Due Date")
        print("6. Type")
        print("7. Due Time")
        print("8. Participants")
        print("Enter numbers separated by commas (e.g., 1,3,5) or type 'none': ")
        user_input = input().strip().lower()
        
        if user_input != 'none':
            selected_options = [opt.strip() for opt in user_input.split(',')]
            activity_details = ask_for_missing_details(activity_details, selected_options)
        
        result = create_activity(api_token, activity_details)
 
    elif method_name == "update activity":
        # Ensure activity_id is provided
        if not params or len(params) < 1:
            print("Activity ID is required to update an activity.")
            return
        
        activity_id = params[0]
        # Create a data dictionary from the params
        activity_details = {}
        if len(params) > 1:
            for param in params[1:]:
                key, value = param.split('=')
                activity_details[key.strip()] = value.strip()
        
        # Ask if user wants to add or modify details
        print("Select options to add or modify details:")
        print("1. Subject")
        print("2. Deal ID")
        print("3. Person ID")
        print("4. Organization ID")
        print("5. Due Date")
        print("6. Type")
        print("7. Due Time")
        print("8. Participants")
        print("Enter numbers separated by commas (e.g., 1,3,5) or type 'none': ")
        user_input = input().strip().lower()
        
        if user_input != 'none':
            selected_options = [opt.strip() for opt in user_input.split(',')]
            activity_details = ask_for_missing_details(activity_details, selected_options)
        
        result = update_activity(api_token, activity_id, activity_details)
 
    elif method_name in intent_to_function:
        function = intent_to_function[method_name]
        if params:
            result = function(api_token, *params)
        else:
            result = function(api_token)
    else:
        print(f"Unrecognized method '{method_name}'. Please try again.")
        return
    
    print(json.dumps(result, indent=4))
 
 
def main():
    api_key = "api_key"
 
    user_query = input("Ask something about Pipedrive activities: ").strip()
 
    llm_chain = create_llm_chain(api_key, user_query)
    llm_response = llm_chain.run(user_query).strip()
 
    method_name, params = parse_llm_response(llm_response)
    execute_function(method_name, params)
 
if __name__ == "__main__":
    main()
