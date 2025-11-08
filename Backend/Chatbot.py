# ========================== Imports ==========================
from groq import Groq                 # Groq API
from json import load, dump           # JSON file handling
import datetime                        # Real-time date and time
from dotenv import dotenv_values       # Load environment variables
from rich import print                 # Pretty printing in terminal

# ========================== Load Environment Variables ==========================
env_vars = dotenv_values(r"c:\Users\user\Desktop\jervisai\.env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# ========================== Initialize Groq Client ==========================
client = Groq(api_key=GroqAPIKey)

# ========================== Chat Log Setup ==========================


# System instructions for chatbot
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""
SystemChatBot =[
    {"role": "system", "content": System}
]

# Load existing chat log or create a new one
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

# ========================== Realtime Information Function ==========================
def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = f"Please use this real-time information if needed, \n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours : {minute} minutes : {second} seconds.\n"
    return data

# ========================== Answer Modifier Function ==========================
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

# ========================== Main ChatBot Function ==========================
def ChatBot(Query):
    """ Send user's query to chatbot and return AI's response """
    try:
        # Load existing chat log
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)

        # Append user's query
        messages.append({"role": "user", "content": Query})

        # Request response from Groq API
        completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "system", "content": RealtimeInformation()}] + messages,  # ✅ system + chat history
    max_tokens=1024,
    temperature=0.7,
    top_p=1,
    stream=True
)

        Answer = ""

        # Process streamed response
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")

        # Append chatbot's response to messages
        messages.append({"role": "assistant", "content": Answer})

        # Save updated chat log
        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)

    except Exception as e:
        print(f"[red]Error:[/red] {e}")
        # Reset chat log and retry
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return ChatBot(Query)

# ========================== Main Program Entry ==========================
if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        print(ChatBot(user_input))