import os
import sys
import time
import math
import threading
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.STT.STT import STT
from src.TTS_better.TTS_better import TTS_better
from src.chat_utils.Enums import Colors

class CLI_voice_better:
    def __init__(self, obj, device_index=0, wake_word=None, similarity_threshold=0.7, length_scale=1.3, noise_scale=0.2, noise_w=0.05):
        try:
            self.obj = obj
            self.stt = STT(device_index=device_index, wake_word=wake_word, similarity_threshold=similarity_threshold)
            self.tts = TTS_better(length_scale=length_scale, noise_scale=noise_scale, noise_w=noise_w)
            self.is_listening = False
            self.audio_lock = threading.Lock()
        except Exception as e:
            print("Erro ao inicializar CLI_voice_better:", e)
    
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
                print("Erro na wave_animator loop:", e)
                time.sleep(0.5)

    def play_audio_with_animation(self, audio_path: str, response_text: str):        
        with self.audio_lock:
            animation_thread = threading.Thread(
                target=self.obj.said_animation, 
                args=(response_text,),
                daemon=True
            )
            animation_thread.start()
            
            try:
                self.tts.play(audio_path.name if hasattr(audio_path, 'name') else audio_path)
            except Exception as e:
                print(f"\n{Colors.YELLOW}Erro ao reproduzir áudio:{Colors.RESET} {e}")
            finally:
                self.obj.is_talking = False
                animation_thread.join(timeout=1)

    def on_speech_captured(self, selected_text, alternatives, raw_response):

        if self.stt.wake_word is not None and self.stt.wake_word not in selected_text.lower():
            print(f"Wake word não detectado em: {selected_text}")
            return
        
        print(f"Comando capturado: {selected_text}")
        self.process_command(selected_text)

    def process_command(self, text: str):
        try:
            self.is_listening = False
            self.obj.api_llm.send_message(f"{text}")
            response = self.obj.api_llm.get_latest_answer()
            
            if response:
                print(f"{Colors.GREEN}Fardo:{Colors.RESET} {response}")
                
                try:
                    audio_path = self.tts.generate(response, "fardo_response.wav")
                    
                    playback_thread = threading.Thread(
                        target=self.play_audio_with_animation,
                        args=(audio_path, response),
                        daemon=True
                    )
                    playback_thread.start()
                    
                    playback_thread.join()
                    
                except Exception as e:
                    print(f"\n{Colors.YELLOW}Erro no TTS:{Colors.RESET} {e}")
                    
            else:
                print(f"\n{Colors.YELLOW}Fardo:{Colors.RESET} Desculpe, algum erro ocorreu")
                
        except Exception as e:
            print(f"\n{Colors.YELLOW}Erro ao processar:{Colors.RESET} {e}")
        
        finally:
            self.tts.cleanup_old_wavs(max_age_seconds=10, exclude="fardo_response.wav")
            self.is_listening = True
            self.obj.idle_animation()

    def main(self):        
        threading.Thread(target=self.obj.blink_interval, daemon=True).start()
        threading.Thread(target=self.wave_animator, daemon=True).start()

        try:
            self.obj.idle_animation()
        except subprocess.CalledProcessError:
            print(f"{Colors.YELLOW}Erro:{Colors.RESET} Sessão tmux '{self.obj.SESSION}' não encontrada.")
            print("Execute primeiro: tmux new -s mysession")
            return

        self.stt.on_speech_callback = self.on_speech_captured
        
        threading.Thread(target=self.stt.start, daemon=True).start()

        self.is_listening = True
        
        print("\n" + "="*50)
        print("  FARDO VOICE INTERFACE - CLI CHAT")
        print("  Diga 'Fardo' seguido do seu comando")
        print("  Pressione [ENTER] para sair")
        print("="*50 + "\n")

        try:
            input()
            self.obj.exit_global()
        except (EOFError, KeyboardInterrupt):
            self.obj.exit_global()