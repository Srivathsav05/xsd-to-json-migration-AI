# SOAP2JSON Migration Agent
### WSDLift — Agentic SOAP to JSON Migration Tool

An end-to-end Agentic AI Migration tool designed to automate the conversion of legacy SOAP/WSDL services into modern JSON API endpoints and Java Spring DTOs. 

By leveraging LangGraph and Google's Gemini models (or OpenAI), this pipeline dynamically parses complex nested XSD/WSDL trees and intelligently converts them into modern OpenAPI JSON Schema contracts and cleanly annotated Spring Boot DTOs (`@JsonProperty`, `@NotNull`, etc.), mirroring your specific architectural style from existing reference models.

## Features
- **Smart Parsing:** Recursively walks through complex nested WSDL/XSD folder structures and extracts unified schemas, stripping unnecessary SOAP XML boilerplate.
- **Reference-Aware:** Learns your team's exact coding standards and annotations by scanning your existing `references/entity` Java DTOs.
- **Agentic Pipeline:** Uses LangGraph to orchestrate a reliable 3-step pipeline: `Extract` -> `Generate` -> `Validate`.
- **Validation:** Automatically validates the generated JSON and Java code before writing the artifacts.
- **Multi-File Output:** Each generated Java DTO class is saved as its own individual `.java` file (e.g., `CustomerProfile.java`, `AuditHeaderType.java`), keeping your output clean and ready for direct import into your project.

---

## Prerequisites
- **Python:** Version 3.9 or higher (3.11+ recommended).
- **API Key:** A valid Google Gemini API Key (or OpenAI API Key).

## Setup & Installation

**1. Clone the repository / Navigate to the project:**
```bash
git clone <your-repository-url>
cd java-soap-json-migrator_AI
```
*(If you already have the files locally, just open your terminal and navigate to the `java-soap-json-migrator_AI` folder.)*

**2. Install dependencies:**
Install the required packages using pip (it is recommended to use a virtual environment, or install with `--user`):
```bash
pip install -r requirements.txt
```
*(If you encounter permission issues, run `pip install --user -r requirements.txt`)*

**3. Configure Environment Variables:**
The project relies on a `.env` file to store API keys and model configurations. 
If it doesn't exist, create a file named `.env` in the root of `java-soap-json-migrator_AI` and add the following:

```env
# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-1.5-pro

# (Optional) OpenAI Configuration
# OPENAI_API_KEY=your_openai_api_key_here
# MODEL_NAME=gpt-4o
```
*Note: Make sure to save the file after editing.*

---

## Directory Structure & Inputs

Before running the CLI, you must place your source files in the correct directories:

- **`inputs/`**: Place all your legacy `.wsdl`, `.xsd`, or `.xml` schemas here. The tool recursively searches subfolders, so you can drop your entire legacy schema folder tree in here.
- **`references/entity/`**: Place your existing, modern Java DTOs, Enums, Requests, and Responses in here. The LLM uses these classes as a structural and stylistic reference to generate the new code.

---

## Usage

Run the Click CLI application by passing the input path, the reference path, and your desired output path. 

```bash
python cli.py --wsdl ./inputs --ref ./references/entity --out ./outputs
```

### What happens when you run it?
1. **Context Loading:** Reads all `.java` files from your reference directory and bundles them into context blocks.
2. **Graph Execution:** Starts the LangGraph execution flow.
   - **Extract Node:** Parses the XML schemas inside `./inputs`.
   - **Generate Node:** Sends the parsed schema + Java reference context to the LLM (Gemini) to generate the modern API contract and code.
   - **Validate Node:** Verifies that valid JSON and Java syntax were returned.
3. **Artifact Generation:** Saves the validated outputs to the `./outputs/` folder.

### Outputs
Once successfully executed, check the `./outputs/` folder. You will find:
- **`schema_contract.json`**: The newly generated OpenAPI-compliant JSON schema contract.
- **Individual Java DTO files:** Each Java class is saved as its own separate file, named after the class (e.g., `CustomerProfile.java`, `AuditHeaderType.java`, `ServiceRequest.java`). This makes the output directly importable into your Spring Boot project without any manual splitting.

> **Note:** If the LLM does not use the expected `// FILE: <ClassName>.java` delimiter format in its response, the tool falls back to saving all generated code into a single `GeneratedDTOs.java` file.

