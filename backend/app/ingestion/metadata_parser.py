import re
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger("app.ingestion.metadata_parser")

def parse_metadata(raw_content: str) -> Tuple[Optional[Dict], str]:
    # Look for explicit markers first
    marker_pattern = r"---METADATA---\s*(.*?)\s*---END METADATA---"
    match = re.search(marker_pattern, raw_content, re.DOTALL)
    
    metadata_text = ""
    clean_content = raw_content
    
    if match:
        metadata_text = match.group(1)
        clean_content = raw_content.replace(match.group(0), "").strip()
    else:
        # Fallback heuristic: Extract first 25 lines as potential metadata header
        lines = raw_content.split('\n')
        header_lines = []
        body_lines = []
        in_header = True
        
        for i, line in enumerate(lines):
            if i > 25:
                in_header = False
            
            if in_header:
                header_lines.append(line)
                # If we hit an empty line after some metadata, end of header
                if line.strip() == '' and any(':' in h for h in header_lines):
                    # Check next line, if it doesn't have a colon, we stop
                    if i + 1 < len(lines) and ':' not in lines[i+1]:
                        in_header = False
            else:
                body_lines.append(line)
                
        metadata_text = '\n'.join(header_lines)
        clean_content = '\n'.join(body_lines).strip()
        
    if not metadata_text or ':' not in metadata_text:
        return None, raw_content
        
    metadata = {}
    for line in metadata_text.split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip().replace(' ', '_')
            val = val.strip()
            
            if key == 'Access_Roles' or key == 'Access_Role':
                # Parse list
                roles = [r.strip() for r in val.replace('[', '').replace(']', '').split(',')]
                metadata['Access_Roles'] = roles
            else:
                metadata[key] = val
                
    # Detect document type based on presence of owner info
    if 'Owner_Employee_ID' in metadata or 'Owner_Name' in metadata:
        metadata['_detected_type'] = 'employee_personal'
    else:
        metadata['_detected_type'] = 'company_wide'
        
    return metadata, clean_content
