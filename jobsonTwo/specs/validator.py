class JobSpecValidator:
    VALID_INPUT_TYPES = {"string", "number", "boolean", "file"}
    REQUIRED_FIELDS = {"name", "description", "expectedInputs", "execution"}
    REQUIRED_EXECUTION_FIELDS = {"application", "arguments"}
    REQUIRED_INPUT_FIELDS = {"id", "type", "name", "description"}

    def validate(self, spec):
        """Validate a job specification."""
        # Check required fields
        self._validate_required_fields(spec)
        
        # Validate inputs
        self._validate_inputs(spec.get("expectedInputs", []))
        
        # Validate execution
        self._validate_execution(spec.get("execution", {}))
        
        return True

    def _validate_required_fields(self, spec):
        """Validate that all required fields are present."""
        missing_fields = self.REQUIRED_FIELDS - set(spec.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

    def _validate_inputs(self, inputs):
        """Validate the expected inputs section."""
        if not isinstance(inputs, list):
            raise ValueError("expectedInputs must be a list")

        for input_spec in inputs:
            # Check required input fields
            missing_fields = self.REQUIRED_INPUT_FIELDS - set(input_spec.keys())
            if missing_fields:
                raise ValueError(f"Input spec missing required fields: {missing_fields}")

            # Validate input type
            if input_spec["type"] not in self.VALID_INPUT_TYPES:
                raise ValueError(f"Invalid input type: {input_spec['type']}. Must be one of {self.VALID_INPUT_TYPES}")

    def _validate_execution(self, execution):
        """Validate the execution section."""
        # Check required execution fields
        missing_fields = self.REQUIRED_EXECUTION_FIELDS - set(execution.keys())
        if missing_fields:
            raise ValueError(f"Execution spec missing required fields: {missing_fields}")

        # Validate arguments is a list
        if not isinstance(execution["arguments"], list):
            raise ValueError("Execution arguments must be a list") 