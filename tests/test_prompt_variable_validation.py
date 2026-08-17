"""
Pytest cases for prompt variable validation.

This module tests the validation of variables used in prompts for NL2SQL generation,
including:
- Variable format validation
- Required vs optional variables
- Type validation
- Special character handling
- Variable substitution
"""

import pytest
from typing import Dict, Any, List
import re


class PromptVariableValidator:
    """Validator for prompt template variables."""
    
    # Valid variable pattern: {variable_name} or {variable_name:type}
    VARIABLE_PATTERN = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*(?::[a-zA-Z_][a-zA-Z0-9_]*)?)\}')
    
    def __init__(self):
        self.errors: List[str] = []
    
    def validate_variable_format(self, variable_name: str) -> bool:
        """Validate that a variable name follows naming conventions."""
        if not variable_name:
            self.errors.append("Variable name cannot be empty")
            return False
        
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', variable_name):
            self.errors.append(
                f"Invalid variable name '{variable_name}'. "
                "Must start with letter or underscore and contain only alphanumeric characters and underscores."
            )
            return False
        
        return True
    
    def extract_variables(self, template: str) -> List[str]:
        """Extract all variables from a template string."""
        if not isinstance(template, str):
            self.errors.append(f"Template must be a string, got {type(template)}")
            return []
        
        matches = self.VARIABLE_PATTERN.findall(template)
        variables = []
        for match in matches:
            # Handle {var:type} format
            var_name = match.split(':')[0] if ':' in match else match
            variables.append(var_name)
        return list(set(variables))  # Remove duplicates
    
    def validate_variables_in_template(self, template: str) -> bool:
        """Validate all variables in a template."""
        if not isinstance(template, str):
            self.errors.append(f"Template must be a string, got {type(template)}")
            return False
        
        variables = self.extract_variables(template)
        valid = True
        for var in variables:
            if not self.validate_variable_format(var):
                valid = False
        return valid
    
    def validate_substitution(self, template: str, variables: Dict[str, Any]) -> bool:
        """Validate that all required variables are provided for substitution."""
        if not isinstance(template, str):
            self.errors.append(f"Template must be a string, got {type(template)}")
            return False
        
        if not isinstance(variables, dict):
            self.errors.append(f"Variables must be a dict, got {type(variables)}")
            return False
        
        required_vars = self.extract_variables(template)
        missing_vars = set(required_vars) - set(variables.keys())
        
        if missing_vars:
            self.errors.append(f"Missing required variables: {', '.join(sorted(missing_vars))}")
            return False
        
        return True
    
    def validate_variable_types(self, variables: Dict[str, Any], 
                                expected_types: Dict[str, type]) -> bool:
        """Validate that variables have expected types."""
        if not isinstance(variables, dict):
            self.errors.append(f"Variables must be a dict, got {type(variables)}")
            return False
        
        valid = True
        for var_name, expected_type in expected_types.items():
            if var_name not in variables:
                self.errors.append(f"Variable '{var_name}' not found")
                valid = False
                continue
            
            actual_value = variables[var_name]
            if not isinstance(actual_value, expected_type):
                self.errors.append(
                    f"Variable '{var_name}' has type {type(actual_value).__name__}, "
                    f"expected {expected_type.__name__}"
                )
                valid = False
        
        return valid
    
    def validate_variable_not_empty(self, variables: Dict[str, Any], 
                                   non_empty_vars: List[str]) -> bool:
        """Validate that specified variables are not empty."""
        valid = True
        for var_name in non_empty_vars:
            if var_name not in variables:
                self.errors.append(f"Variable '{var_name}' not found")
                valid = False
                continue
            
            value = variables[var_name]
            if value is None or (isinstance(value, (str, list, dict)) and len(value) == 0):
                self.errors.append(f"Variable '{var_name}' cannot be empty")
                valid = False
        
        return valid
    
    def substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template. Raises exception if validation fails."""
        if not self.validate_substitution(template, variables):
            raise ValueError("; ".join(self.errors))
        
        result = template
        for var_name, value in variables.items():
            # Replace both {var} and {var:type} formats
            pattern = r'\{' + var_name + r'(?::[a-zA-Z_][a-zA-Z0-9_]*)?\}'
            result = re.sub(pattern, str(value), result)
        
        return result


# ============================================================================
# TEST CASES
# ============================================================================


class TestVariableFormatValidation:
    """Test variable name format validation."""
    
    def test_valid_variable_names(self):
        """Test that valid variable names are accepted."""
        validator = PromptVariableValidator()
        valid_names = [
            'query',
            'schema',
            '_private',
            'camelCase',
            'snake_case',
            'CONSTANT',
            '_',
            'var123',
            'x1y2z3'
        ]
        for name in valid_names:
            assert validator.validate_variable_format(name), f"'{name}' should be valid"
    
    def test_invalid_variable_names(self):
        """Test that invalid variable names are rejected."""
        validator = PromptVariableValidator()
        invalid_names = [
            '123invalid',  # starts with number
            '!invalid',    # starts with special char
            'invalid-var', # contains hyphen
            'invalid.var', # contains dot
            'invalid var', # contains space
            'invalid@',    # contains special char
            '',            # empty
        ]
        for name in invalid_names:
            validator.errors = []
            assert not validator.validate_variable_format(name), f"'{name}' should be invalid"
            assert len(validator.errors) > 0
    
    def test_variable_name_empty(self):
        """Test that empty variable names are rejected."""
        validator = PromptVariableValidator()
        assert not validator.validate_variable_format('')
        assert len(validator.errors) > 0


class TestVariableExtraction:
    """Test extraction of variables from templates."""
    
    def test_extract_single_variable(self):
        """Test extracting a single variable from template."""
        validator = PromptVariableValidator()
        template = "SELECT * FROM {table_name}"
        variables = validator.extract_variables(template)
        assert variables == ['table_name']
    
    def test_extract_multiple_variables(self):
        """Test extracting multiple variables from template."""
        validator = PromptVariableValidator()
        template = "SELECT {columns} FROM {table_name} WHERE {condition}"
        variables = validator.extract_variables(template)
        assert set(variables) == {'columns', 'table_name', 'condition'}
    
    def test_extract_duplicate_variables(self):
        """Test that duplicate variables are returned only once."""
        validator = PromptVariableValidator()
        template = "Use {schema} schema. The schema is: {schema}"
        variables = validator.extract_variables(template)
        assert variables == ['schema']
        assert len(variables) == 1
    
    def test_extract_no_variables(self):
        """Test template with no variables."""
        validator = PromptVariableValidator()
        template = "This is a simple template with no variables"
        variables = validator.extract_variables(template)
        assert variables == []
    
    def test_extract_typed_variables(self):
        """Test extracting variables with type annotations."""
        validator = PromptVariableValidator()
        template = "Use {schema:str} and {limit:int}"
        variables = validator.extract_variables(template)
        assert set(variables) == {'schema', 'limit'}
    
    def test_extract_from_non_string_fails(self):
        """Test that non-string templates are handled gracefully."""
        validator = PromptVariableValidator()
        result = validator.extract_variables(123)
        assert result == []
        assert len(validator.errors) > 0


class TestTemplateValidation:
    """Test validation of entire templates."""
    
    def test_valid_template(self):
        """Test validation of a valid template."""
        validator = PromptVariableValidator()
        template = "SELECT {columns} FROM {table_name} WHERE id = {record_id}"
        assert validator.validate_variables_in_template(template)
    
    def test_template_with_invalid_variables(self):
        """Test that templates with invalid variables are rejected."""
        validator = PromptVariableValidator()
        template = "SELECT * FROM {123invalid}"
        assert not validator.validate_variables_in_template(template)
    
    def test_template_with_special_chars_in_variable(self):
        """Test template with special characters in variable names."""
        validator = PromptVariableValidator()
        template = "SELECT * FROM {table-name}"
        assert not validator.validate_variables_in_template(template)


class TestVariableSubstitution:
    """Test variable substitution in templates."""
    
    def test_simple_substitution(self):
        """Test simple variable substitution."""
        validator = PromptVariableValidator()
        template = "SELECT * FROM {table_name}"
        variables = {'table_name': 'users'}
        result = validator.substitute_variables(template, variables)
        assert result == "SELECT * FROM users"
    
    def test_multiple_substitutions(self):
        """Test substituting multiple variables."""
        validator = PromptVariableValidator()
        template = "SELECT {columns} FROM {table_name} WHERE {condition}"
        variables = {
            'columns': '*',
            'table_name': 'users',
            'condition': 'id > 0'
        }
        result = validator.substitute_variables(template, variables)
        assert result == "SELECT * FROM users WHERE id > 0"
    
    def test_substitution_with_duplicate_variables(self):
        """Test substitution with duplicate variables in template."""
        validator = PromptVariableValidator()
        template = "From {schema}, use {schema}"
        variables = {'schema': 'public'}
        result = validator.substitute_variables(template, variables)
        assert result == "From public, use public"
    
    def test_substitution_missing_variable_fails(self):
        """Test that substitution fails when required variable is missing."""
        validator = PromptVariableValidator()
        template = "SELECT * FROM {table_name} WHERE id = {record_id}"
        variables = {'table_name': 'users'}  # missing record_id
        
        with pytest.raises(ValueError) as exc_info:
            validator.substitute_variables(template, variables)
        
        assert 'record_id' in str(exc_info.value)
    
    def test_substitution_non_string_template_fails(self):
        """Test that non-string template fails."""
        validator = PromptVariableValidator()
        with pytest.raises(ValueError):
            validator.substitute_variables(123, {})
    
    def test_substitution_non_dict_variables_fails(self):
        """Test that non-dict variables fails."""
        validator = PromptVariableValidator()
        template = "SELECT * FROM {table_name}"
        with pytest.raises(ValueError):
            validator.substitute_variables(template, ["users"])


class TestSubstitutionValidation:
    """Test validation before substitution."""
    
    def test_validate_substitution_success(self):
        """Test successful substitution validation."""
        validator = PromptVariableValidator()
        template = "SELECT * FROM {table_name} WHERE id = {record_id}"
        variables = {'table_name': 'users', 'record_id': 1}
        assert validator.validate_substitution(template, variables)
    
    def test_validate_substitution_missing_required_var(self):
        """Test validation fails with missing required variable."""
        validator = PromptVariableValidator()
        template = "SELECT * FROM {table_name} WHERE id = {record_id}"
        variables = {'table_name': 'users'}  # missing record_id
        
        assert not validator.validate_substitution(template, variables)
        assert len(validator.errors) > 0
        assert 'record_id' in validator.errors[0]
    
    def test_validate_substitution_extra_variables_allowed(self):
        """Test that extra variables in dict don't cause validation failure."""
        validator = PromptVariableValidator()
        template = "SELECT * FROM {table_name}"
        variables = {'table_name': 'users', 'extra_var': 'unused'}
        assert validator.validate_substitution(template, variables)


