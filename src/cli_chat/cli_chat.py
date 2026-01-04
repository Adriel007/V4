import subprocess
import signal
import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.api_llm.api_llm import ApiLLM
from src.prompt import __PROMPTS__

SESSION = "mysession"

api_llm = ApiLLM()
api_llm.open_deepseek()
api_llm.login_deepseek()
time.sleep(1)
api_llm.delete_all_chats()
time.sleep(1)
api_llm.new_chat()
time.sleep(1)
api_llm.search_mode()
api_llm.send_message(__PROMPTS__["main"])
api_llm.get_latest_answer()

print("\033c", end="")
MODE = input("Choose mode (voice/voice_better/text): ").strip().lower()

def cleanup(*_):
    subprocess.run(
        ["tmux", "kill-session", "-t", SESSION],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

subprocess.run(
    [
        "tmux",
        "new-session",
        "-d",
        "-s",
        SESSION,
        "bash", 
    ],
    check=True,
)

time.sleep(0.1)
subprocess.run(
    ["tmux", "send-keys", "-t", f"{SESSION}:0.0", "export PS1=''; stty -echo; clear", "C-m"],
    check=True,
)

subprocess.run(
    [
        "tmux",
        "split-window",
        "-v",
        "-p",
        "50",
        "-t",
        SESSION,
        f"python3 ./src/cli_chat/cli_chat_interface.py --mode {MODE}", #"2>> ./tmp/fardo_errors.log" <- to log tmux erros
    ],
    check=True,
)

subprocess.run(
    ["tmux", "select-pane", "-D", "-t", SESSION],
    check=True,
)

subprocess.run(["tmux", "attach-session", "-t", SESSION])