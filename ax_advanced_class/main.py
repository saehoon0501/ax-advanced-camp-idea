import sys
from ax_advanced_class.initializer_agent import InitializerAgent
from ax_advanced_class.coding_agent import CodingAgent

def main():
    """
    Main entry point for the Long-Running Agent Harness.
    """
    if len(sys.argv) < 2:
        print("Usage: python main.py [init|run] [args...]")
        return

    command = sys.argv[1]
    
    # Mock LLM Client (Replace with actual client initialization)
    model_client = None 

    if command == "init":
        print("Starting Initializer Agent...")
        agent = InitializerAgent(model_client)
        # agent.initialize_project(...)
        print("Initializer Agent finished (Mock).")
        
    elif command == "run":
        print("Starting Coding Agent Session...")
        agent = CodingAgent(model_client)
        # agent.run_session()
        print("Coding Agent Session finished (Mock).")
        
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
