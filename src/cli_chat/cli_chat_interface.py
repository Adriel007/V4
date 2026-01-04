import os
import sys
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.chat_utils.chat_utils import Chat_Utils
from src.chat_utils.CLI_text import CLI_text
from src.chat_utils.chat_utils import Chat_Utils  
from src.chat_utils.CLI_voice import CLI_voice
from src.chat_utils.CLI_voice_better import CLI_voice_better

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, help="Mode of operation")
    args = parser.parse_args()
    mode = args.mode.lower()
    chat_utils = Chat_Utils()

    if mode == "text":
        cli_text = CLI_text(obj=chat_utils)
        cli_text.main()
    elif mode == "voice":
        cli_voice = CLI_voice(obj=chat_utils, device_index=0, wake_word=None, similarity_threshold=0.7)
        cli_voice.main()
    elif mode == "voice_better":
        cli_voice_better = CLI_voice_better(obj=chat_utils, device_index=0, wake_word=None, similarity_threshold=0.7, length_scale=1.3, noise_scale=0.2, noise_w=0.05)
        cli_voice_better.main()
    else:
        print(f"Modo desconhecido: {mode}. Escolha entre 'text', 'voice' ou 'voice_better'.")

if __name__ == "__main__":
    main()