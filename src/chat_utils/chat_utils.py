import subprocess
import sys
import time
import random
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.prompt import __PROMPTS__
from src.api_llm.api_llm import ApiLLM

class Chat_Utils:
    def __init__(self):
        try:
            self.api_llm = ApiLLM()
            self.last_response = 0
            self.SESSION = "mysession"
            self.INPUT_PANE = "0.1"
            self.OUTPUT_PANE = "0.0"
            self.ANIMATION_CLI = "python3 ./src/cli_animation/cli_animation.py"
            self.is_talking = False
        except Exception as e:
            print("Erro ao inicializar Chat_Utils")
            raise

    def focus_input_pane(self):
        try:
            subprocess.run(["tmux", "select-pane", "-t", f"{self.SESSION}:{self.INPUT_PANE}"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao focar pane de entrada: {e}")

    def send_to_output(self, cmd: str):
        try:
            subprocess.run(["tmux", "send-keys", "-t", f"{self.SESSION}:{self.OUTPUT_PANE}", cmd, "C-m"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao enviar comando para output: {cmd} - {e}")

    def exit_global(self):
        try:
            subprocess.run(["tmux", "kill-session", "-t", self.SESSION], stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Erro ao encerrar sessão tmux: {e}")
        finally:
            sys.exit(0)

    def blink_interval(self):
        try:
            while True:
                if not self.is_talking:
                    self.send_to_output(f"{self.ANIMATION_CLI} --left closed --right closed --mouth closed")
                    time.sleep(random.uniform(0.1, 0.2))
                    self.send_to_output(f"{self.ANIMATION_CLI} --left open --right open --mouth closed")
                time.sleep(random.uniform(4, 8))
        except Exception as e:
            print("Erro na thread blink_interval")

    def initiative_interval(self):
        try:
            while True:
                time.sleep(random.uniform(120, 300))  # 2~5 minutes
                if not self.is_talking and self.last_response >= time.time() - 300:  # only if no response in last 5 minutes
                    prompt = f"{__PROMPTS__['initiative']}"
                    self.api_llm.send_message(prompt)
                    response = self.api_llm.get_latest_answer()
                    if response:
                        print(f"\nFardo: {response}")
                        self.said_animation(response)
                        print("You: ", end='', flush=True)
        except Exception as e:
            print("Erro na thread initiative_interval")

    def said_animation(self, text: str):
        try:
            self.is_talking = True
            
            iterations = max(2, len(text) // 4) 
            
            for _ in range(iterations):
                self.send_to_output(f"{self.ANIMATION_CLI} --left open --right open --mouth open")
                time.sleep(0.15)
                self.send_to_output(f"{self.ANIMATION_CLI} --left open --right open --mouth closed")
                time.sleep(0.15)
                
            self.is_talking = False
            self.last_response = time.time()
            self.focus_input_pane()
        except Exception as e:
            print("Erro na animação said")
            self.is_talking = False

    def idle_animation(self):
        try:
            self.send_to_output(f"{self.ANIMATION_CLI} --left open --right open --mouth closed")
            self.focus_input_pane()
        except Exception as e:
            print("Erro ao iniciar animação idle")

    def send_message(self, message: str):
        try:
            prompt = f"{__PROMPTS__['user']} {message}"
            self.api_llm.send_message(prompt)
            response = self.api_llm.get_latest_answer()
            if response:
                print(f"Fardo: {response}")
                self.said_animation(response)
            else:
                print(f"Fardo: Desculpe, algum erro ocorreu")
        except Exception as e:
            print(f"Erro ao processar mensagem: {message}")
        