import requests
from app.config import LLM_URL

def call_llm(payload, logger):
    try:
        response = requests.post(
            LLM_URL,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": "AzureOpenAIManager123"
            },
            json=payload,
            timeout=1000,
            verify=False
        )

        data = response.json()

        reply = (
            data.get("data", {})
            .get("result", {})
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )

        return reply or "No response from LLM"

    except Exception as e:
        logger.error(f"LLM Error: {str(e)}")
        return "Error communicating with LLM"