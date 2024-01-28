from flask import Flask, request, jsonify
from functools import wraps
from dotenv import dotenv_values
from semantic_kernel.orchestration.context_variables import ContextVariables
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextCompletion
from semantic_kernel.planning import SequentialPlanner
from dataclasses import dataclass
import json
import logging

app = Flask(__name__, template_folder="templates", static_folder="static")
config = dotenv_values(".env")
apiKey = config.get("API_KEY", None)

@dataclass
class AssistantAction:
    follow_up_needed: bool
    follow_up_question: str
    answer: str
    
class ChatHistory:
    def __init__(self):
        self.history = []
    
    def add_message(self, message):
        self.history.append(message)
    
    def get_messages(self):
        return json.dumps(self.history)
    
    def clear_history(self):
        self.history = []
        
chat_history = ChatHistory()

@app.route("/")
def root():
    return "Hello World"

async def execute(query):
    
    
    useAzureOpenAI = True
    chatTurnResponse = None
    
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Initialize the SemanticKernel
    logger.info("Initializing SemanticKernel")
    kernel = sk.Kernel()
    
    deployment, api_key, endpoint  = sk.azure_openai_settings_from_dot_env()
    kernel.add_chat_service("GPT35", AzureChatCompletion(deployment_name=deployment, api_key=api_key, base_url=endpoint))    
    #kernel.add_text_completion_service("GPT35", AzureTextCompletion( deployment_name=deployment, api_key=api_key, base_url=endpoint, logger=logger))
        
    native_plugins = kernel.import_native_plugin_from_directory("plugins/faq", "query_index")
    semantic_plugins = kernel.import_semantic_plugin_from_directory("plugins", "faq")
    
    seqPlanner = SequentialPlanner(kernel)
    planDirective = "Execute the following things in sequence: " \
                    "1. Write a better query by incoporating chat history and the current ask and making a more concise query, " \
                        "only if the question is too vague, otherwise pass the current ask as the query. " \
                    "2. Query the FAQ index with the given query. " \
                    "3. Review the query results and determine a follow-up calrification question is required. " \
                    
    seqPlan = await seqPlanner.create_plan_async(goal=planDirective)
    for step in seqPlan._steps:
        print(step.description, ":", step._state.__dict__)
    planContext = kernel.create_new_context(variables=ContextVariables(variables={"currentturnask": query, "history": chat_history.get_messages()}))
    assistantResponse = await seqPlan.invoke_async(query, planContext)
    assistantAction = json.loads(assistantResponse.result, object_hook=lambda d: AssistantAction(**d))
    
    chat_history.add_message({
		"role": "user",
		"content": query
	})
    
    if assistantAction.follow_up_needed == True:
        chat_history.add_message({
            "role": "assistant",
            "content": assistantAction.follow_up_question
        })
        chatTurnResponse =  "Further clarification required: " + assistantAction.follow_up_question
    else:
        chat_history.add_message({
            "role": "assistant",
            "content": assistantAction.answer
        })
        chatTurnResponse = assistantAction.answer
        
    print(chatTurnResponse)
    return chatTurnResponse
    

def require_api_key(view_function):
    @wraps(view_function)
    async def decorated_function(*args, **kwargs):
        if request.headers.get('X-Api-Key') != apiKey:
            return jsonify({"success": False, "message": "Invalid API key"}), 403
        return await view_function(*args, **kwargs)
    return decorated_function


@app.route("/query", methods=["POST"])
@require_api_key
async def query():
    body = request.get_json()
    query = body.get("query", None)
    
    output = await execute(query)
    
    response = {
        "success": True,
        "result": output
    }
    return jsonify(response)
