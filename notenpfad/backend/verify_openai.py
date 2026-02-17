import os
import openai

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("SKIPPING TEST: No OPENAI_API_KEY found in environment.")
else:
    print(f"Testing OpenAI with key: {api_key[:5]}...")
    client = openai.OpenAI(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a test bot."},
                {"role": "user", "content": "Say 'Connection Successful'"}
            ]
        )
        print("RESPONSE:", completion.choices[0].message.content)
    except Exception as e:
        print("ERROR:", e)
