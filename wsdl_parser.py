import os
import json
import xmltodict
from typing import Dict, Any, Union, List

def _strip_namespace(tag: str) -> str:
    """Removes namespace prefix from XML tag or attribute name."""
    if tag.startswith('@xmlns') or tag == '@xmlns':
        return ""
    if ':' in tag and not tag.startswith('@'):
        return tag.split(':', 1)[1]
    if tag.startswith('@'):
        prefix_part = tag[1:]
        if ':' in prefix_part:
            return '@' + prefix_part.split(':', 1)[1]
    return tag

def _clean_dict(data: Union[Dict[str, Any], List[Any], str, int, float, bool]) -> Any:
    """
    Recursively cleans xmltodict parsed structures:
    - Removes XML namespace prefixes
    - Removes unnecessary WSDL/XSD boilerplate keys
    - Simplifies single-element lists or nested text nodes
    """
    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for key, value in data.items():
            # Skip noise attributes
            if key.startswith('@xmlns') or key in ('@xmlns', '@attributeFormDefault', '@elementFormDefault', '@version', '@targetNamespace'):
                continue
            
            clean_key = _strip_namespace(key)
            if not clean_key:
                continue

            cleaned_val = _clean_dict(value)
            
            # Skip empty objects/lists
            if cleaned_val is None or cleaned_val == {} or cleaned_val == []:
                continue

            # Simplify #text objects
            if isinstance(cleaned_val, dict) and list(cleaned_val.keys()) == ['#text']:
                cleaned_val = cleaned_val['#text']

            cleaned[clean_key] = cleaned_val

        return cleaned

    elif isinstance(data, list):
        cleaned_list = [_clean_dict(item) for item in data]
        return [item for item in cleaned_list if item is not None and item != {}]

    return data

def _extract_schema_from_parsed(parsed_dict: Dict[str, Any], file_name: str) -> Dict[str, Any]:
    """
    Extracts core data definitions (types, elements, messages, operations) 
    from a parsed WSDL/XSD dictionary.
    """
    cleaned = _clean_dict(parsed_dict)
    
    # Check if top-level is definitions (WSDL) or schema (XSD)
    result = {
        "source": file_name,
        "types": [],
        "elements": [],
        "messages": [],
        "operations": []
    }

    def walk_and_collect(obj: Any):
        if not isinstance(obj, dict):
            return
        
        for k, v in obj.items():
            if k in ('complexType', 'simpleType'):
                if isinstance(v, list):
                    result['types'].extend(v)
                elif isinstance(v, dict):
                    result['types'].append(v)
            elif k == 'element':
                if isinstance(v, list):
                    result['elements'].extend(v)
                elif isinstance(v, dict):
                    result['elements'].append(v)
            elif k == 'message':
                if isinstance(v, list):
                    result['messages'].extend(v)
                elif isinstance(v, dict):
                    result['messages'].append(v)
            elif k == 'operation':
                if isinstance(v, list):
                    result['operations'].extend(v)
                elif isinstance(v, dict):
                    result['operations'].append(v)
            elif isinstance(v, (dict, list)):
                walk_and_collect(v)

    walk_and_collect(cleaned)
    return result

def parse_single_file(file_path: str) -> Dict[str, Any]:
    """Parses a single XML/WSDL/XSD file using xmltodict and extracts schemas."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        parsed = xmltodict.parse(content)
        cleaned = _clean_dict(parsed)
        extracted = _extract_schema_from_parsed(cleaned, os.path.basename(file_path))
        extracted["raw_cleaned_structure"] = cleaned
        return extracted
    except Exception as e:
        return {
            "source": os.path.basename(file_path),
            "error": str(e)
        }

def extract_wsdl_schema(target_path: str) -> str:
    """
    Parses & simplifies WSDL files and multi-folder XSD schemas.
    
    Supports:
    - Single WSDL/XSD/XML file.
    - Recursive traversal of directories containing multiple subfolders (e.g. common/, idth-report.schemas/).
    
    Returns a simplified JSON string representation of the schemas.
    """
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Target path does not exist: {target_path}")

    combined_schema: Dict[str, Any] = {
        "target_path": target_path,
        "files_parsed": [],
        "schemas": []
    }

    if os.path.isfile(target_path):
        file_result = parse_single_file(target_path)
        combined_schema["files_parsed"].append(os.path.basename(target_path))
        combined_schema["schemas"].append(file_result)
    else:
        # Directory - walk recursively
        valid_extensions = ('.wsdl', '.xsd', '.xml')
        for root, _, files in os.walk(target_path):
            for file in sorted(files):
                if file.lower().endswith(valid_extensions):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, target_path)
                    file_result = parse_single_file(full_path)
                    file_result["relative_path"] = rel_path
                    combined_schema["files_parsed"].append(rel_path)
                    combined_schema["schemas"].append(file_result)

    return json.dumps(combined_schema, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        out = extract_wsdl_schema(sys.argv[1])
        print(out[:1000] + "\n..." if len(out) > 1000 else out)
