import os
import json
import re
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from wsdl_parser import extract_wsdl_schema

# Load environment variables
load_dotenv()

def snake_to_camel(name: str) -> str:
    """Convert snake_case string to camelCase."""
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def convert_json_properties_to_camel(json_str: str) -> str:
    """Convert all snake_case keys in a JSON string to camelCase."""
    try:
        data = json.loads(json_str)
        json_text = json.dumps(data)
        # Replace any snake_case key patterns (quoted strings containing underscores)
        def replace_key(match):
            key = match.group(1)
            if '_' in key:
                return f'"{snake_to_camel(key)}"'
            return match.group(0)
        return re.sub(r'"([a-z][a-z0-9]*(?:_[a-z0-9]+)+)"\s*:', lambda m: replace_key(m) + ':', json_text)
    except Exception:
        return json_str

def convert_java_json_properties_to_camel(java_code: str) -> str:
    """Post-process generated Java code: convert all @JsonProperty snake_case values to camelCase."""
    def replace_annotation(match):
        value = match.group(1)
        if '_' in value:
            camel = snake_to_camel(value)
            print(f"[PostProcess] @JsonProperty(\"{value}\") -> @JsonProperty(\"{camel}\")")
            return f'@JsonProperty("{camel}")'
        return match.group(0)
    return re.sub(r'@JsonProperty\("([^"]+)"\)', replace_annotation, java_code)

class MigrationState(TypedDict):
    wsdl_path: str
    reference_context: str
    extracted_schema: str
    generated_json_contract: str
    generated_code: str
    validation_errors: List[str]
    is_valid: bool

def node_extract(state: MigrationState) -> MigrationState:
    """Node 1: Extract WSDL/XSD definitions."""
    print("[Agent] Running Extract Node...")
    try:
        extracted = extract_wsdl_schema(state["wsdl_path"])
        state["extracted_schema"] = extracted
    except Exception as e:
        state["validation_errors"].append(f"Extraction Error: {str(e)}")
        state["extracted_schema"] = ""
    return state

def node_generate(state: MigrationState) -> MigrationState:
    """Node 2: Generate JSON Schema and Java DTOs using LLM."""
    print("[Agent] Running Generate Node...")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        model_name = os.getenv("MODEL_NAME", "gemini-1.5-pro")
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.1, google_api_key=gemini_key)
    else:
        model_name = os.getenv("MODEL_NAME", "gpt-4o")
        llm = ChatOpenAI(model_name=model_name, temperature=0.1)
    
    system_prompt = """You are an expert AI Architect and Lead Java/Python Engineer.
Your task is to migrate a legacy SOAP/WSDL schema into a modern OpenAPI JSON Schema and Java Spring DTOs.
You will be provided with:
1. The extracted WSDL/XSD definitions in JSON format.
2. A reference context of existing production Java Spring DTOs to mirror the design style and naming conventions. 

CRITICAL RULE: You MUST strictly mirror the exact JSON property naming conventions (e.g., camelCase vs snake_case) found in the reference context for your generated `@JsonProperty` annotations and JSON schema keys. Do not default to snake_case if the references use camelCase.

You must output your response in the following format exactly, with no additional conversational text outside these blocks:

### JSON SCHEMA
```json
<Your OpenAPI-compliant JSON schema contract here>
```

### JAVA DTOS
Generate one class per type found in the schema. Separate each class using this exact delimiter format: `// FILE: <ClassName>.java`
The class name must be derived from the schema type name — do NOT reuse any names from these instructions.
```java
// FILE: <FirstClassNameFromSchema>.java
public class <FirstClassNameFromSchema> { ... }

// FILE: <SecondClassNameFromSchema>.java
public class <SecondClassNameFromSchema> { ... }
```
"""

    human_message = f"""
--- WSDL / XSD EXTRACTION ---
{state["extracted_schema"]}

--- REFERENCE CONTEXT (Existing Java DTOs) ---
{state["reference_context"]}

Please generate the JSON SCHEMA and JAVA DTOS.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Langchain Gemini sometimes returns a list of blocks instead of a string
    if isinstance(content, list):
        content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block) 
            for block in content
        )

    # Parse out the JSON schema block
    json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if json_match:
        raw_json = json_match.group(1).strip()
        # Post-process: guarantee all JSON keys are camelCase
        state["generated_json_contract"] = convert_json_properties_to_camel(raw_json)
    else:
        state["generated_json_contract"] = ""
        state["validation_errors"].append("Failed to extract JSON block from LLM output.")

    # Parse out the Java code block
    java_match = re.search(r"```java\s*(.*?)\s*```", content, re.DOTALL)
    if java_match:
        raw_java = java_match.group(1).strip()
        # Post-process: guarantee all @JsonProperty values are camelCase
        state["generated_code"] = convert_java_json_properties_to_camel(raw_java)
    else:
        state["generated_code"] = ""
        state["validation_errors"].append("Failed to extract Java block from LLM output.")

    return state

def node_validate(state: MigrationState) -> MigrationState:
    """Node 3: Validate generated JSON and Code."""
    print("[Agent] Running Validate Node...")
    state["is_valid"] = True
    
    # Validate JSON
    if not state["generated_json_contract"]:
        state["validation_errors"].append("JSON Contract is empty.")
        state["is_valid"] = False
    else:
        try:
            json.loads(state["generated_json_contract"])
        except json.JSONDecodeError as e:
            state["validation_errors"].append(f"Invalid JSON: {str(e)}")
            state["is_valid"] = False

    # Validate Java Code
    if not state["generated_code"]:
        state["validation_errors"].append("Generated Java code is empty.")
        state["is_valid"] = False
    elif len(state["generated_code"]) < 50:
        state["validation_errors"].append("Generated Java code seems too short to be valid.")
        state["is_valid"] = False

    if state["is_valid"]:
        print("[Agent] Validation Passed.")
    else:
        print("[Agent] Validation Failed with errors:", state["validation_errors"])

    return state

def build_graph():
    """Builds and compiles the LangGraph."""
    workflow = StateGraph(MigrationState)
    
    # Add nodes
    workflow.add_node("extract", node_extract)
    workflow.add_node("generate", node_generate)
    workflow.add_node("validate", node_validate)
    
    # Add edges
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "generate")
    workflow.add_edge("generate", "validate")
    workflow.add_edge("validate", END)
    
    return workflow.compile()
