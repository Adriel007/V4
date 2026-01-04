import os
import sys
import time
import math
import threading
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.STT.STT import STT
from src.TTS.TTS import TTS
from src.chat_utils.Enums import Colors

class CLI_voice:
    def __init__(self, obj, device_index=0, wake_word=None, similarity_threshold=0.7):
        try:
            self.obj = obj
            self.stt = STT(device_index=device_index, wake_word=wake_word, similarity_threshold=similarity_threshold)
            self.tts = TTS(speed=125, pitch=36, gap=7, amplitude=105)
            self.is_listening = False
            print("CLI_voice inicializado com sucesso")
        except Exception as e:
            print("Erro ao inicializar CLI_voice")
    
    def wave_animator(self):
        t = 0
        BLOCKS = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        while True:
            try:
                if self.is_listening and not self.obj.is_talking:
                    wave = ""
                    for i in range(12):
                        amplitude = (math.sin(t + i * 0.5) + 1) / 2
                        idx = int(amplitude * (len(BLOCKS) - 1))
                        wave += BLOCKS[idx]

                    sys.stdout.write(f"{Colors.CLEAR_LINE}{Colors.BLUE}[LISTENING]{Colors.RESET} {wave}")

                elif self.obj.is_talking:
                    pulse_size = int((math.sin(t * 2) + 1) * 5) + 5
                    bar = "█" * pulse_size
                    sys.stdout.write(f"{Colors.CLEAR_LINE}{Colors.GREEN}[TALKING]{Colors.RESET} {bar}")

                else:
                    dots = "." * (int(t * 2) % 4)
                    sys.stdout.write(f"{Colors.CLEAR_LINE}{Colors.YELLOW}[PROCESSING]{Colors.RESET} {dots: <3}")

                sys.stdout.flush()
                t += 0.3
                time.sleep(0.05)
            except Exception as e:
                print("Erro na wave_animator loop")
                time.sleep(0.5)

    def on_speech_captured(self, selected_text, alternatives, raw_response):

        if self.stt.wake_word is not None and self.stt.wake_word not in selected_text.lower():
            print(f"Wake word não detectado em: {selected_text}")
            return
        
        print(f"Comando capturado: {selected_text}")
        self.process_command(selected_text)

    def process_command(self, text: str):
        try:
            self.is_listening = False
            print(f"Processando comando: {text}")

            self.obj.api_llm.send_message(text)
            response = self.obj.api_llm.get_latest_answer()
            
            if response:
                print(f"Resposta recebida: {response[:100]}...")
                try:
                    audio_path = self.tts.generate(response, "audio.wav")
                    threading.Thread(target=self.obj.said_animation, args=(response,)).start()
                    self.tts.play(str(audio_path))
                except Exception as e:
                    print(f"Erro ao sintetizar/reproduzir áudio: {e}")
                    print(f"\nFardo: Desculpe, ocorreu um erro no TTS")
            else:
                print("Nenhuma resposta recebida da API")
                print("Nenhuma resposta recebida da API ao processar comando")
                print(f"\nFardo: Desculpe, algum erro ocorreu")
            
            self.is_listening = True
        except Exception as e:
            print(f"Erro ao processar comando: {text}")
            print(f"Detalhe do erro: {e}")
            print(f"\nFardo: Desculpe, algum erro ocorreu")
            self.is_listening = True

    def main(self):        
        threading.Thread(target=self.obj.blink_interval, daemon=True).start()
        threading.Thread(target=self.wave_animator, daemon=True).start()

        try:
            self.obj.idle_animation()
            print("Animação idle iniciada")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao iniciar animação: {e}")
            return
        except Exception as e:
            print("Erro inesperado ao iniciar animação")
            return

        self.stt.on_speech_callback = self.on_speech_captured
        
        threading.Thread(target=self.stt.start, daemon=True).start()
        print("Thread STT iniciada")

        self.is_listening = True
        
        print("\n" + "="*40)
        print(" FARDO VOICE INTERFACE - CLI CHAT")
        print(" Press [ENTER] to exit")
        print("="*40 + "\n")

        try:
            input()
            self.obj.exit_global()
        except (EOFError, KeyboardInterrupt):
            print("CLI_voice encerrado pelo usuário")
            self.obj.exit_global()