from langchain_openai import ChatOpenAI

from app.core.config import get_settings

PROVIDER_BASE_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "openai": "https://api.openai.com/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
}

PROVIDER_DEFAULT_MODELS = {
    "deepseek": "deepseek-chat",
    "qwen": "qwen-plus",
    "openai": "gpt-4o-mini",
    "zhipu": "glm-4-flash",
}


def get_chat_model(stream_usage: bool = False) -> ChatOpenAI:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    base_url = settings.llm_base_url or PROVIDER_BASE_URLS.get(provider, settings.llm_base_url)
    model = settings.llm_model or PROVIDER_DEFAULT_MODELS.get(provider, "gpt-4o-mini")
    api_key = settings.llm_api_key or "not-set"

    kwargs = {
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "temperature": settings.llm_temperature,
    }
    if stream_usage:
        kwargs["stream_usage"] = True
    return ChatOpenAI(**kwargs)


def current_provider_model() -> tuple[str, str]:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    model = settings.llm_model or PROVIDER_DEFAULT_MODELS.get(provider, "gpt-4o-mini")
    return provider, model