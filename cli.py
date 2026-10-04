import os
import click
from agent import build_graph, MigrationState

def load_reference_context(ref_path: str) -> str:
    """
    Recursively walks through a directory, reads all .java files, 
    and bundles them with header separators.
    """
    if not os.path.exists(ref_path):
        click.secho(f"Warning: Reference path not found: {ref_path}", fg="yellow")
        return ""

    context_blocks = []
    
    if os.path.isfile(ref_path) and ref_path.endswith('.java'):
        with open(ref_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return f"// FILE: {os.path.basename(ref_path)}\n{content}\n"

    for root, _, files in os.walk(ref_path):
        for file in sorted(files):
            if file.endswith('.java'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, ref_path)
                
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                context_blocks.append(f"// FILE: {rel_path}\n{content}\n")
                
    return "\n".join(context_blocks)

@click.command()
@click.option('--wsdl', required=True, help='Path to input WSDL/XSD file or directory.')
@click.option('--ref', required=True, help='Path to reference context directory containing Java DTOs.')
@click.option('--out', required=True, help='Path to output directory where artifacts will be saved.')
def main(wsdl: str, ref: str, out: str):
    """
    Agentic AI Migration CLI tool to convert legacy SOAP/WSDL services 
    into modern JSON API endpoints and Java Spring DTOs.
    """
    click.secho(f"Starting migration process...", fg="blue", bold=True)
    click.secho(f"WSDL Path: {wsdl}", fg="cyan")
    click.secho(f"Reference Context: {ref}", fg="cyan")
    click.secho(f"Output Directory: {out}\n", fg="cyan")

    # Load Context
    click.secho("Loading reference context...", fg="blue")
    ref_context = load_reference_context(ref)
    click.secho(f"Loaded {len(ref_context)} bytes of reference context.\n", fg="green")

    # Initialize Agent State
    initial_state: MigrationState = {
        "wsdl_path": wsdl,
        "reference_context": ref_context,
        "extracted_schema": "",
        "generated_json_contract": "",
        "generated_code": "",
        "validation_errors": [],
        "is_valid": False
    }

    # Run LangGraph Agent
    click.secho("Initializing Agent Graph...", fg="blue")
    graph = build_graph()
    
    click.secho("Executing Agent Pipeline (Extract -> Generate -> Validate)...", fg="blue")
    
    try:
        final_state = graph.invoke(initial_state)
    except Exception as e:
        click.secho(f"Pipeline execution failed: {str(e)}", fg="red", bold=True)
        return

    # Check validation results
    if not final_state.get("is_valid"):
        click.secho("\nMigration completed with Validation Errors:", fg="red", bold=True)
        for err in final_state.get("validation_errors", []):
            click.secho(f" - {err}", fg="red")
        click.secho("\nReview output carefully.", fg="yellow")
    else:
        click.secho("\nMigration Pipeline completed successfully!", fg="green", bold=True)

    # Save Output
    os.makedirs(out, exist_ok=True)
    
    schema_path = os.path.join(out, "schema_contract.json")

    if final_state.get("generated_json_contract"):
        with open(schema_path, "w", encoding="utf-8") as f:
            f.write(final_state["generated_json_contract"])
        click.secho(f"Saved Schema Contract to: {schema_path}", fg="green")

    if final_state.get("generated_code"):
        # Split the string by the delimiter
        file_blocks = final_state["generated_code"].split("// FILE: ")
        
        saved_any = False
        for block in file_blocks:
            if not block.strip():
                continue
            
            # The first line is the filename, the rest is the code
            lines = block.strip().split("\n", 1)
            if len(lines) == 2:
                filename = lines[0].strip()
                code_content = lines[1].strip()
                
                # Write to the specific file
                specific_java_path = os.path.join(out, filename)
                with open(specific_java_path, "w", encoding="utf-8") as f:
                    f.write(code_content)
                click.secho(f"Saved Java DTO to: {specific_java_path}", fg="green")
                saved_any = True
                
        # Fallback if no delimiter was used
        if not saved_any:
            java_path = os.path.join(out, "GeneratedDTOs.java")
            with open(java_path, "w", encoding="utf-8") as f:
                f.write(final_state["generated_code"])
            click.secho(f"Saved Java DTOs to: {java_path}", fg="green")

if __name__ == "__main__":
    main()
