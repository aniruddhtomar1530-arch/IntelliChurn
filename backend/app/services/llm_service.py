import httpx

from fastapi import HTTPException
from google import genai
from google.genai import errors, types

from app.core.config import settings
from app.schemas import RetentionRequest

GEMINI_TIMEOUT_MS = 25_000


def generate_retention_strategy(request: RetentionRequest) -> str:
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini is not configured. Set GEMINI_API_KEY in the backend environment.",
        )

    customer = request.customer
    factors = "\n".join(
        f"- {factor.feature}: impact {factor.impact:+.3f}" for factor in request.factors[:5]
    )
    prompt = f"""You are a customer-retention analyst. Suggest three specific, ethical,
    non-discriminatory actions for this telecom customer. Do not promise discounts that
    are not authorized. Keep the answer concise and explain how each action addresses
    the churn drivers.

    Contract: {customer.contract}; tenure: {customer.tenure} months;
    monthly charges: {customer.monthly_charges}; churn risk: {request.churn_probability:.0%}.
    Model factors (positive impact increases churn risk):
    {factors}
    """
    try:
        client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(
                timeout=GEMINI_TIMEOUT_MS,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=256,
                thinking_config=types.ThinkingConfig(thinking_level="LOW"),
            ),
        )
    except errors.APIError as exc:
        if exc.code != 504:
            raise HTTPException(
                status_code=502, detail=f"Gemini request failed: {exc}"
            ) from exc
        response = None
    except httpx.TimeoutException:
        response = None

    if response is None:
        if settings.gemini_fallback_model == settings.gemini_model:
            raise HTTPException(
                status_code=504,
                detail="Gemini timed out. Please try again shortly.",
            )
        try:
            response = client.models.generate_content(
                model=settings.gemini_fallback_model,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=256),
            )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504,
                detail="Gemini timed out on both models. Please try again shortly.",
            ) from exc
        except errors.APIError as exc:
            if exc.code == 504:
                raise HTTPException(
                    status_code=504,
                    detail="Gemini timed out on both models. Please try again shortly.",
                ) from exc
            raise HTTPException(
                status_code=502, detail=f"Gemini fallback request failed: {exc}"
            ) from exc

    if not response.text:
        raise HTTPException(status_code=502, detail="Gemini returned an empty response.")
    return response.text