class TestTypeValidation:
    """Test type validation for variables."""
    
    def test_validate_correct_types(self):
        """Test validation with correct variable types."""
        validator = PromptVariableValidator()
        variables = {
            'table_name': 'users',
            'limit': 10,
            'active': True
        }
        expected_types = {
            'table_name': str,
            'limit': int,
            'active': bool
        }
        assert validator.validate_variable_types(variables, expected_types)
    
    def test_validate_incorrect_types(self):
        """Test validation fails with incorrect types."""
        validator = PromptVariableValidator()
        variables = {
            'table_name': 'users',
            'limit': '10'  # should be int, not str
        }
        expected_types = {
            'table_name': str,
            'limit': int
        }
        assert not validator.validate_variable_types(variables, expected_types)
        assert len(validator.errors) > 0
    
    def test_validate_missing_variable_type(self):
        """Test validation fails when variable is missing."""
        validator = PromptVariableValidator()
        variables = {'table_name': 'users'}
        expected_types = {
            'table_name': str,
            'limit': int
        }
        assert not validator.validate_variable_types(variables, expected_types)
    
    def test_validate_type_none_value(self):
        """Test validation with None values."""
        validator = PromptVariableValidator()
        variables = {'table_name': None}
        expected_types = {'table_name': str}
        assert not validator.validate_variable_types(variables, expected_types)


