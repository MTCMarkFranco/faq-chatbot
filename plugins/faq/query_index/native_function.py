import os
import json
from semantic_kernel.plugin_definition import sk_function, sk_function_context_parameter
from semantic_kernel.orchestration.sk_context import SKContext
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from flask import jsonify

class QueryIndexPlugin:
    @sk_function(
        description="Query the Azure Search FAQ index",
        name="get_faq_query_results",
        input_description="The question that the user needs an answer to from the FAQ index"
    )
    @sk_function_context_parameter(
        name="output",
        description="The results of the query to the FAQ index"
    )
    def get_faq_query_results(self, context: SKContext) -> str:
        # Replace with your service name and index name
        service_name = os.getenv("AZURE_SEARCH_SERVICE")
        index_name = os.getenv("AZURE_SEARCH_INDEX")
        api_key = os.getenv("AZURE_SEARCH_API_KEY")

        endpoint = f"https://{service_name}.search.windows.net/"
        credential = AzureKeyCredential(api_key)

        client = SearchClient(endpoint=endpoint,
                    index_name=index_name,
                    credential=credential)

        results = client.search(search_text=context["input"], 
                    include_total_count=True, 
                    search_fields=["Category", "Question", "Answer"],   
                    select=["Category", "Question", "Answer"],
                    top=5,
                    query_type="semantic",
                    semantic_configuration_name="sr-faq")

        result_list = []
        for result in results:
            result_list.append(result)

        return json.dumps(result_list)
