import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

from .tool_impl import available_tool_implementations

from .ai_config import (
    default_model,
    system_prompt,
    temperature,
    max_tokens, 
    top_k,
    top_p,
    stop_sequences,
    safety_settings,
)
from shared.logger import setup_logger

logger = setup_logger("gemini_ai")

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY environment variable not set.")
        genai_configured = False
    else:
        genai.configure(api_key=api_key)
        genai_configured = True
except Exception as e:
    logger.error(f"Failed to configure Gemini client: {e}")
    genai_configured = False

try:
    if genai_configured:
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            top_k=top_k,
            top_p=top_p,
            stop_sequences=stop_sequences if stop_sequences else None,
        )
        generative_model = genai.GenerativeModel(
            model_name=default_model,
            system_instruction=system_prompt,
            safety_settings=safety_settings,
            tools=available_tool_implementations,
            generation_config=generation_config
        )
        logger.info(f"Gemini model '{default_model}' initialized with tools: {[f.__name__ for f in available_tool_implementations]}")
    else:
        generative_model = None
        logger.warning("Gemini model not initialized due to configuration issues.")

except Exception as e:
    logger.error(f"Failed to initialize GenerativeModel: {e}", exc_info=True)
    generative_model = None


def get_response_with_function_calling(prompt: str) -> str:
    """
    Gets a response from Gemini using a ChatSession for robust automatic
    function calling.
    """
    if not genai_configured:
        return "Error: Gemini AI client is not configured. Check API key."
    if not generative_model:
         return "Error: Gemini AI model failed to initialize."

    try:
        chat = generative_model.start_chat(enable_automatic_function_calling=True)
        logger.info(f"Sending prompt to Gemini ChatSession: '{prompt}'")
        response = chat.send_message(prompt)

        logger.debug(f"Gemini ChatSession Raw Response: {response}")

        if not response.candidates:
             logger.warning(f"Gemini response blocked or empty for prompt: '{prompt}'. Reason: {response.prompt_feedback}")
             block_reason = "Unknown"
             feedback = getattr(response, 'prompt_feedback', None)
             if feedback and hasattr(feedback, 'block_reason'):
                  block_reason = str(feedback.block_reason)
             elif hasattr(response, '_raw_response'): 
                 raw_feedback = getattr(response._raw_response, 'prompt_feedback', None)
                 if raw_feedback and hasattr(raw_feedback, 'block_reason'):
                     block_reason = str(raw_feedback.block_reason)

             return f"Sorry, I couldn't generate a response. (Reason: {block_reason})"

        final_text = response.text
        logger.info(f"Gemini ChatSession final response: {final_text}")

        if hasattr(response, 'function_calls') and response.function_calls:
             logger.warning(f"Final response object unexpectedly contains function_calls: {response.function_calls}")

        return final_text.strip()

    except ConnectionError as e:
        logger.error(f"Network error connecting to Gemini: {e}")
        return "Error: Could not connect to the AI service."
    except AttributeError as e:
         logger.error(f"Attribute error processing Gemini response: {e}", exc_info=True)
         last_response_str = f"Last response state: {response}" if 'response' in locals() else "Response object not available."
         logger.error(last_response_str)
         return f"An internal error occurred processing the AI response."
    except Exception as e:
        logger.error(f"An unexpected error occurred in Gemini chat interaction: {e}", exc_info=True)
        last_response_str = f"Last response state: {response}" if 'response' in locals() else "Response object not available."
        logger.error(last_response_str)
        return f"An unexpected error occurred while processing your request with the AI."