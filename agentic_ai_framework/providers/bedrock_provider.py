import json
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from .base_llm_provider import BaseLLMProvider, ModelInfo, GenerationConfig, Message, GenerationResponse

logger = logging.getLogger(__name__)

class BedrockProvider(BaseLLMProvider):
    """AWS Bedrock LLM Provider"""
    
    def __init__(self, provider_name: str, config: Dict[str, Any]):
        super().__init__(provider_name, config)
        self.client = None
    
    async def initialize(self) -> bool:
        """Initialize the Bedrock provider"""
        try:
            # Import boto3 here to avoid import issues
            import boto3
            
            # Configure AWS credentials and region
            region_name = self.config.get('region_name', 'us-east-1')
            aws_access_key_id = self.config.get('aws_access_key_id')
            aws_secret_access_key = self.config.get('aws_secret_access_key')
            
            # Create Bedrock client
            if aws_access_key_id and aws_secret_access_key:
                self.client = boto3.client(
                    'bedrock-runtime',
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                # Use default AWS credentials (IAM roles, environment variables, etc.)
                self.client = boto3.client('bedrock-runtime', region_name=region_name)
            
            logger.info(f"Bedrock provider initialized for region: {region_name}")
            self.is_initialized = True
            return True
            
        except ImportError:
            logger.error("boto3 is required for Bedrock provider. Install with: pip install boto3")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if Bedrock provider is healthy"""
        try:
            if not self.client:
                return False
            
            # Test with a simple model list request
            self.client.list_foundation_models()
            return True
            
        except Exception as e:
            logger.error(f"Bedrock health check failed: {e}")
            return False
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Bedrock models"""
        models = [
            ModelInfo(
                name='anthropic.claude-3-sonnet-20240229-v1:0',
                provider=self.provider_name,
                description='Claude 3 Sonnet - Balanced performance and speed',
                context_length=200000,
                max_tokens=4096,
                supports_streaming=True,
                supports_tools=True
            ),
            ModelInfo(
                name='anthropic.claude-3-haiku-20240307-v1:0',
                provider=self.provider_name,
                description='Claude 3 Haiku - Fast and efficient',
                context_length=200000,
                max_tokens=4096,
                supports_streaming=True,
                supports_tools=True
            ),
            ModelInfo(
                name='anthropic.claude-3-opus-20240229-v1:0',
                provider=self.provider_name,
                description='Claude 3 Opus - Most capable model',
                context_length=200000,
                max_tokens=4096,
                supports_streaming=True,
                supports_tools=True
            ),
            ModelInfo(
                name='amazon.titan-text-express-v1',
                provider=self.provider_name,
                description='Amazon Titan Text Express',
                context_length=8192,
                max_tokens=4096,
                supports_streaming=False,
                supports_tools=False
            ),
            ModelInfo(
                name='meta.llama2-13b-chat-v1',
                provider=self.provider_name,
                description='Meta Llama 2 13B Chat',
                context_length=4096,
                max_tokens=2048,
                supports_streaming=True,
                supports_tools=False
            ),
            ModelInfo(
                name='meta.llama3-8b-instruct-v1:0',
                provider=self.provider_name,
                description='Meta Llama 3 8B Instruct',
                context_length=8192,
                max_tokens=4096,
                supports_streaming=True,
                supports_tools=False
            )
        ]
        return models
    
    async def generate_response(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """Generate response using AWS Bedrock"""
        if not self.client:
            raise Exception("Bedrock client not initialized")
        
        config = config or GenerationConfig()
        
        try:
            # Convert messages to Bedrock format
            prompt = self._messages_to_prompt(messages)
            
            # Prepare request body based on model type
            if 'anthropic' in model:
                request_body = self._prepare_anthropic_request(prompt, config)
            elif 'amazon' in model:
                request_body = self._prepare_titan_request(prompt, config)
            elif 'meta' in model:
                request_body = self._prepare_llama_request(prompt, config)
            else:
                # Default to Anthropic format
                request_body = self._prepare_anthropic_request(prompt, config)
            
            # Make request to Bedrock
            response = self.client.invoke_model(
                modelId=model,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            parsed_response = self._parse_response(response_body, model)
            
            return GenerationResponse(
                content=parsed_response['content'],
                model=model,
                provider=self.provider_name,
                usage=parsed_response['usage'],
                finish_reason='stop'
            )
            
        except Exception as e:
            logger.error(f"Bedrock API error: {e}")
            raise Exception(f"Bedrock API error: {e}")
    
    async def generate_response_stream(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using AWS Bedrock"""
        if not self.client:
            raise Exception("Bedrock client not initialized")
        
        config = config or GenerationConfig()
        config.stream = True
        
        try:
            # Convert messages to Bedrock format
            prompt = self._messages_to_prompt(messages)
            
            # Prepare request body based on model type
            if 'anthropic' in model:
                request_body = self._prepare_anthropic_request(prompt, config)
            elif 'amazon' in model:
                request_body = self._prepare_titan_request(prompt, config)
            elif 'meta' in model:
                request_body = self._prepare_llama_request(prompt, config)
            else:
                # Default to Anthropic format
                request_body = self._prepare_anthropic_request(prompt, config)
            
            # Make streaming request to Bedrock
            response = self.client.invoke_model_with_response_stream(
                modelId=model,
                body=json.dumps(request_body)
            )
            
            # Stream response chunks
            for event in response['body']:
                chunk = json.loads(event['chunk']['bytes'].decode())
                if 'content' in chunk:
                    for content_block in chunk['content']:
                        if 'text' in content_block:
                            yield content_block['text']
                            
        except Exception as e:
            logger.error(f"Bedrock streaming API error: {e}")
            raise Exception(f"Bedrock streaming API error: {e}")
    
    def _messages_to_prompt(self, messages: List[Message]) -> str:
        """Convert messages to prompt format"""
        prompt = ""
        for message in messages:
            role = message.role
            content = message.content
            
            if role == 'system':
                prompt += f"System: {content}\n\n"
            elif role == 'user':
                prompt += f"Human: {content}\n\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n\n"
        
        prompt += "Assistant: "
        return prompt
    
    def _prepare_anthropic_request(self, prompt: str, config: GenerationConfig) -> Dict[str, Any]:
        """Prepare request for Anthropic models (Claude)"""
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": config.max_tokens or 1000,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
    
    def _prepare_titan_request(self, prompt: str, config: GenerationConfig) -> Dict[str, Any]:
        """Prepare request for Amazon Titan models"""
        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": config.max_tokens or 1000,
                "temperature": config.temperature,
                "topP": config.top_p,
                "stopSequences": config.stop_sequences or []
            }
        }
    
    def _prepare_llama_request(self, prompt: str, config: GenerationConfig) -> Dict[str, Any]:
        """Prepare request for Meta Llama models"""
        return {
            "prompt": prompt,
            "max_gen_len": config.max_tokens or 1000,
            "temperature": config.temperature,
            "top_p": config.top_p
        }
    
    def _parse_response(self, response_body: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Parse Bedrock response based on model type"""
        try:
            if 'anthropic' in model:
                # Anthropic Claude response
                content = response_body.get('content', [])
                if content and len(content) > 0:
                    text = content[0].get('text', '')
                else:
                    text = ''
                
                return {
                    'content': text,
                    'usage': {
                        'prompt_tokens': response_body.get('usage', {}).get('input_tokens', 0),
                        'completion_tokens': response_body.get('usage', {}).get('output_tokens', 0),
                        'total_tokens': response_body.get('usage', {}).get('input_tokens', 0) + 
                                      response_body.get('usage', {}).get('output_tokens', 0)
                    }
                }
            
            elif 'amazon' in model:
                # Amazon Titan response
                return {
                    'content': response_body.get('results', [{}])[0].get('outputText', ''),
                    'usage': {
                        'prompt_tokens': response_body.get('inputTextTokenCount', 0),
                        'completion_tokens': response_body.get('results', [{}])[0].get('tokenCount', 0),
                        'total_tokens': response_body.get('inputTextTokenCount', 0) + 
                                      response_body.get('results', [{}])[0].get('tokenCount', 0)
                    }
                }
            
            elif 'meta' in model:
                # Meta Llama response
                return {
                    'content': response_body.get('generation', ''),
                    'usage': {
                        'prompt_tokens': response_body.get('prompt_token_count', 0),
                        'completion_tokens': response_body.get('generation_token_count', 0),
                        'total_tokens': response_body.get('prompt_token_count', 0) + 
                                      response_body.get('generation_token_count', 0)
                    }
                }
            
            else:
                # Default parsing
                return {
                    'content': str(response_body),
                    'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
                }
                
        except Exception as e:
            logger.error(f"Error parsing Bedrock response: {e}")
            return {
                'content': str(response_body),
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
            } 