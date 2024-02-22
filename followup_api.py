from fastapi import FastAPI, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from typing import Optional
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from typing import List

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

def multi_turn_search(
    current_query: str,
) -> None:
    
    response = converse_with_conversation(conversation, current_query, client)
    process_response(response)


html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Follow-Up Question Form</title>
</head>
<body>
    <form action="/search" method="post">
        Enter your question: <input type="text" name="search_query" value="apa itu sisa kuota?">
        <input type="submit" value="Submit">
    </form>
</body>
</html>
"""

project_id = "sea-id-aid-genai"
location = "global"                    # Values: "global", "us", "eu"
data_store_id = "kms-agent-datastore"

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

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    with open("index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

class QueryInput(BaseModel):
    message: str

@app.post("/search")
async def search(search_query: QueryInput):
    print('works')
    if search_query.message.lower() == "exit":
        return {"message": "Goodbye!"}
    else:
        multi_turn_search(search_query.message)
        return {"message": "Question received and processed."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
