import threading
import subprocess

class CLI_text:
    def __init__(self, obj):
        self.obj = obj

    def main(self):
        threading.Thread(target=self.obj.blink_interval, daemon=True).start()
        threading.Thread(target=self.obj.initiative_interval, daemon=True).start()

        try:
            self.obj.idle_animation()
        except subprocess.CalledProcessError:
            print(f"Erro: '{self.obj.SESSION}' not found.")
            return

        while True:
            try:
                cmd = input("You: ").strip()
                if cmd.lower() in ("exit", "quit"):
                    self.obj.exit_global()
                if cmd:
                    try:
                        self.obj.send_message(cmd)
                    except Exception as e:
                        print(f"[ERROR] {str(e)}")
            except (EOFError, KeyboardInterrupt):
                self.obj.exit_global()