class TestEmptyValueValidation:
    """Test validation of empty values."""
    
    def test_validate_non_empty_strings(self):
        """Test validation of non-empty string variables."""
        validator = PromptVariableValidator()
        variables = {
            'table_name': 'users',
            'query': 'SELECT * FROM users'
        }
        assert validator.validate_variable_not_empty(variables, ['table_name', 'query'])
    
    def test_validate_empty_string_fails(self):
        """Test that empty strings fail non-empty validation."""
        validator = PromptVariableValidator()
        variables = {'table_name': ''}
        assert not validator.validate_variable_not_empty(variables, ['table_name'])
    
    def test_validate_none_fails(self):
        """Test that None values fail non-empty validation."""
        validator = PromptVariableValidator()
        variables = {'table_name': None}
        assert not validator.validate_variable_not_empty(variables, ['table_name'])
    
    def test_validate_empty_list_fails(self):
        """Test that empty lists fail non-empty validation."""
        validator = PromptVariableValidator()
        variables = {'columns': []}
        assert not validator.validate_variable_not_empty(variables, ['columns'])
    
    def test_validate_empty_dict_fails(self):
        """Test that empty dicts fail non-empty validation."""
        validator = PromptVariableValidator()
        variables = {'schema_config': {}}
        assert not validator.validate_variable_not_empty(variables, ['schema_config'])
    
    def test_validate_non_empty_list_passes(self):
        """Test that non-empty lists pass validation."""
        validator = PromptVariableValidator()
        variables = {'columns': ['id', 'name']}
        assert validator.validate_variable_not_empty(variables, ['columns'])
    
    def test_validate_missing_variable(self):
        """Test validation with missing variable."""
        validator = PromptVariableValidator()
        variables = {'table_name': 'users'}
        assert not validator.validate_variable_not_empty(variables, ['missing_var'])


