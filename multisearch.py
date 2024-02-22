from typing import List

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine


project_id = "sea-id-aid-genai"
location = "global"                    # Values: "global", "us", "eu"
data_store_id = "kms-agent-datastore"
# search_query = "halo"


def multi_turn_search_sample(
    project_id: str,
    location: str,
    data_store_id: str,
    search_queries: List[str],
) -> List[discoveryengine.ConverseConversationResponse]:
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.ConversationalSearchServiceClient(
        client_options=client_options
    )

    # Initialize Multi-Turn Session
    conversation = client.create_conversation(
        # The full resource name of the data store
        # e.g. projects/{project_id}/locations/{location}/dataStores/{data_store_id}
        parent=client.data_store_path(
            project=project_id, location=location, data_store=data_store_id
        ),
        conversation=discoveryengine.Conversation(),
    )


    for search_query in search_queries:
        # Add new message to session
        request = discoveryengine.ConverseConversationRequest(
            name=conversation.name,
            query=discoveryengine.TextInput(input=search_query),
            serving_config=client.serving_config_path(
                location=location,
                project=project_id,
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
        response = client.converse_conversation(request)

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

def search():
    response = multi_turn_search_sample(
        project_id,
        location,
        data_store_id,
        ["apa itu sisa kuota", "bagaimana cara dapatnya"]
    )
    return response

search()