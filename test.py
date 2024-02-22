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


content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec()
print(dir(content_search_spec))
