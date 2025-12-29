import shutil
import sys
import argparse

class FaceCLI:
    def __init__(self):
        self.eye_open, self.eye_closed = "█", "—"
        self.m_open, self.m_closed = "█", "▬"
        self.HIDE, self.SHOW, self.HOME, self.CLEAR = "\033[?25l", "\033[?25h", "\033[H", "\033[2J"

    def render(self, left="open", right="open", mouth="closed"):
        columns, lines = shutil.get_terminal_size()
        mouth_width = max(3, columns // 12) | 1
        eye_gap = max(2, columns // 5) | 1
        vertical_gap = max(1, lines // 5)

        l_char = self.eye_open if left == "open" else self.eye_closed
        r_char = self.eye_open if right == "open" else self.eye_closed
        m_char = self.m_open if mouth == "open" else self.m_closed

        eyes_row = f"{l_char}{' ' * eye_gap}{r_char}"
        mouth_row = m_char * mouth_width

        left_pad_eyes = max(0, (columns // 2) - (len(eyes_row) // 2))
        left_pad_mouth = max(0, (columns // 2) - (len(mouth_row) // 2))
        top_padding = max(0, (lines - (2 + vertical_gap)) // 2)

        sys.stdout.write(self.CLEAR + self.HOME + self.HIDE)
        sys.stdout.write("\n" * top_padding)
        sys.stdout.write(f"{' ' * left_pad_eyes}{eyes_row}\n")
        sys.stdout.write("\n" * vertical_gap)
        sys.stdout.write(f"{' ' * left_pad_mouth}{mouth_row}\n")
        sys.stdout.write(self.SHOW)
        sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", choices=["open", "closed"], default="open")
    parser.add_argument("--right", choices=["open", "closed"], default="open")
    parser.add_argument("--mouth", choices=["open", "closed"], default="closed")
    
    args = parser.parse_args()
    FaceCLI().render(left=args.left, right=args.right, mouth=args.mouth)

if __name__ == "__main__":
    main()