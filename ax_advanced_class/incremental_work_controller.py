from typing import Dict, List, Optional

class IncrementalWorkController:
    """
    Scenario 7: Incremental Work Controller
    
    Enforces the "One Feature at a Time" rule to prevent context overflow 
    and "one-shotting" attempts.
    """
    
    def __init__(self):
        self.current_feature: Optional[Dict] = None

    def start_feature_session(self, feature: Dict) -> bool:
        """
        Locks the session to a specific feature.
        """
        if self.current_feature:
            print(f"Error: Already working on {self.current_feature['id']}")
            return False
            
        print(f"Starting work on feature: {feature['id']}")
        self.current_feature = feature
        return True

    def check_scope_violation(self, changed_files: List[str]) -> bool:
        """
        Checks if the agent is modifying files unrelated to the current feature.
        (Optional advanced implementation)
        """
        # TODO: Implement scope checking logic
        return False
        
    def complete_feature(self) -> None:
        """Unlocks the session."""
        self.current_feature = None
