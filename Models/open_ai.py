import Constants.settings
import openai

openai.api_key = Constants.settings.OPEN_AI_API_KEY


def embed(text: str, model='text-embedding-ada-002'):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model=model)['data'][0]['embedding']


def generate_completion(prompt: str, temperature: float = 0.0, n: int = 1, max_tokens: int = 2000, model: str = "gpt-3.5-turbo") -> str:
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
        n=n,
        stop="###",
        temperature=temperature,
    )
    return response


def generate_chat_completion(system_prompt: str, user_prompt: str, temperature: float = 0.0, n: int = 1, max_tokens: int = 2000, model: str = "gpt-3.5-turbo") -> str:
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": {system_prompt}
            },
            {
                "role": "user",
                "content": {user_prompt}
            }
        ],
        max_tokens=max_tokens,
        n=n,
        stop="###",
        temperature=temperature,
    )
    return response

