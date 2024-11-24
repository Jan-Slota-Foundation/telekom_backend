from openai import OpenAI
import os
from typing import Optional, List, Dict, Tuple, Union
import json
from datetime import datetime
import tiktoken

class TokenAnalyzer:
    """A utility class to analyze token usage using tiktoken."""
    
    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        self.encoding = tiktoken.encoding_for_model(model_name)
        
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a piece of text."""
        return len(self.encoding.encode(text))
    
    def analyze_chat_messages(self, messages: List[Dict[str, str]]) -> Dict[str, int]:
        """Analyze token usage in chat messages."""
        per_message_tokens = []
        
        for message in messages:
            message_tokens = self.count_tokens(message['content'])
            total_tokens = message_tokens + 4  # Message overhead
            if message['role'] == 'system':
                total_tokens += 2  # System message overhead
            per_message_tokens.append({
                'role': message['role'],
                'content_tokens': message_tokens,
                'total_tokens': total_tokens
            })
        
        return {
            'messages': per_message_tokens,
            'total_tokens': sum(m['total_tokens'] for m in per_message_tokens)
        }
    
    def estimate_cost(self, token_count: int) -> Dict[str, float]:
        """Estimate API cost based on token count."""
        prices = {
            "gpt-4-turbo-preview": {
                "input": 0.01,
                "output": 0.03
            },
            "gpt-4": {
                "input": 0.03,
                "output": 0.06
            },
            "gpt-3.5-turbo": {
                "input": 0.0010,
                "output": 0.0020
            }
        }
        
        if self.model_name not in prices:
            return {"error": f"Price not available for model {self.model_name}"}
        
        price_per_1k = prices[self.model_name]
        input_cost = (token_count / 1000) * price_per_1k["input"]
        output_cost = (token_count / 1000) * price_per_1k["output"]
        
        return {
            "token_count": token_count,
            "estimated_input_cost": round(input_cost, 4),
            "estimated_output_cost": round(output_cost, 4),
            "total_estimated_cost": round(input_cost + output_cost, 4)
        }

class ContextAwareChatClient:
    def __init__(
        self, 
        file1_path: str,
        file2_path: str,
        model: str = "gpt-4-turbo-preview",
        max_output_tokens: int = 4096,
        max_total_tokens: int = 128000
    ):
        """
        Initialize the context-aware chat client with two files.
        
        Args:
            file1_path (str): Path to the first context file
            file2_path (str): Path to the second context file
            model (str): The OpenAI model to use
            max_output_tokens (int): Maximum tokens for model response
            max_total_tokens (int): Maximum total tokens for context window
        """
        self.file1_path = file1_path
        self.file2_path = file2_path
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.max_total_tokens = max_total_tokens
        self.conversation_history: List[Dict] = []
        
        # Initialize token analyzer
        self.token_analyzer = TokenAnalyzer(model)
        
        # Initialize OpenAI client
        api_key = os.environ.get("API_KEY")
        if not api_key:
            raise ValueError("Please set the API_KEY environment variable")
        self.client = OpenAI(api_key=api_key)
        
        # Load initial context from files
        self.file1_content = self._load_file(file1_path)
        self.file2_content = self._load_file(file2_path)
        
        # Initialize conversation with context
        self._initialize_context()
        
        # Initial token analysis
        initial_analysis = self.token_analyzer.analyze_chat_messages(self.conversation_history)
    
    def _load_file(self, file_path: str) -> str:
        """Load and read a file, with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {e}")
    
    def _initialize_context(self):
        """Initialize the conversation with context from both files."""
        context_prompt = f"""You are tasked with explaining the question asked in the context of provided files, which are static analysis for vulnerabilities of websites. We are trying
        to teach students to have safer websites. REMEMBER, maximum 230 characters.

File 1 ({self.file1_path}):
{self.file1_content}

File 2 ({self.file2_path}):
{self.file2_content}

Please use this context to inform your responses. When referring to content from either file, 
specify which file you're referencing. Maintain awareness of this context throughout our conversation. Keep it short and sweet. Dont hallucinate, if you dont know admit it.
"""
        
        self.conversation_history.append({
            "role": "system",
            "content": context_prompt
        })
    
    def _truncate_history_if_needed(self, new_message_tokens: int):
        """Truncate conversation history if needed while preserving context."""
        current_analysis = self.token_analyzer.analyze_chat_messages(self.conversation_history)
        total_needed = current_analysis['total_tokens'] + new_message_tokens
        
        if total_needed > self.max_total_tokens:
            # Keep system message and last 3 messages
            system_message = self.conversation_history[0]
            recent_messages = self.conversation_history[-3:]
            
            # Reset history
            self.conversation_history = [system_message] + recent_messages
            
            new_analysis = self.token_analyzer.analyze_chat_messages(self.conversation_history)
            print(f"History truncated. New token count: {new_analysis['total_tokens']}")
    
    def get_token_usage(self) -> Dict[str, Union[int, float, Dict]]:
        """Get detailed token usage analysis."""
        analysis = self.token_analyzer.analyze_chat_messages(self.conversation_history)
        percentage_used = (analysis['total_tokens'] / self.max_total_tokens) * 100
        cost_estimate = self.token_analyzer.estimate_cost(analysis['total_tokens'])
        
        return {
            "total_tokens": analysis['total_tokens'],
            "percentage_used": round(percentage_used, 2),
            "max_tokens": self.max_total_tokens,
            "remaining_tokens": self.max_total_tokens - analysis['total_tokens'],
            "cost_estimate": cost_estimate
        }
    
    def chat(self, user_message: str, temperature: float = 1.0) -> Optional[str]:
        """Send a message to the chat model while maintaining context."""
        try:
            # Check token count of new message
            new_message_tokens = self.token_analyzer.count_tokens(user_message)
            self._truncate_history_if_needed(new_message_tokens)
            
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Create chat completion
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                max_tokens=self.max_output_tokens,
                temperature=temperature
            )
            
            # Extract and add response to history
            assistant_response = response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            # Get and print token usage
            usage = self.get_token_usage()
            
            return assistant_response
            
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    
    def save_conversation(self, output_path: str):
        """Save the conversation history with token analysis to a JSON file."""
        conversation_data = {
            "timestamp": datetime.now().isoformat(),
            "file1_path": self.file1_path,
            "file2_path": self.file2_path,
            "model": self.model,
            "token_usage": self.get_token_usage(),
            "conversation": self.conversation_history
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2)

# Example usage
if __name__ == "__main__":
    # Example files
    file1_path = "output.csv"
    file2_path = "message.json"

    chat_client = ContextAwareChatClient(
        file1_path,
        file2_path,
        model="gpt-4-mini",
        max_output_tokens=32,
        max_total_tokens=128000
    )
    
    # print("\nInitial token usage:", chat_client.get_token_usage())
    
    # Example conversation loop
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        response = chat_client.chat(user_input)
        if response:
            print(f"\nAssistant: {response}")
    
    # Save conversation with analysis
    chat_client.save_conversation("conversation_history.json")
    