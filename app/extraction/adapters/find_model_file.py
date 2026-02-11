"""
Find and examine the current model definition
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def find_model_file():
    """Find where the models are defined"""
    
    print("=== Finding Model Definitions ===")
    
    # Look for model files
    possible_paths = [
        'app/extraction/models.py',
        'app/extraction/models/__init__.py',
        'app/models.py',
        'app/extraction/extraction_models.py'
    ]
    
    for path in possible_paths:
        full_path = os.path.join(os.getcwd(), path)
        if os.path.exists(full_path):
            print(f"✅ Found model file: {full_path}")
            
            # Show the file content related to ExtractedStakeholder
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for ExtractedStakeholder definition
                lines = content.split('\n')
                in_stakeholder_class = False
                stakeholder_lines = []
                
                for i, line in enumerate(lines):
                    if 'class ExtractedStakeholder' in line:
                        in_stakeholder_class = True
                        stakeholder_lines.append(f"{i+1}: {line}")
                    elif in_stakeholder_class:
                        if line.strip().startswith('class ') and 'ExtractedStakeholder' not in line:
                            break
                        stakeholder_lines.append(f"{i+1}: {line}")
                        if len(stakeholder_lines) > 50:  # Limit output
                            stakeholder_lines.append("... (truncated)")
                            break
                
                if stakeholder_lines:
                    print(f"\nExtractedStakeholder definition from {path}:")
                    for line in stakeholder_lines:
                        print(f"  {line}")
                else:
                    print(f"  No ExtractedStakeholder class found in {path}")
                    
            except Exception as e:
                print(f"  Error reading {path}: {e}")
        else:
            print(f"❌ Not found: {full_path}")

if __name__ == "__main__":
    find_model_file()