class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    def test_sql_generation_prompt(self):
        """Test validation of SQL generation prompt."""
        validator = PromptVariableValidator()
        template = """
        Generate SQL for the following:
        Schema: {schema}
        Table: {table_name}
        Columns: {columns}
        Natural Language Query: {nl_query}
        """
        variables = {
            'schema': 'public',
            'table_name': 'users',
            'columns': 'id, name, email',
            'nl_query': 'Find all active users'
        }
        
        assert validator.validate_substitution(template, variables)
        result = validator.substitute_variables(template, variables)
        assert 'public' in result
        assert 'users' in result
        assert 'Find all active users' in result
    
    def test_error_accumulation(self):
        """Test that multiple errors are accumulated."""
        validator = PromptVariableValidator()
        template = "Use {123invalid} and {another-bad}"
        
        assert not validator.validate_variables_in_template(template)
        assert len(validator.errors) >= 2
    
    def test_special_values_in_substitution(self):
        """Test substitution with special values."""
        validator = PromptVariableValidator()
        template = "Query: {query}"
        
        # Test with various special characters
        special_values = [
            "'; DROP TABLE users; --",
            "{nested}",
            "SELECT * FROM {table}",
            "Line1\nLine2\nLine3",
        ]
        
        for value in special_values:
            variables = {'query': value}
            result = validator.substitute_variables(template, variables)
            assert value in result
    
    def test_numeric_values_substitution(self):
        """Test substitution with numeric values."""
        validator = PromptVariableValidator()
        template = "SELECT * FROM users LIMIT {limit} OFFSET {offset}"
        variables = {'limit': 10, 'offset': 0}
        
        result = validator.substitute_variables(template, variables)
        assert '10' in result
        assert '0' in result
    
    def test_boolean_values_substitution(self):
        """Test substitution with boolean values."""
        validator = PromptVariableValidator()
        template = "WHERE is_active = {is_active}"
        variables = {'is_active': True}
        
        result = validator.substitute_variables(template, variables)
        assert 'True' in result


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_long_variable_name(self):
        """Test with very long variable name."""
        validator = PromptVariableValidator()
        long_name = 'a' * 1000
        assert validator.validate_variable_format(long_name)
    
    def test_single_character_variable(self):
        """Test with single character variable."""
        validator = PromptVariableValidator()
        assert validator.validate_variable_format('x')
        assert validator.validate_variable_format('_')
    
    def test_underscore_prefixed_variable(self):
        """Test underscore-prefixed variables (common for private vars)."""
        validator = PromptVariableValidator()
        assert validator.validate_variable_format('_private')
        assert validator.validate_variable_format('__dunder__')
    
    def test_template_with_nested_braces(self):
        """Test template with nested braces."""
        validator = PromptVariableValidator()
        # Note: This is a known limitation - regex won't handle nested braces
        template = "Use {config} where format is {json}"
        variables = validator.extract_variables(template)
        assert 'config' in variables
        assert 'json' in variables
    
    def test_unicode_in_variable_values(self):
        """Test substitution with unicode characters."""
        validator = PromptVariableValidator()
        template = "Name: {name}"
        variables = {'name': '日本語テキスト'}
        
        result = validator.substitute_variables(template, variables)
        assert '日本語テキスト' in result
    
    def test_very_large_template(self):
        """Test with very large template."""
        validator = PromptVariableValidator()
        # Create a large template
        template = "SELECT * FROM {table}" * 1000
        variables = {'table': 'users'}
        
        result = validator.substitute_variables(template, variables)
        assert result.count('users') == 1000
    
    def test_variable_name_with_numbers(self):
        """Test variable names containing numbers."""
        validator = PromptVariableValidator()
        assert validator.validate_variable_format('var1')
        assert validator.validate_variable_format('test_2_var')
        assert validator.validate_variable_format('v123')


