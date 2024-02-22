from typing import List
from fastapi import FastAPI, HTTPException
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.protobuf.json_format import MessageToDict
from proto.marshal.collections import repeated

from fastapi import FastAPI, Form
from starlette.responses import HTMLResponse

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

project_id = "sea-id-aid-genai"
location = "global"                    # Values: "global", "us", "eu"
data_store_id = "kms-agent-datastore"
# search_query = "halo"


def search_sample(
    project_id: str,
    location: str,
    data_store_id: str,
    search_query: str,
) -> List[discoveryengine.SearchResponse]:
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.SearchServiceClient(client_options=client_options)

    # The full resource name of the search engine serving config
    # e.g. projects/{project_id}/locations/{location}/dataStores/{data_store_id}/servingConfigs/{serving_config_id}
    serving_config = client.serving_config_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        serving_config="default_config",
    )

    # Optional: Configuration options for search
    # Refer to the `ContentSearchSpec` reference for all supported fields:
    # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SearchRequest.ContentSearchSpec
    content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
        # For information about snippets, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/snippets
        snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
            return_snippet=True
        ),
        # For information about search summaries, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/get-search-summaries
        summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
            summary_result_count=5,
            include_citations=True,
            ignore_adversarial_query=True,
            ignore_non_summary_seeking_query=True,
            # model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
            #     preamble="answer nicely please"
            # ),
        ),
    )

    # Refer to the `SearchRequest` reference for all supported fields:
    # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SearchRequest
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=search_query,
        page_size=10,
        content_search_spec=content_search_spec,
        query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
            condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
        ),
        spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
            mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
        ),
    )

    results = client.search(request).results
    summary = client.search(request).summary.summary_text
    
    # print(type(results))
    json_list = []

    for item in results:
        doc = item.document
        item_dict = {}
        for key, value in doc.derived_struct_data.items():
            if isinstance(value, str) or isinstance(value, int):
                item_dict[key] = value
            # else:
            #     item_dict[key] = type(value)
            elif isinstance(value, repeated.RepeatedComposite):
                item_dict[key] = type(value)
                nested_dict = {}
                for sub_key, sub_value in value[0].items():
                    nested_dict[sub_key] = sub_value
                item_dict[key] = nested_dict
            
        
        json_list.append(item_dict)

    # print(json_list)
    # print(summary.summary_text) 

    return json_list, summary

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <html>
        <body>
            <form action="/search" method="post">
                Enter your query: <input type="text" name="q" value="apakah Prosedur Permintaan Layanan Interkoneksi?">
                <input type="submit" value="Submit">
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

class QueryInput(BaseModel):
    message: str

@app.post("/search")
async def search(query_input: QueryInput):
    try:
        response = search_sample(
            project_id,
            location,
            data_store_id,
            search_query = query_input.message
        )
        return response
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        print(error_msg)  # Log the error message for debugging
        raise HTTPException(status_code=500, detail=error_msg)
