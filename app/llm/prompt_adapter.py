# app/utils/llm_utils/prompt_adapter.py
# create a new file for the prompt adapter
# app/utils/llm_utils/prompt_adapter.py
import os

class PromptTemplateAdapter:
    """Adapts prompt templates for different LLM providers."""
    
    def __init__(self, templates_dir="app/utils/prompts"):
        self.templates_dir = templates_dir
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all prompt templates from the templates directory."""
        # Load standard templates
        with open(f"{self.templates_dir}/stakeholder_extraction.txt", "r") as f:
            self.templates["standard"] = f.read()
        
        # Load provider-specific templates if they exist
        for provider in ["ollama", "github", "anthropic"]:
            specific_template = f"{self.templates_dir}/stakeholder_extraction_{provider}.txt"
            if os.path.exists(specific_template):
                with open(specific_template, "r") as f:
                    self.templates[provider] = f.read()
    
    def get_prompt(self, task, provider, **kwargs):
        """Get the appropriate prompt template for the given task and provider."""
        template_key = f"{task}_{provider}" if f"{task}_{provider}" in self.templates else task
        
        if provider == "ollama":
            # Simpler prompts for local models
            template_key = f"{task}_simple" if f"{task}_simple" in self.templates else template_key
        
        template = self.templates.get(
            template_key,
            self.templates.get(provider, self.templates.get("standard"))
        )
        
        # Customize prompt based on provider capabilities
        if provider == "anthropic":
            # Claude works better with clearly defined roles and structured examples
            template = self._enhance_for_claude(template)
        elif provider == "ollama":
            # Local models need simpler instructions and fewer requirements
            template = self._simplify_for_smaller_models(template)
        
        return template
    
    def _enhance_for_claude(self, template):
        """Enhance template for Claude's capabilities."""
        # Add more explicit formatting for Claude if needed
        return template
    
    def _simplify_for_smaller_models(self, template):
        """Simplify template for smaller models."""
        # Remove complex parts of the prompt that smaller models struggle with
        # This is a simplistic example - real implementation would be more sophisticated
        if "Return the data in a structured JSON format:" in template:
            # Simplify the JSON structure requirements
            simplified = template.split("Return the data in a structured JSON format:")[0]
            simplified += "\nReturn a simple JSON with stakeholder information. Include name, type, and role."
            return simplified
        return template