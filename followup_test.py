from typing import List

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine


project_id = "sea-id-aid-genai"
location = "global"                    # Values: "global", "us", "eu"
data_store_id = "kms-agent-datastore"
initial_query = "apa itu sisa kuota"

def multi_turn_search(
    project_id: str,
    location: str,
    data_store_id: str,
    current_query: str,
) -> None:
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.ConversationalSearchServiceClient(
        client_options=client_options
    )

    # Initialize conversation
    conversation = initialize_conversation(project_id, location, data_store_id, client)
    
    while True:
        response = converse_with_conversation(conversation, current_query, client)
        
        process_response(response)
        
        follow_up_query = input("Enter your follow-up question: ")
        
        if follow_up_query == "exit":
            break
        
        # Use follow-up query for next iteration
        current_query = follow_up_query

def initialize_conversation(project_id: str, location: str, data_store_id: str, client):

    # Initialize Multi-Turn Session
    return client.create_conversation(
            # The full resource name of the data store
            # e.g. projects/{project_id}/locations/{location}/dataStores/{data_store_id}
            parent=client.data_store_path(
                project=project_id, location=location, data_store=data_store_id
            ),
            conversation=discoveryengine.Conversation(),
        )

def converse_with_conversation(conversation, current_query: str, client):
    request = discoveryengine.ConverseConversationRequest(
            name=conversation.name,
            query=discoveryengine.TextInput(input=current_query),
            serving_config=client.serving_config_path(
                project=project_id,
                location=location,
                data_store=data_store_id,
                serving_config="default_config",
            ),
            # Options for the returned summary
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                # Number of results to include in summary
                summary_result_count=3,
                include_citations=True,
            ),
        )
    
    return client.converse_conversation(request)

def process_response(response):
    print(f"Reply: {response.reply.summary.summary_text}\n")

    for i, result in enumerate(response.search_results, 1):
        result_data = result.document.derived_struct_data
        print(f"[{i}]")
        print(f"Link: {result_data['link']}")
        print(f"First Snippet: {result_data['snippets'][0]['snippet']}")
        print(
            "First Extractive Answer: \n"
            # f"\tPage: {result_data['extractive_answers'][0]['pageNumber']}\n"
            f"\tContent: {result_data['extractive_answers'][0]['content']}\n\n"
        )
    print("\n\n")

multi_turn_search(project_id, location, data_store_id, initial_query)
