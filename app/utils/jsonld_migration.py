"""
JSON-LD Migration Utility
Converts existing legacy JSON files to proper JSON-LD format
"""

import os
import json
from datetime import datetime
from pathlib import Path

def migrate_jsonld_files(jsonld_dir):
    """
    Migrate all JSON files in the directory to proper JSON-LD format
    """
    try:
        print(f"🔄 Starting JSON-LD migration in: {jsonld_dir}")
        
        if not os.path.exists(jsonld_dir):
            print(f"❌ Directory not found: {jsonld_dir}")
            return
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for filename in os.listdir(jsonld_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(jsonld_dir, filename)
                
                try:
                    # Load existing file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Check if already proper JSON-LD
                    if '@context' in data and '@type' in data:
                        print(f"✅ Already valid JSON-LD: {filename}")
                        skipped_count += 1
                        continue
                    
                    # Convert to JSON-LD
                    from app.utils.rdf_utils import convert_legacy_json_to_jsonld
                    
                    jsonld_data = convert_legacy_json_to_jsonld(data, filename)
                    
                    # Create backup
                    backup_path = file_path + '.backup'
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    # Save converted file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(jsonld_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Migrated: {filename}")
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"❌ Error migrating {filename}: {e}")
                    error_count += 1
        
        print(f"\n📊 Migration Summary:")
        print(f"   ✅ Migrated: {migrated_count}")
        print(f"   ⏩ Skipped: {skipped_count}")
        print(f"   ❌ Errors: {error_count}")
        
        return migrated_count > 0
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def validate_all_jsonld_files(jsonld_dir):
    """
    Validate all JSON-LD files in the directory
    """
    try:
        from app.utils.rdf_utils import validate_jsonld_format
        
        print(f"🔍 Validating JSON-LD files in: {jsonld_dir}")
        
        valid_count = 0
        invalid_count = 0
        
        for filename in os.listdir(jsonld_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(jsonld_dir, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                is_valid, message = validate_jsonld_format(data)
                
                if is_valid:
                    print(f"✅ {filename}: {message}")
                    valid_count += 1
                else:
                    print(f"❌ {filename}: {message}")
                    invalid_count += 1
        
        print(f"\n📊 Validation Summary:")
        print(f"   ✅ Valid: {valid_count}")
        print(f"   ❌ Invalid: {invalid_count}")
        
        return invalid_count == 0
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

if __name__ == "__main__":
    # Run migration if called directly
    import sys
    
    if len(sys.argv) > 1:
        jsonld_dir = sys.argv[1]
    else:
        # Default directory
        jsonld_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'jsonld')
    
    print("🚀 DocEX JSON-LD Migration Tool")
    print("=" * 40)
    
    # Run migration
    migrate_jsonld_files(jsonld_dir)
    
    print("\n" + "=" * 40)
    
    # Validate results
    validate_all_jsonld_files(jsonld_dir)