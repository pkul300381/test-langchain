"""
AWS Lambda handler for LangChain Agent
Converts the interactive CLI agent into a serverless function

Usage:
    Deploy this file with langchain-agent.py, llm_config.py, and requirements.txt to AWS Lambda
    
Example event structure:
{
    "query": "What is the current AWS pricing for EC2?",
    "provider": "perplexity",
    "credential_source": "aws"
}
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import LLM configuration
try:
    from llm_config import initialize_llm, select_llm_interactive
except ImportError:
    logger.error("Failed to import llm_config")
    raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for the LangChain agent
    
    Args:
        event: Lambda event containing 'query', 'provider' (optional), 'credential_source' (optional)
        context: Lambda context
    
    Returns:
        Dict with 'statusCode', 'body', and 'response'
    """
    try:
        # Extract parameters from event
        query = event.get('query')
        provider = event.get('provider', os.getenv('LLM_PROVIDER', 'perplexity'))
        credential_source = event.get('credential_source', 'aws')
        conversation_history = event.get('conversation_history', [])
        
        # Validate input
        if not query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required parameter: query'}),
                'response': None
            }
        
        logger.info(f"Processing query with provider: {provider}")
        
        # Initialize LLM
        try:
            llm = initialize_llm(provider, temperature=0, preferred_source=credential_source)
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to initialize LLM: {str(e)}'}),
                'response': None
            }
        
        # Convert conversation history to LangChain messages if provided
        messages = []
        if conversation_history:
            for msg in conversation_history:
                if msg.get('role') == 'user':
                    messages.append(HumanMessage(content=msg.get('content')))
                elif msg.get('role') == 'assistant':
                    messages.append(AIMessage(content=msg.get('content')))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        # Get response from LLM
        logger.info(f"Invoking LLM with {len(messages)} messages in context")
        response = llm.invoke(messages)
        
        # Add response to history
        messages.append(AIMessage(content=response.content))
        
        # Prepare conversation history for return (convert to serializable format)
        updated_history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                updated_history.append({'role': 'user', 'content': msg.content})
            elif isinstance(msg, AIMessage):
                updated_history.append({'role': 'assistant', 'content': msg.content})
        
        logger.info("Query processed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Query processed successfully',
                'provider': provider
            }),
            'response': response.content,
            'conversation_history': updated_history
        }
    
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'}),
            'response': None
        }


# Lambda handler for direct invocation (synchronous)
def sync_invoke(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Synchronous Lambda invocation"""
    return lambda_handler(event, context)


# Optional: Layer handler for scheduled tasks
def scheduled_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler for EventBridge scheduled invocations
    Useful for periodic monitoring or report generation
    """
    logger.info(f"Scheduled invocation triggered at {event.get('time')}")
    
    default_query = "What are the latest AWS infrastructure updates?"
    
    invoke_event = {
        'query': default_query,
        'provider': os.getenv('LLM_PROVIDER', 'perplexity'),
        'credential_source': 'aws'
    }
    
    return lambda_handler(invoke_event, context)


if __name__ == "__main__":
    # Local testing
    test_event = {
        'query': 'What is Amazon EC2?',
        'provider': 'perplexity',
        'credential_source': 'local'
    }
    
    class MockContext:
        request_id = "test-request-id"
        function_name = "langchain-agent-test"
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))
