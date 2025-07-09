import os
import logging
from groq import Groq
import openai
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# Set up logging
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.ai_provider = os.getenv("AI_PROVIDER", "groq").lower()
        self.model_name = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
        self.temperature = float(os.getenv("TEMPERATURE", "0.1"))
        
        # Initialize clients
        self.groq_client = None
        self.openai_client = None
        self.github_client = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI clients based on environment configuration"""
        if self.ai_provider == "groq":
            try:
                groq_api_key = os.getenv("GROQ_API_KEY")
                if not groq_api_key:
                    raise ValueError("GROQ_API_KEY not found in environment variables")
                    
                self.groq_client = Groq(api_key=groq_api_key)
                logger.info(f"Initialized Groq client with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                
        elif self.ai_provider == "openai":
            try:
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment variables")
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                logger.info(f"Initialized OpenAI client with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        
        elif self.ai_provider == "github":
            try:
                github_token = os.getenv("GITHUB_TOKEN")
                if not github_token:
                    raise ValueError("GITHUB_TOKEN not found in environment variables")
                
                endpoint = "https://models.github.ai/inference"
                self.github_client = ChatCompletionsClient(
                    endpoint=endpoint,
                    credential=AzureKeyCredential(github_token),
                )
                logger.info(f"Initialized GitHub Models client with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize GitHub Models client: {e}")
        else:
            logger.error(f"Unsupported AI provider: {self.ai_provider}")

    async def get_response(self, prompt: str) -> str:
        """Get response from configured AI provider"""
        try:
            if self.ai_provider == "groq" and self.groq_client:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model_name,
                    temperature=self.temperature
                )
                return chat_completion.choices[0].message.content
                
            elif self.ai_provider == "openai" and self.openai_client:
                chat_completion = self.openai_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model_name,
                    temperature=self.temperature
                )
                return chat_completion.choices[0].message.content

            elif self.ai_provider == "github" and self.github_client:
                response = self.github_client.complete(
                    messages=[
                        SystemMessage("You are a helpful AI assistant for filling out advertising campaign forms."),
                        UserMessage(prompt)
                    ],
                    temperature=self.temperature,
                    top_p=1.0,
                    model=self.model_name
                )
                return response.choices[0].message.content
                            
            else:
                raise Exception(f"No valid AI client available for provider: {self.ai_provider}")
                
        except Exception as e:
            logger.error(f"Error getting AI response from {self.ai_provider}: {e}")
            raise

    def get_status(self) -> dict:
        """Get status of AI client and basic API health"""
        ai_status = "unknown"
        health_code = 500
        error_msg = None

        try:
            if self.ai_provider == "groq" and self.groq_client:
                # Ping model with dummy prompt
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": "ping"}],
                    model=self.model_name,
                    temperature=0.0
                )
                ai_status = "healthy"
                health_code = 200

            elif self.ai_provider == "openai" and self.openai_client:
                chat_completion = self.openai_client.chat.completions.create(
                    messages=[{"role": "user", "content": "ping"}],
                    model=self.model_name,
                    temperature=0.0
                )
                ai_status = "healthy"
                health_code = 200

            elif self.ai_provider == "github" and self.github_client:
                response = self.github_client.complete(
                    messages=[
                        SystemMessage("Health check."),
                        UserMessage("ping")
                    ],
                    model=self.model_name,
                    temperature=0.0,
                    top_p=1.0
                )
                ai_status = "healthy"
                health_code = 200

            else:
                ai_status = "unavailable"
                health_code = 503

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                health_code = 429
                ai_status = "rate_limited"
            elif "timeout" in error_msg.lower():
                health_code = 504
                ai_status = "timeout"
            else:
                health_code = 500
                ai_status = "error"

        return {
            "ai_provider": self.ai_provider,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "ai_status": ai_status,
            "status_code": health_code,
            "error_message": error_msg
        }

    def is_available(self) -> bool:
        """Check if AI client is available"""
        if self.ai_provider == "groq" and self.groq_client:
            return True
        elif self.ai_provider == "openai" and self.openai_client:
            return True
        elif self.ai_provider == "github" and self.github_client:
            return True
        return False