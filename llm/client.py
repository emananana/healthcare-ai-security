"""Small Groq adapter shared by enterprise/red/blue integrations.

No retries or hidden fallback: one complete() call makes at most one request.
Never expose provider error bodies, request headers or credentials to the UI.
"""
import httpx


class LLMError(RuntimeError):
    """Safe, user-visible provider/validation failure; not a defense decision."""


class GroqClient:
    def __init__(self, api_key: str, *, transport=None):
        if not api_key.strip():
            raise ValueError("A Groq API key is required")
        self._api_key = api_key
        self._transport = transport

    def complete(self, *, model: str, messages: list[dict], tools=None,
                 tool_choice="none") -> dict:
        """Return one assistant message. Agents must validate its task-specific schema."""
        payload = {
            "model": model, "messages": messages, "temperature": 0,
            "max_completion_tokens": 1024, "stream": False,
        }
        if tools:
            payload.update(tools=tools, tool_choice=tool_choice,
                           parallel_tool_calls=False)
        try:
            with httpx.Client(timeout=httpx.Timeout(10, connect=3),
                              transport=self._transport) as client:
                response = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                )
            if response.status_code == 429:
                raise LLMError("Groq rate limit reached. Wait before retrying.")
            if response.status_code in {401, 403}:
                raise LLMError("Groq access failed. Check the server's API key and model access.")
            if response.is_error:
                raise LLMError("Groq could not complete this request. Check the configured model or retry later.")
            data = response.json()
            choice = data["choices"][0]
            message = choice["message"]
            if choice.get("finish_reason") not in {"stop", "tool_calls"}:
                raise LLMError("The model response was incomplete. No further action was executed.")
            if not isinstance(message, dict) or message.get("role") != "assistant":
                raise ValueError("Invalid assistant message")
            return message
        except httpx.TimeoutException:
            raise LLMError("Groq timed out. No automatic retry was made.") from None
        except httpx.HTTPError:
            raise LLMError("Could not connect to Groq. Check the backend connection.") from None
        except (ValueError, KeyError, IndexError, TypeError):
            raise LLMError("Groq returned an invalid response.") from None
