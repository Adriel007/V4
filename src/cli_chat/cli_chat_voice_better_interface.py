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
from src.TTS_better.TTS_better import TTS_better
from src.prompt import __PROMPTS__

api_llm = ApiLLM()
last_response = 0

stt = STT(
    device_index=0, 
    wake_word="fardo", 
    similarity_threshold=0.7,
    energy_threshold=300
)

tts_engine = TTS_better(
    length_scale=1.3,
    noise_scale=0.2,
    noise_w=0.05
)

SESSION = "mysession"
INPUT_PANE = "0.1"
OUTPUT_PANE = "0.0"
ANIMATION_CLI = "python3 ./src/cli_animation/cli_animation.py"

is_talking = False
is_listening = False
audio_lock = threading.Lock()

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
        if not is_talking:
            break
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

def play_audio_with_animation(audio_path: str, response_text: str):
    global is_talking
    
    with audio_lock:
        animation_thread = threading.Thread(
            target=said_animation, 
            args=(response_text,),
            daemon=True
        )
        animation_thread.start()
        
        try:
            tts_engine.play(audio_path.name if hasattr(audio_path, 'name') else audio_path)
        except Exception as e:
            print(f"\n{YELLOW}Erro ao reproduzir áudio:{RESET} {e}")
        finally:
            is_talking = False
            animation_thread.join(timeout=1)

def on_speech_captured(selected_text, alternatives, raw_response):
    if "fardo" not in selected_text.lower():
        return
    
    global is_listening
    is_listening = False
    
    print(f"\n{BLUE}Você:{RESET} {selected_text}")
    
    process_command(f"{__PROMPTS__['main']} {__PROMPTS__['user']} {selected_text}")
    
def process_command(text: str):
    try:
        api_llm.send_message(f"{text}")
        response = api_llm.get_latest_answer()
        
        if response:
            print(f"{GREEN}Fardo:{RESET} {response}")
            
            try:
                audio_path = tts_engine.generate(response, "fardo_response.wav")
                
                playback_thread = threading.Thread(
                    target=play_audio_with_animation,
                    args=(audio_path, response),
                    daemon=True
                )
                playback_thread.start()
                
                playback_thread.join()
                
            except Exception as e:
                print(f"\n{YELLOW}Erro no TTS:{RESET} {e}")
                
        else:
            print(f"\n{YELLOW}Fardo:{RESET} Desculpe, algum erro ocorreu")
            
    except Exception as e:
        print(f"\n{YELLOW}Erro ao processar:{RESET} {e}")
    
    finally:
        tts_engine.cleanup_old_wavs(max_age_seconds=10, exclude="fardo_response.wav")
        is_listening = True
        idle_animation()

def main():
    global is_listening
    
    threading.Thread(target=blink_interval, daemon=True).start()
    threading.Thread(target=wave_animator, daemon=True).start()

    try:
        idle_animation()
    except subprocess.CalledProcessError:
        print(f"{YELLOW}Erro:{RESET} Sessão tmux '{SESSION}' não encontrada.")
        print("Execute primeiro: tmux new -s mysession")
        return

    stt.on_speech_callback = on_speech_captured
    
    stt_thread = threading.Thread(target=stt.start, daemon=True)
    stt_thread.start()

    is_listening = True
    
    print("\n" + "="*50)
    print("  FARDO VOICE INTERFACE - CLI CHAT")
    print("  Diga 'Fardo' seguido do seu comando")
    print("  Pressione [ENTER] para sair")
    print("="*50 + "\n")

    try:
        input()
        exit_global()
    except (EOFError, KeyboardInterrupt):
        exit_global()

if __name__ == "__main__":
    main()