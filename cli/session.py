from typing import Optional, Dict, Any
import shutil

class SessionState:
    
    def __init__(self):
        self.is_interactive = False
        self.current_user: Optional[Dict[str, Any]] = None
        self.last_command_success = True
        self.history = []
        
    def set_user(self, user_data: Dict[str, Any]):
        self.current_user = user_data
        
    def clear_user(self):
        self.current_user = None
        
    def get_prompt_symbol(self) -> str:
        return "jars ❯ " 

session = SessionState()
