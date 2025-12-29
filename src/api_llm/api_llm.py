import requests
import time
import json

class ApiLLM:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url

    def open_deepseek(self):
        resp = requests.patch(f'{self.base_url}/deepseek/open', json={})
        print('Open DeepSeek:', resp.json())
        return resp.json()

    def login_deepseek(self):
        resp = requests.patch(f'{self.base_url}/deepseek/login')
        print('Login:', resp.json())
        return resp.json()
    
    def delete_all_chats(self):
        resp = requests.delete(f'{self.base_url}/deepseek/chat/delete_all')
        print('Delete All Chats:', resp.json())
        return resp.json()
    
    def new_chat(self):
        resp = requests.post(f'{self.base_url}/deepseek/new_chat', json={})
        print('New Chat:', resp.json())
        return resp.json()

    def send_message(self, message):
        resp = requests.post(f'{self.base_url}/deepseek/send_message', json={'message': message})
        return resp.json()

    def send_message_stream(self, message):
        try:            
            resp = requests.post(
                f'{self.base_url}/deepseek/send_message_stream', 
                json={'message': message}, 
                stream=True,
                timeout=120
            )
            
            full_text = ''
            error_occurred = False
            chunks_received = 0
            
            for line in resp.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            
                            if 'error' in data:
                                print(f"\n[ERROR] {data['error']}", flush=True)
                                error_occurred = True
                                break
                            
                            if 'text' in data:
                                text_chunk = data['text']
                                full_text += text_chunk
                                chunks_received += 1
                            
                            if 'status' in data:
                                if data['status'] == 'completed':
                                    break
                                elif data['status'] == 'timeout':
                                    break
                                elif data['status'] == 'generating':
                                    pass 
                        except json.JSONDecodeError as e:
                            print(f"\n[JSON Error] {e}")
                            error_occurred = True
                            break
            
            if not error_occurred:
                time.sleep(0.3)
            
            return full_text
        
        except requests.exceptions.Timeout:
            print("\n[ERROR] Request timeout")
            return ""
        except requests.exceptions.ConnectionError:
            print("\n[ERROR] Connection failed - the server is running?")
            return ""
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            return ""

    def get_latest_answer(self):
        resp = requests.get(f'{self.base_url}/deepseek/get_latest_answer')
        data = resp.json()
        answer = data.get('answer', '')
        return answer