import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    openai_api_base: str
    openai_api_key: str
    openai_model: str
    doubao_api_endpoint: str
    doubao_api_key: str
    doubao_model: str
    llm_provider: str
    max_iterations: int
    score: int
    input_customer_profile_file: str


def __post_init__(self):
    if self.max_iterations <= 0:
        raise ValueError("MAX_ITERATIONS must be greater than 0")
    if self.score < 0:
        raise ValueError("SCORE must be non-negative")
    if not self.input_customer_profile_file:
        raise ValueError("INPUT_CUSTOMER_PROFILE_FILE cannot be empty" )
    

class ConfigParser:
    """JSON configuration file parser"""
    
    def __init__(self, config_file_path: str ="config.json"):
        """
        Initialize configuration parser

        Args:
            config file_path: configuration file path, default is config.json
        """    
        self.config_file_path = Path(config_file_path)
        self._config_data: Optional[Dict[str, Any]] = None
        self._config: Optional[Config] = None

    def load(self)-> Config:
        """
        Load and parse configuration file

        Returns:
            Config object
            
        Raises:
            FileNotFoundError: Configuration file does not exist
            json.JSONDecodeError: Invalid json format
            KeyError: Missing required configuration items
            ValueError: Inyalid configuration values
        """   
        if not self.config_file_path.exists():
            raise FileNotFoundError(f"config file not found; {self.config_file_path}")
                                    
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
        except json.JSoNDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JsoN format in {self.config_file_path}: {str(e)}",
                e.doc,
                e.pos
            )
        
        # Validate required configuration items
        required_keys = [
            "OPENAI_API_BASE",
            "OPENAI_API_KEY",
            "OPENAI_MODEL",
            "DOUBAO_API_ENDPOINT",
            "DOUBAO_API_KEY",
            "DOUBAO_MODEL",
            "LLM_PROVIDER",
            "MAX_ITERATIONS",
            "SCORE",
            "INPUT_CUSTOMER_PROFILE_FILE"
        ]

        missing_keys = [key for key in required_keys if key not in self._config_data]
        if missing_keys:
            raise KeyError(f"Missing required config keys: {','.join(missing_keys)}")

        # Create Config object
        self._config = Config(
            openai_api_base=self._config_data["OPENAI_API_BASE"],
            openai_api_key=self._config_data["OPENAI_API_KEY"],
            openai_model=self._config_data["OPENAI_MODEL"],
            doubao_api_endpoint=self._config_data["DOUBAO_API_ENDPOINT"],
            doubao_api_key=self._config_data["DOUBAO_API_KEY"],
            doubao_model=self._config_data["DOUBAO_MODEL"],
            llm_provider=self._config_data["LLM_PROVIDER"],
            max_iterations=int(self._config_data["MAX_ITERATIONS"]),
            score=int(self._config_data["SCORE"]),
            input_customer_profile_file=self._config_data["INPUT_CUSTOMER_PROFILE_FILE"]
        )

        return self._config

    def get(self, key: str, default: Any = None)-> Any:
        """
        Get the value of specified configuration item

        Args:
            key: Configuration item name
            default: Default value

        Returns:
            Value of the configuration item or default value if key does not exist    
        """
        if self._config_data is None:
            self.load()
        return self._config_data.get(key, default)

    def get_config(self) -> Config:
        """
        Get configuration object (load first if not loaded)

        Returns:
            Config object
        """
        if self._config is None:
            self.load()
        return self._config
    
    def set_environment_variables(self) -> None:
        """
        Set OpenAI related configuration as environment variables
        """
        if self._config is None:
            self.load()

        os.environ["OPENAI_API_BASE"]= self._config.openai_api_base
        os.environ["OPENAI_API_KEY"]= self._config.openai_api_key
        os.environ["OPENAI_MODEL"]= self._config.openai_model
        os.environ["DOUBAO_API_ENDPOINT"]= self._config.doubao_api_endpoint
        os.environ["DOUBAO_API_KEY"]= self._config.doubao_api_key
        os.environ["DOUBAO_MODEL"]= self._config.doubao_model
        print(f"Environment variables set: OPENAI API_BASE, OPENAI_API_KEY, OPENAI_MODEL, DOUBAO_API_ENDPOINT, DOUBAO_API_KEY, DOUBAO_MODEL")

    def validate_paths(self) -> bool:
        """ 
        Validate if file paths in configuration exist

        Returns:
            True if all paths are yalid, otherwise False
        """
        if self._config is None:
            self.load()

        customer_file_path = Path(self._config.input_customer_profile_file)
        if not customer_file_path.exists():
            print(f"Warning; Customer profile file not found: {customer_file_path}")
            return False
        return True

    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration and save to file

        Args:
            updates: Dictionary of configuration items to update
        """
        if self. _config_data is None:
            self.load()

        self._config_data.update(updates)

        # Save to file
        with open(self.config_file_path, 'w', encoding='utf-g') as f:
            json.dump(self._config_data, f, indent=4, ensure_ascii=False)

        # Reload configuration
        self._config = None
        self.load()
        print(f"Config updated and saved to {self.config_file_path}")

    def __repr__(self) -> str:
        """Return string representation of configuration"""
        if self._config:
            return f"ConfigParser(api_base={self._config.openai_api_base[:50]}..., " \
                   f"max iterations={self._config.max_iterations}, " \
                   f"score={self._config.score}"
        return "ConfigParser(not loaded)"
    

# Singleton pattern global configuration instance
_config_instance: Optional[ConfigParser] = None


def get_config() -> ConfigParser:
    """
    Get global configuration instance (singleton pattern)

    Returns:
        ConfigParser
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigParser()
    return _config_instance

