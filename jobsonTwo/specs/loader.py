import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .validator import JobSpecValidator

class JobSpecLoader:
    """Loads and validates job specifications from YAML files."""
    
    def __init__(self):
        self.validator = JobSpecValidator()

    def load(self, spec_path: str) -> Dict[str, Any]:
        """Load a job specification from a file path."""
        return self.load_from_file(spec_path)
    
    def load_from_file(self, spec_path: str) -> Dict[str, Any]:
        """Load a job specification from a file path."""
        path = Path(spec_path)
        if not path.exists():
            raise FileNotFoundError(f"Job spec file not found: {spec_path}")
        
        with open(path, 'r') as f:
            spec = yaml.safe_load(f)
        
        self.validator.validate(spec)
        return spec

    def load_from_string(self, yaml_string):
        """Load and validate a job specification from a YAML string."""
        spec = yaml.safe_load(yaml_string)
        self.validator.validate(spec)
        return spec 

    def _validate_spec(self, spec: Dict[str, Any]) -> None:
        """Validate a job specification."""
        required_fields = ['name', 'description', 'expectedInputs', 'execution']
        
        for field in required_fields:
            if field not in spec:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(spec['expectedInputs'], list):
            raise ValueError("expectedInputs must be a list")
        
        for input_spec in spec['expectedInputs']:
            self._validate_input_spec(input_spec)
        
        if not isinstance(spec['execution'], dict):
            raise ValueError("execution must be a dictionary")
        
        if 'application' not in spec['execution']:
            raise ValueError("execution must specify an application")
    
    def _validate_input_spec(self, input_spec: Dict[str, Any]) -> None:
        """Validate an input specification."""
        required_fields = ['id', 'type', 'name']
        
        for field in required_fields:
            if field not in input_spec:
                raise ValueError(f"Input spec missing required field: {field}")
        
        valid_types = ['string', 'number', 'boolean']
        if input_spec['type'] not in valid_types:
            raise ValueError(f"Invalid input type: {input_spec['type']}. Must be one of {valid_types}") 