#Create a class called TaskManager that will manage the tasks for the LLM
# class TaskManager:
import os
import yaml
from .prompt_adapter import PromptTemplateAdapter

class TaskManager:
    """Manages different LLM tasks and their prompt configurations."""
    
    def __init__(self, config_dir="app/config/tasks", prompt_adapter=None):
        self.config_dir = config_dir
        self.prompt_adapter = prompt_adapter or PromptTemplateAdapter()
        self.tasks = {}
        self._load_task_configs()
    
    def _load_task_configs(self):
        """Load task configurations from YAML files."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
            
        # Get all YAML files in the config directory
        config_files = [f for f in os.listdir(self.config_dir) 
                      if f.endswith('.yaml') or f.endswith('.yml')]
        
        # Load each config file
        for config_file in config_files:
            task_name = os.path.splitext(config_file)[0]
            with open(os.path.join(self.config_dir, config_file), 'r') as f:
                self.tasks[task_name] = yaml.safe_load(f)
    
    def get_task_prompt(self, task_name, provider, **kwargs):
        """Get the appropriate prompt for a specific task and provider."""
        if task_name not in self.tasks:
            raise ValueError(f"Unknown task: {task_name}")
            
        task_config = self.tasks[task_name]
        
        # Get task-specific customization parameters
        params = {**task_config.get('default_params', {}), **kwargs}
        
        # Get the base prompt template from the adapter
        return self.prompt_adapter.get_prompt(task_name, provider, **params)
    
    def list_available_tasks(self):
        """List all available tasks."""
        return list(self.tasks.keys())
    
    def get_task_info(self, task_name):
        """Get information about a specific task."""
        if task_name not in self.tasks:
            raise ValueError(f"Unknown task: {task_name}")
            
        return {
            'name': task_name,
            'description': self.tasks[task_name].get('description', ''),
            'parameters': self.tasks[task_name].get('parameters', {})
        }
