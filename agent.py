from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from tools.file_reader import read_file
from tools.knowledge_loader import load_knowledge
from agents.router import route_request
from core.intents import handle_identity


# Fast brain
general_llm = ChatOllama(
    model="qwen2.5:3b",
    temperature=0.25,
    keep_alive="30m"
)

# Engineering brain
coding_llm = ChatOllama(
    model="qwen2.5-coder:7b",
    temperature=0.2,
    keep_alive="30m"
)


identity = Path("identity/personality.md").read_text(
    encoding="utf-8"
)

knowledge = load_knowledge()


def choose_model(user_input):
    specialist = route_request(user_input)

    if specialist == "CODING":
        return coding_llm, specialist

    return general_llm, specialist


print("🤖 Ahmed AI v0.4")
print("⚡ Dual Brain Mode")
print("اكتب exit للخروج\n")


while True:

    user_input = input("أحمد: ")

    if user_input.lower() == "exit":
        break


    direct_answer = handle_identity(user_input)

    if direct_answer:
        print("\n🤖 Ahmed AI:\n")
        print(direct_answer)
        print("\n" + "-" * 50)
        continue

    llm, specialist = choose_model(user_input)


    print(f"\n🔀 Specialist: {specialist}")
    print("🤖 Ahmed AI:\n")


    messages = [
        SystemMessage(
            content=f"""
أنت Ahmed AI، مساعد أحمد الذكي.

قواعد مهمة:
- أحمد عبد الخالق هو المستخدم وصاحب النظام.
- أنت لست أحمد.
- تحدث باللهجة المصرية الطبيعية.
- كن ودودًا مثل صديق ومهندس خبير.
- لا تستخدم لهجات أخرى.

معلومات أحمد:
{identity}

المعرفة المتاحة:
{knowledge}

أجب بشكل عملي ومفيد.
"""
        ),
        HumanMessage(content=user_input)
    ]


    for chunk in llm.stream(messages):
        print(chunk.content, end="", flush=True)


    print("\n")
    print("-" * 50)
