"""Unified LLM client — routes to Anthropic or OpenRouter.

OpenRouter uses the OpenAI-compatible API format, so we use the openai
SDK pointed at https://openrouter.ai/api/v1.
"""
import base64
import json
import re
import anthropic
from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Free OpenRouter models with vision support (tried in order, first success wins)
OPENROUTER_FREE_VISION_MODELS = [
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
]

OPENROUTER_FREE_TEXT_MODELS = [
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
]

ANTHROPIC_MODELS = [
    "claude-sonnet-4-6",
    "claude-opus-4-7",
    "claude-haiku-4-5-20251001",
]


def chat(provider, api_key, model, system_prompt, user_prompt,
         max_tokens=16000, cache_system=False):
    """Send a chat completion. Returns the response text string."""
    if provider == "anthropic":
        return _anthropic_chat(api_key, model, system_prompt, user_prompt,
                               max_tokens, cache_system)
    else:
        return _openrouter_chat(api_key, model, system_prompt, user_prompt, max_tokens)


def vision_describe(provider, api_key, model, img_bytes, img_ext, prompt_text,
                    max_tokens=600):
    """Describe an image. Returns the description string."""
    if provider == "anthropic":
        return _anthropic_vision(api_key, img_bytes, img_ext, prompt_text, max_tokens)
    else:
        return _openrouter_vision(api_key, model, img_bytes, img_ext, prompt_text, max_tokens)


# ── Anthropic ─────────────────────────────────────────────────────────────────

def _anthropic_chat(api_key, model, system_prompt, user_prompt, max_tokens, cache_system):
    client = anthropic.Anthropic(api_key=api_key)
    system = [{
        "type": "text",
        "text": system_prompt,
        **({"cache_control": {"type": "ephemeral"}} if cache_system else {}),
    }]
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(b.text for b in msg.content if hasattr(b, "text")).strip()


def _anthropic_vision(api_key, img_bytes, img_ext, prompt_text, max_tokens):
    client = anthropic.Anthropic(api_key=api_key)
    media_type = _ext_to_media_type(img_ext)
    b64 = base64.standard_b64encode(img_bytes).decode()
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
            {"type": "text", "text": prompt_text},
        ]}],
    )
    return resp.content[0].text.strip()


# ── OpenRouter ────────────────────────────────────────────────────────────────

def _openrouter_chat(api_key, model, system_prompt, user_prompt, max_tokens):
    client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    resp = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
    )
    content = resp.choices[0].message.content
    if content is None:
        finish = resp.choices[0].finish_reason
        raise RuntimeError(f"Model returned no content (finish_reason: {finish}). Try a different model.")
    return _strip_reasoning(content)


def _openrouter_vision(api_key, model, img_bytes, img_ext, prompt_text, max_tokens):
    client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
    media_type = _ext_to_media_type(img_ext)
    b64 = base64.standard_b64encode(img_bytes).decode()
    data_url = f"data:{media_type};base64,{b64}"
    messages = [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": data_url}},
        {"type": "text", "text": prompt_text},
    ]}]
    # Try requested model first, then fall back through the vision model list
    candidates = [model] + [m for m in OPENROUTER_FREE_VISION_MODELS if m != model]
    errors = []
    for candidate in candidates:
        try:
            resp = client.chat.completions.create(
                model=candidate,
                max_tokens=max_tokens,
                messages=messages,
            )
            content = resp.choices[0].message.content
            if content:
                cleaned = _strip_reasoning(content)
                if cleaned:
                    return cleaned
            errors.append(f"{candidate}: returned empty content")
        except Exception as e:
            errors.append(f"{candidate}: {e}")
            continue
    raise RuntimeError("All vision models failed:\n" + "\n".join(errors))


def _strip_reasoning(text):
    """Remove <think>...</think> and similar reasoning blocks some models prepend."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


def _ext_to_media_type(ext):
    return {"jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp"}.get(ext.lower(), "image/jpeg")