class TestErrorMessages:
    """Test that error messages are informative."""
    
    def test_missing_variable_error_message(self):
        """Test error message for missing variable."""
        validator = PromptVariableValidator()
        template = "Use {schema} and {table_name}"
        variables = {'schema': 'public'}
        
        assert not validator.validate_substitution(template, variables)
        error_msg = validator.errors[0]
        assert 'table_name' in error_msg
        assert 'Missing' in error_msg
    
    def test_invalid_format_error_message(self):
        """Test error message for invalid variable format."""
        validator = PromptVariableValidator()
        validator.validate_variable_format('123invalid')
        
        error_msg = validator.errors[0]
        assert '123invalid' in error_msg
        assert 'Invalid' in error_msg
    
    def test_type_mismatch_error_message(self):
        """Test error message for type mismatch."""
        validator = PromptVariableValidator()
        variables = {'count': '10'}
        expected_types = {'count': int}
        
        validator.validate_variable_types(variables, expected_types)
        error_msg = validator.errors[0]
        assert 'count' in error_msg
        assert 'str' in error_msg
        assert 'int' in error_msg


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests combining multiple validations."""
    
    def test_full_validation_pipeline(self):
        """Test complete validation pipeline."""
        validator = PromptVariableValidator()
        template = "SELECT {columns} FROM {table_name} LIMIT {limit}"
        
        # Step 1: Validate template format
        assert validator.validate_variables_in_template(template)
        
        # Step 2: Define requirements
        required_vars = validator.extract_variables(template)
        assert set(required_vars) == {'columns', 'table_name', 'limit'}
        
        # Step 3: Prepare variables
        variables = {
            'columns': '*',
            'table_name': 'users',
            'limit': 100
        }
        
        # Step 4: Validate type compliance
        expected_types = {'columns': str, 'table_name': str, 'limit': int}
        assert validator.validate_variable_types(variables, expected_types)
        
        # Step 5: Validate non-empty
        assert validator.validate_variable_not_empty(
            variables, 
            ['columns', 'table_name', 'limit']
        )
        
        # Step 6: Perform substitution
        result = validator.substitute_variables(template, variables)
        assert result == "SELECT * FROM users LIMIT 100"
    
    def test_validation_failure_at_each_step(self):
        """Test that validation properly fails at each step."""
        validator = PromptVariableValidator()
        
        # Step 1: Invalid variable format
        assert not validator.validate_variable_format('123bad')
        
        # Step 2: Invalid template
        validator = PromptVariableValidator()
        assert not validator.validate_variables_in_template("SELECT FROM {123}")
        
        # Step 3: Missing variable
        validator = PromptVariableValidator()
        assert not validator.validate_substitution(
            "SELECT * FROM {table}",
            {}
        )
        
        # Step 4: Type mismatch
        validator = PromptVariableValidator()
        assert not validator.validate_variable_types(
            {'limit': '100'},
            {'limit': int}
        )
        
        # Step 5: Empty value
        validator = PromptVariableValidator()
        assert not validator.validate_variable_not_empty(
            {'table': ''},
            ['table']
        )
