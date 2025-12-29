import speech_recognition as sr
import sys
from difflib import SequenceMatcher

EXCLUDE_KEYWORDS = [
    "hdmi", "digital", "surround", "spdif", "iec958",
    "dmix", "upmix", "vdownmix", "speex", "a52",
    "samplerate", "lavrate", "default", "pulse", "pipewire"
]

class STT:
    def __init__(
        self,
        device_index: int,
        language: str = "pt-BR",
        wake_word: str | None = None,
        search_first_n: int = 0,
        on_speech_callback=None,
        similarity_threshold: float = 0.7
    ):
        self.device_index = device_index
        self.language = language
        self.wake_word = wake_word.lower() if wake_word else None
        self.search_first_n = search_first_n
        self.on_speech_callback = on_speech_callback
        self.similarity_threshold = similarity_threshold

        self.recognizer = sr.Recognizer()

    def _get_similarity(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def _select_best_transcription(self, response: dict):
        alternatives = [
            alt.get("transcript", "").lower()
            for alt in response.get("alternative", [])
            if alt.get("transcript")
        ]

        if not alternatives:
            return None, []

        if not self.wake_word:
            return alternatives[0], alternatives

        scored = []

        for idx, text in enumerate(alternatives):
            score = 0.0
            words = text.split()
            
            best_word_idx = -1
            max_sim = 0
            
            for i, word in enumerate(words):
                sim = self._get_similarity(word, self.wake_word)
                if sim > max_sim:
                    max_sim = sim
                    best_word_idx = i

            if max_sim >= self.similarity_threshold:
                score += (max_sim * 100)
                
                words[best_word_idx] = self.wake_word
                corrected_text = " ".join(words)
                
                if best_word_idx == 0:
                    score += 20
            else:
                corrected_text = text

            score -= len(text) * 0.1
            score -= idx * 0.5
            scored.append((score, corrected_text))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_text = scored[0]

        if best_score > 0:
            return best_text, alternatives

        return None, alternatives

    def start(self):
        print(f"Using microphone index {self.device_index}")
        if self.wake_word:
            print(f"Target wake word: '{self.wake_word}'")
        print("Press Ctrl+C to stop.\n")

        with sr.Microphone(device_index=self.device_index) as source:
            print("Calibrating ambient noise (2 seconds)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)

            while True:
                try:
                    print("Listening...")
                    audio = self.recognizer.listen(
                        source,
                        timeout=5,
                        phrase_time_limit=10
                    )

                    response = self.recognizer.recognize_google(
                        audio,
                        language=self.language,
                        show_all=True
                    )

                    if not response:
                        #print("Speech detected but not recognized.")
                        continue

                    selected, alternatives = self._select_best_transcription(response)

                    if selected:
                        #print(f"Selected transcription: {selected}")

                        if self.on_speech_callback:
                            self.on_speech_callback(
                                selected_text=selected,
                                alternatives=alternatives,
                                raw_response=response
                            )
                    else:
                        print("Wake word not found in speech.")

                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    print("Speech detected but not recognized.")
                except sr.RequestError as e:
                    print(f"API request error: {e}")
                except KeyboardInterrupt:
                    print("\nExiting...")
                    sys.exit(0)

# Example:
"""
def on_speech(selected_text, alternatives, raw_response):
    print("\n--- CALLBACK ---")
    print(f"Result: {selected_text}")
        
listener = STT(
    device_index=0,
    wake_word="fardo",
    #wake_word=None,
    similarity_threshold=0.7,
    on_speech_callback=on_speech
)

listener.start()
"""