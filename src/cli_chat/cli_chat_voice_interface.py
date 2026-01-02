import subprocess
import sys
import time
import threading
import random
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.api_llm.api_llm import ApiLLM
from src.STT.STT import STT
from src.TTS.TTS import TTS
from src.prompt import __PROMPTS__

api_llm = ApiLLM()
last_response = 0
stt = STT(device_index=0, wake_word=None, similarity_threshold=0.7)
tts_engine = TTS()

SESSION = "mysession"
INPUT_PANE = "0.1"
OUTPUT_PANE = "0.0"
ANIMATION_CLI = "python3 ./src/cli_animation/cli_animation.py"

is_talking = False
is_listening = False

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
            initiative_interval()
        time.sleep(random.uniform(4, 8))

def initiative_interval():
    global last_response
    while True:
        time.sleep(random.uniform(120, 300))  # 2~5 minutes
        if not is_talking and last_response >= time.time() - 300:  # only if no response in last 5 minutes
            prompt = f"{__PROMPTS__['main']} {__PROMPTS__['initiative']}"
            process_command(prompt)

def said_animation(text: str):
    global is_talking
    is_talking = True
    iterations = max(3, len(text) // 3) 
    
    for _ in range(iterations):
        if not is_talking: break
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

BLUE = "\033[1;34m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RESET = "\033[0m"
CLEAR_LINE = "\r\033[K"

def wave_animator():
    t = 0
    BLOCKS = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    
    while True:
        if is_listening and not is_talking:
            wave = ""
            for i in range(12):
                amplitude = (math.sin(t + i * 0.5) + 1) / 2
                idx = int(amplitude * (len(BLOCKS) - 1))
                wave += BLOCKS[idx]
            
            sys.stdout.write(f"{CLEAR_LINE}{BLUE}[LISTENING]{RESET} {wave}")
            
        elif is_talking:
            pulse_size = int((math.sin(t * 2) + 1) * 5) + 5
            bar = "█" * pulse_size
            sys.stdout.write(f"{CLEAR_LINE}{GREEN}[TALKING]{RESET} {bar}")
            
        else:
            dots = "." * (int(t * 2) % 4)
            sys.stdout.write(f"{CLEAR_LINE}{YELLOW}[PROCESSING]{RESET} {dots: <3}")
            
        sys.stdout.flush()
        t += 0.3
        time.sleep(0.05)

def on_speech_captured(selected_text, alternatives, raw_response):
    
    if not "fardo" in selected_text.lower():
        return
        
    prompt = f"{__PROMPTS__['main']} {__PROMPTS__['user']} {selected_text}"
    process_command(prompt)

def process_command(text: str):
    global is_listening
    is_listening = False

    api_llm.send_message(text)
    response = api_llm.get_latest_answer()
    
    if response:
        tts_voice = TTS(speed=125, pitch=36, gap=7, amplitude=105)
        audio_path = tts_voice.generate(response, "audio.wav")
        threading.Thread(target=said_animation, args=(response,)).start()
        tts_voice.play(str(audio_path))
    else:
        print(f"\nFardo: Desculpe, algum erro ocorreu")
    
    is_listening = True

def main():
    global is_listening
    
    threading.Thread(target=blink_interval, daemon=True).start()
    threading.Thread(target=wave_animator, daemon=True).start()

    try:
        idle_animation()
    except subprocess.CalledProcessError:
        print(f"Erro: '{SESSION}' not found, verify your tmux session.")
        return

    stt.on_speech_callback = on_speech_captured
    
    stt_thread = threading.Thread(target=stt.start, daemon=True)
    stt_thread.start()

    is_listening = True
    
    print("\n" + "="*40)
    print(" FARDO VOICE INTERFACE - CLI CHAT")
    print(" Press [ENTER] to exit")
    print("="*40 + "\n")

    try:
        input()
        exit_global()
    except (EOFError, KeyboardInterrupt):
        exit_global()

if __name__ == "__main__":
    main()