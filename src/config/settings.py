"""
Configuration management for STPA Tool
Handles loading, saving, and managing application settings.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict

from .constants import (
    CONFIG_FILE_JSON, CONFIG_FILE_YAML, DEFAULT_DB_NAME,
    WORKING_BASELINE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    SPLITTER_DEFAULT_SIZES
)


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    name: str = DEFAULT_DB_NAME
    timeout: float = 30.0
    wal_mode: bool = True


@dataclass
class UIConfig:
    """User interface configuration settings."""
    window_width: int = WINDOW_MIN_WIDTH
    window_height: int = WINDOW_MIN_HEIGHT
    window_maximized: bool = False
    splitter_sizes: list = None
    current_soi_id: Optional[str] = None
    
    def __post_init__(self):
        if self.splitter_sizes is None:
            self.splitter_sizes = SPLITTER_DEFAULT_SIZES.copy()


@dataclass
class DiagramsConfig:
    """Diagrams configuration settings."""
    output_dir: str = "diagrams"


@dataclass
class AppConfig:
    """Main application configuration."""
    working_directory: Optional[str] = None
    current_baseline: str = WORKING_BASELINE
    database: DatabaseConfig = None
    ui: UIConfig = None
    diagrams: DiagramsConfig = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.ui is None:
            self.ui = UIConfig()
        if self.diagrams is None:
            self.diagrams = DiagramsConfig()


class ConfigManager:
    """
    Manages application configuration loading and saving.
    """
    
    def __init__(self, working_directory: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            working_directory: Path to working directory
        """
        self.working_directory = working_directory
        self._config = AppConfig()
        
        if working_directory:
            self._config.working_directory = str(working_directory)
    
    @property
    def config(self) -> AppConfig:
        """Get current configuration."""
        return self._config
    
    def load_config(self, config_path: Optional[Path] = None) -> bool:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file (optional)
            
        Returns:
            True if configuration was loaded successfully
        """
        if config_path is None:
            config_path = self._find_config_file()
        
        if not config_path or not config_path.exists():
            return False
        
        try:
            if config_path.suffix.lower() == '.json':
                return self._load_json_config(config_path)
            elif config_path.suffix.lower() in ['.yaml', '.yml']:
                return self._load_yaml_config(config_path)
            else:
                return False
        except Exception:
            return False
    
    def save_config(self, config_path: Optional[Path] = None, format: str = 'json') -> bool:
        """
        Save configuration to file.
        
        Args:
            config_path: Path to save configuration (optional)
            format: Configuration format ('json' or 'yaml')
            
        Returns:
            True if configuration was saved successfully
        """
        if config_path is None:
            if not self.working_directory:
                return False
            
            filename = CONFIG_FILE_JSON if format == 'json' else CONFIG_FILE_YAML
            config_path = self.working_directory / filename
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == 'json':
                return self._save_json_config(config_path)
            elif format == 'yaml':
                return self._save_yaml_config(config_path)
            else:
                return False
        except Exception:
            return False
    
    def update_working_directory(self, working_directory: Path) -> None:
        """
        Update working directory.
        
        Args:
            working_directory: New working directory path
        """
        self.working_directory = working_directory
        self._config.working_directory = str(working_directory)
    
    def update_ui_state(self, **kwargs) -> None:
        """
        Update UI configuration state.
        
        Args:
            **kwargs: UI configuration parameters
        """
        for key, value in kwargs.items():
            if hasattr(self._config.ui, key):
                setattr(self._config.ui, key, value)
    
    def get_database_path(self) -> Optional[Path]:
        """
        Get full path to database file.
        
        Returns:
            Path to database file or None if working directory not set
        """
        if not self.working_directory:
            return None
        
        return self.working_directory / self._config.database.name
    
    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in working directory."""
        if not self.working_directory:
            return None
        
        # Try JSON first, then YAML
        for filename in [CONFIG_FILE_JSON, CONFIG_FILE_YAML]:
            config_path = self.working_directory / filename
            if config_path.exists():
                return config_path
        
        return None
    
    def _load_json_config(self, config_path: Path) -> bool:
        """Load JSON configuration file."""
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        self._config = self._dict_to_config(data)
        return True
    
    def _load_yaml_config(self, config_path: Path) -> bool:
        """Load YAML configuration file."""
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        self._config = self._dict_to_config(data)
        return True
    
    def _save_json_config(self, config_path: Path) -> bool:
        """Save configuration as JSON."""
        data = self._config_to_dict()
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    
    def _save_yaml_config(self, config_path: Path) -> bool:
        """Save configuration as YAML."""
        data = self._config_to_dict()
        
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
        
        return True
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self._config)
    
    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to configuration object."""
        # Extract database config
        db_data = data.get('database', {})
        db_config = DatabaseConfig(
            name=db_data.get('name', DEFAULT_DB_NAME),
            timeout=db_data.get('timeout', 30.0),
            wal_mode=db_data.get('wal_mode', True)
        )
        
        # Extract UI config
        ui_data = data.get('ui', {})
        ui_config = UIConfig(
            window_width=ui_data.get('window_width', WINDOW_MIN_WIDTH),
            window_height=ui_data.get('window_height', WINDOW_MIN_HEIGHT),
            window_maximized=ui_data.get('window_maximized', False),
            splitter_sizes=ui_data.get('splitter_sizes', SPLITTER_DEFAULT_SIZES.copy()),
            current_soi_id=ui_data.get('current_soi_id')
        )
        
        # Extract Diagrams config
        diagrams_data = data.get('diagrams', {})
        diagrams_config = DiagramsConfig(
            output_dir=diagrams_data.get('output_dir', "diagrams")
        )
        
        # Create main config
        return AppConfig(
            working_directory=data.get('working_directory'),
            current_baseline=data.get('current_baseline', WORKING_BASELINE),
            database=db_config,
            ui=ui_config,
            diagrams=diagrams_config
        )