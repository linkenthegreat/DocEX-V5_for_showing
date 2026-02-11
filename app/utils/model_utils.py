"""
Model Availability and Management Utilities
Handles AI model status checking and recommendations
"""

def check_model_availability():
    """Check which AI models are currently available"""
    try:
        # This would integrate with your existing AI agent setup
        # For now, we'll simulate the checks
        
        model_status = {
            "gpt4o": True,      # Assume GPT-4o is available if API key is set
            "deepseek": True,   # Assume DeepSeek is available
            "llama_local": False  # Assume local Llama needs to be checked
        }
        
        # TODO: Add real model availability checks
        # - Check OpenAI API key for GPT-4o
        # - Check DeepSeek API key 
        # - Check if local Llama server is running
        
        return model_status
        
    except Exception as e:
        print(f"❌ Error checking model availability: {e}")
        return {"gpt4o": False, "deepseek": False, "llama_local": False}

def get_recommended_priority(model_status):
    """Get recommended priority based on available models"""
    if model_status.get("llama_local"):
        return "cost"  # Local is free
    elif model_status.get("deepseek"):
        return "speed"  # DeepSeek is fast and affordable
    elif model_status.get("gpt4o"):
        return "quality"  # GPT-4o for quality
    else:
        return "cost"  # Default fallback

def find_source_file(filename):
    """Find the source file for extraction (TTL or original document)"""
    try:
        import os
        from flask import current_app
        
        app_dir = current_app.config.get('APP_DIR', os.path.dirname(os.path.abspath(__file__)))
        
        # Check triples directory first
        triples_dir = os.path.join(app_dir, '..', 'database', 'triples')
        triples_path = os.path.join(triples_dir, filename)
        
        if os.path.exists(triples_path):
            return triples_path
        
        # Check other possible locations
        possible_dirs = [
            os.path.join(app_dir, '..', 'uploads'),
            os.path.join(app_dir, '..', 'processed_files'),
            os.path.join(app_dir, '..', 'database', 'jsonld')
        ]
        
        for dir_path in possible_dirs:
            if os.path.exists(dir_path):
                file_path = os.path.join(dir_path, filename)
                if os.path.exists(file_path):
                    return file_path
        
        return None
        
    except Exception as e:
        print(f"❌ Error finding source file: {e}")
        return None

# Export functions
__all__ = [
    'check_model_availability',
    'get_recommended_priority',
    'find_source_file'
]