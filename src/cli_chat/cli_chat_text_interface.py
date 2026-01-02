import subprocess
import sys
import time
import threading
import random
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.api_llm.api_llm import ApiLLM
from src.prompt import __PROMPTS__

api_llm = ApiLLM()
last_response = 0
SESSION = "mysession"
INPUT_PANE = "0.1"
OUTPUT_PANE = "0.0"
ANIMATION_CLI = "python3 ./src/cli_animation/cli_animation.py"

is_talking = False

def focus_input_pane():
    subprocess.run(["tmux", "select-pane", "-t", f"{SESSION}:{INPUT_PANE}"], check=True)

def send_to_output(cmd: str):
    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:{OUTPUT_PANE}", cmd, "C-m"], check=True)

def exit_global():
    subprocess.run(["tmux", "kill-session", "-t", SESSION], stderr=subprocess.DEVNULL)
    sys.exit(0)

def blink_interval():
    while True:
        if not is_talking:
            send_to_output(f"{ANIMATION_CLI} --left closed --right closed --mouth closed")
            time.sleep(random.uniform(0.1, 0.2))
            send_to_output(f"{ANIMATION_CLI} --left open --right open --mouth closed")
        time.sleep(random.uniform(4, 8))

def initiative_interval():
    global last_response
    while True:
        time.sleep(random.uniform(120, 300))  # 2~5 minutes
        if not is_talking and last_response >= time.time() - 300:  # only if no response in last 5 minutes
            prompt = f"{__PROMPTS__['main']} {__PROMPTS__['initiative']}"
            api_llm.send_message(prompt)
            response = api_llm.get_latest_answer()
            if response:
                print(f"\nFardo: {response}")
                said_animation(response)
                print("You: ", end='', flush=True)

def said_animation(text: str):
    global is_talking
    is_talking = True
    
    iterations = max(2, len(text) // 4) 
    
    for _ in range(iterations):
        send_to_output(f"{ANIMATION_CLI} --left open --right open --mouth open")
        time.sleep(0.15)
        send_to_output(f"{ANIMATION_CLI} --left open --right open --mouth closed")
        time.sleep(0.15)
        
    is_talking = False
    global last_response
    last_response = time.time()
    focus_input_pane()

def idle_animation():
    send_to_output(f"{ANIMATION_CLI} --left open --right open --mouth closed")
    focus_input_pane()

def send_message(message: str):
    prompt = f"{__PROMPTS__['main']} {__PROMPTS__['user']} {message}"
    api_llm.send_message(prompt)
    response = api_llm.get_latest_answer()
    if response:
        print(f"Fardo: {response}")
        said_animation(response)
    else:
        print(f"Fardo: Desculpe, algum erro ocorreu")

def main():
    threading.Thread(target=blink_interval, daemon=True).start()
    threading.Thread(target=initiative_interval, daemon=True).start()

    try:
        idle_animation()
    except subprocess.CalledProcessError:
        print(f"Erro: '{SESSION}' not found.")
        return

    while True:
        try:
            cmd = input("You: ").strip()
            if cmd.lower() in ("exit", "quit"):
                exit_global()
            if cmd:
                try:
                    send_message(cmd)
                except Exception as e:
                    print(f"[ERROR] {str(e)}")
        except (EOFError, KeyboardInterrupt):
            exit_global()

if __name__ == "__main__":
    main()