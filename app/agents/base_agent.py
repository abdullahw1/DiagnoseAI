"""
Base agent class providing common interface for all specialized agents.

All agents in the multi-agent pipeline inherit from this base class
to ensure consistent interface and behavior.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent pipeline.
    
    Each agent must implement:
    - process(): Execute the agent's core logic
    - validate_output(): Validate the agent's output
    """
    
    def __init__(self, agent_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Unique identifier for this agent
            config: Optional configuration dictionary
        """
        self.agent_name = agent_name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's core processing logic.
        
        Args:
            input_data: Input data dictionary containing all necessary information
            
        Returns:
            Dictionary containing the agent's output
            
        Raises:
            Exception: If processing fails
        """
        pass
    
    @abstractmethod
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Validate the agent's output to ensure it meets requirements.
        
        Args:
            output: The output dictionary to validate
            
        Returns:
            True if output is valid, False otherwise
        """
        pass
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with timing and error handling.
        
        This method wraps the process() method with:
        - Execution timing
        - Error handling
        - Output validation
        - Logging
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Dictionary containing:
                - success: Boolean indicating success/failure
                - output: Agent output (if successful)
                - error: Error message (if failed)
                - execution_time_ms: Execution time in milliseconds
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Starting execution of {self.agent_name}")
            
            # Process the input
            output = self.process(input_data)
            
            # Validate the output
            if not self.validate_output(output):
                raise ValueError(f"Output validation failed for {self.agent_name}")
            
            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            self.logger.info(
                f"Successfully completed {self.agent_name} in {execution_time_ms}ms"
            )
            
            return {
                'success': True,
                'output': output,
                'error': None,
                'execution_time_ms': execution_time_ms
            }
            
        except Exception as e:
            # Calculate execution time even on failure
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            error_msg = f"Error in {self.agent_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'output': None,
                'error': error_msg,
                'execution_time_ms': execution_time_ms
            }
    
    def get_prompt_template(self) -> str:
        """
        Get the current prompt template for this agent.
        
        This method can be overridden to support versioned prompts
        from the database.
        
        Returns:
            The prompt template string
        """
        return self.config.get('prompt_template', '')
    
    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.agent_name}>"
