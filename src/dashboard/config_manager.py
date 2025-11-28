"""
Configuration management for dashboard.

Handles loading pre-configured scenarios, saving custom configurations,
and validation.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


class ConfigurationError(Exception):
    """Configuration validation or loading error."""
    pass


@dataclass
class ScenarioConfig:
    """Parsed scenario configuration."""
    name: str
    description: str
    field_config: Dict
    parameters: Dict
    aco_params: Dict
    visualization: Dict


class ConfigManager:
    """Manages scenario and custom configurations."""

    def __init__(self, scenarios_dir: str = "scenarios"):
        """
        Initialize configuration manager.

        Args:
            scenarios_dir: Directory containing scenario JSON files
        """
        self.scenarios_dir = Path(scenarios_dir)
        self._scenarios_cache = {}

    def load_scenario(self, scenario_name: str) -> ScenarioConfig:
        """
        Load pre-configured scenario.

        Args:
            scenario_name: Name of scenario (small, medium, large)

        Returns:
            ScenarioConfig object

        Raises:
            ConfigurationError: If scenario not found or invalid
        """
        # Check cache first
        if scenario_name in self._scenarios_cache:
            return self._scenarios_cache[scenario_name]

        # Load from file
        scenario_file = self.scenarios_dir / f"{scenario_name}_field.json"

        if not scenario_file.exists():
            raise ConfigurationError(f"Scenario not found: {scenario_name}")

        try:
            with open(scenario_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in {scenario_file}: {e}")

        # Validate
        if not self._validate_config(data):
            raise ConfigurationError(f"Invalid configuration in {scenario_file}")

        # Parse into ScenarioConfig
        config = ScenarioConfig(
            name=data['name'],
            description=data['description'],
            field_config=data['field'],
            parameters=data['parameters'],
            aco_params=data['aco'],
            visualization=data.get('visualization', {})
        )

        # Cache
        self._scenarios_cache[scenario_name] = config

        return config

    def save_configuration(self, config: Dict, filename: str) -> Path:
        """
        Save custom configuration to JSON file.

        Args:
            config: Configuration dictionary
            filename: Output filename (without .json extension)

        Returns:
            Path to saved file

        Raises:
            ConfigurationError: If validation fails
        """
        # Validate
        if not self._validate_config(config):
            raise ConfigurationError("Invalid configuration")

        # Create custom configs directory
        custom_dir = Path("exports/configs")
        custom_dir.mkdir(parents=True, exist_ok=True)

        # Save
        output_file = custom_dir / f"{filename}.json"

        try:
            with open(output_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")

        return output_file

    def load_custom_configuration(self, filepath: str) -> ScenarioConfig:
        """
        Load custom configuration from file.

        Args:
            filepath: Path to configuration JSON file

        Returns:
            ScenarioConfig object

        Raises:
            ConfigurationError: If file not found or invalid
        """
        config_path = Path(filepath)

        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {filepath}")

        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON: {e}")

        # Validate
        if not self._validate_config(data):
            raise ConfigurationError("Invalid configuration")

        # Parse
        config = ScenarioConfig(
            name=data.get('name', 'Custom Configuration'),
            description=data.get('description', ''),
            field_config=data['field'],
            parameters=data['parameters'],
            aco_params=data['aco'],
            visualization=data.get('visualization', {})
        )

        return config

    def _validate_config(self, config: Dict) -> bool:
        """
        Validate configuration structure and values.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid, False otherwise
        """
        # Check required top-level keys
        required_keys = ['field', 'parameters', 'aco']
        if not all(key in config for key in required_keys):
            return False

        # Validate field
        field = config['field']
        required_field_keys = ['width', 'height', 'obstacles']
        if not all(key in field for key in required_field_keys):
            return False

        if field['width'] <= 0 or field['height'] <= 0:
            return False

        # Validate obstacles
        for obs in field['obstacles']:
            required_obs_keys = ['x', 'y', 'width', 'height']
            if not all(key in obs for key in required_obs_keys):
                return False

            # Check within bounds
            if obs['x'] < 0 or obs['y'] < 0:
                return False
            if obs['x'] + obs['width'] > field['width']:
                return False
            if obs['y'] + obs['height'] > field['height']:
                return False
            if obs['width'] <= 0 or obs['height'] <= 0:
                return False

        # Validate parameters
        params = config['parameters']
        required_param_keys = [
            'operating_width', 'turning_radius', 'num_headland_passes',
            'driving_direction', 'obstacle_threshold'
        ]
        if not all(key in params for key in required_param_keys):
            return False

        if params['operating_width'] <= 0:
            return False
        if params['turning_radius'] < 0:
            return False
        if params['num_headland_passes'] < 0:
            return False

        # Validate ACO
        aco = config['aco']
        required_aco_keys = [
            'alpha', 'beta', 'rho', 'q', 'num_ants', 'num_iterations'
        ]
        if not all(key in aco for key in required_aco_keys):
            return False

        if aco['num_ants'] <= 0 or aco['num_iterations'] <= 0:
            return False
        if aco['alpha'] < 0 or aco['beta'] < 0:
            return False
        if aco['rho'] < 0 or aco['rho'] > 1:
            return False

        return True

    def get_available_scenarios(self) -> list:
        """Get list of available pre-configured scenarios."""
        scenarios = []
        for json_file in self.scenarios_dir.glob("*_field.json"):
            scenario_name = json_file.stem.replace('_field', '')
            scenarios.append(scenario_name)
        return sorted(scenarios)
