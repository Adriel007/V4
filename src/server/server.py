from flask import Flask, request, jsonify, Response
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
import threading
from time import sleep
import logging
import json
import shutil
import os
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

load_dotenv("../../.env")

VERBOSE = bool(os.getenv('VERBOSE'))

def typing(driver, by, selector, text, index=0):
    log(f'Looking for element with selector: {selector} at index {index}')
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            elems = driver.find_elements(by, selector)
            log(f'Found {len(elems)} elements for selector {selector} (attempt {attempt+1})')
            
            if len(elems) > index:
                elem = elems[index]
                log(f'Clearing and typing on element at index {index}')
                elem.clear()
                elem.click()
                elem.send_keys(text)
                sleep(0.2)
                log(f'Successfully typed text on element')
                return
            
            if attempt < max_attempts - 1:
                log(f'Element not found at index {index}, retrying in 0.5s...')
                sleep(0.5)
        except Exception as e:
            log(f'Error on attempt {attempt+1}: {str(e)}')
            if attempt < max_attempts - 1:
                sleep(0.5)
    
    raise Exception(f"Elemento de índice {index} não encontrado para o seletor {selector} após {max_attempts} tentativas")

app = Flask(__name__)

browser = {
    'driver': None,
    'lock': threading.Lock(),
    'ready': False
}

__DEEPSEEK__ = {
    "new_chat": "//span[text()='New chat']",
    "send": "_7436101 ds-icon-button ds-icon-button--l ds-icon-button--sizing-container",
    "input": "_27c9245 ds-scroll-area d96f2d2a",
    "chat": "dad65929", # STACK 0-> USER, 1-> BOT, 2 -> USER, ...
    "search_trash": ["d162f7b9", "_669a677"],
    "answer": "dad65929",
    "login_input": "ds-input__input",
    "login_button": "ds-atom-button ds-basic-button ds-basic-button--primary",

    "$class_name": lambda class_name: f"document.getElementsByClassName('{class_name}')",
    "$class_1": lambda class_name: f"document.getElementsByClassName('{class_name}')[0]",
}

def log(msg):
    if VERBOSE:
        logging.info(msg)

def get_driver():
    if browser['driver'] is not None:
        return browser['driver']
    options = FirefoxOptions()
    options.add_argument('--headless')
    geckodriver_path = shutil.which('geckodriver')
    if not geckodriver_path:
        raise RuntimeError('geckodriver not found in PATH')
    service = FirefoxService(executable_path=geckodriver_path)
    driver = webdriver.Firefox(service=service, options=options)
    browser['driver'] = driver
    browser['ready'] = True
    log('Browser driver initialized')
    return driver

@app.route('/open', methods=['POST'])
def open_url():
    data = request.get_json() or {}
    url = data.get('url')
    log(f'Request to open URL: {url}')
    if not url:
        log('Error: Missing url')
        return jsonify({'success': False, 'error': 'Missing url'}), 400
    driver = get_driver()
    with browser['lock']:
        log(f'Navigating to: {url}')
        driver.get(url)
    log(f'Successfully opened URL: {url}')
    return jsonify({'success': True, 'message': f'Opened {url}'})

@app.route('/js', methods=['POST'])
def run_js():
    data = request.get_json() or {}
    script = data.get('script')
    log(f'Request to execute JS script')
    if not script:
        log('Error: Missing script')
        return jsonify({'success': False, 'error': 'Missing script'}), 400
    driver = get_driver()
    with browser['lock']:
        try:
            log(f'Executing JavaScript')
            result = driver.execute_script(script)
            log(f'JavaScript executed successfully, result: {result}')
            return jsonify({'success': True, 'result': result})
        except Exception as e:
            log(f'Error executing JavaScript: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})

@app.route('/js/console', methods=['POST'])
def run_js_console():
    data = request.get_json() or {}
    expr = data.get('expr')
    log(f'Request to execute JS console expression')
    if not expr:
        log('Error: Missing expr')
        return jsonify({'success': False, 'error': 'Missing expr'}), 400
    driver = get_driver()
    with browser['lock']:
        try:
            log(f'Executing console expression')
            result = driver.execute_script(f'return eval("{expr}")')
            log(f'Console expression executed successfully: {expr}, result: {result}')
            return jsonify({'success': True, 'result': result})
        except Exception as e:
            log(f'Error executing console expression: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})

@app.route('/close', methods=['POST'])
def close_browser():
    log('Request to close browser')
    if browser['driver']:
        with browser['lock']:
            log('Closing browser driver')
            browser['driver'].quit()
            browser['driver'] = None
            browser['ready'] = False
        log('Browser successfully closed')
        return jsonify({'success': True, 'message': 'Browser closed'})
    log('Error: No browser running')
    return jsonify({'success': False, 'error': 'No browser running'})

@app.route('/status', methods=['GET'])
def status():
    log(f'Status requested - ready: {browser["ready"]}, has_driver: {browser["driver"] is not None}')
    return jsonify({
        'ready': browser['ready'],
        'has_driver': browser['driver'] is not None
    })


@app.route('/deepseek/open', methods=['PATCH'])
def deepseek_open():
    data = request.get_json() or {}
    url = data.get('url', 'https://chat.deepseek.com/')
    log(f'Request to open DeepSeek at {url}')
    driver = get_driver()
    with browser['lock']:
        log(f'Navigating to DeepSeek: {url}')
        driver.get(url)
        log('Waiting 2 seconds for page to load')
        sleep(2)
    log(f'Successfully opened DeepSeek at {url}')
    return jsonify({'success': True, 'message': f'Opened DeepSeek at {url}'})

@app.route('/deepseek/login', methods=['PATCH'])
def deepseek_login():
    log('Request to login to DeepSeek')
    email = {}.get('email', os.getenv('DEEPSEEK_EMAIL'))
    password = {}.get('password', os.getenv('DEEPSEEK_PASSWORD'))
    log(f'Email configured: {bool(email)}, Password configured: {bool(password)}')

    if not email or not password:
        log('Error: Missing email or password')
        return jsonify({'success': False, 'error': 'Missing email or password'}), 400
    driver = get_driver()
    with browser['lock']:
        try:
            log('Typing email')
            typing(driver, By.CLASS_NAME, __DEEPSEEK__["login_input"], email, index=0)
            log('Typing password')
            typing(driver, By.CLASS_NAME, __DEEPSEEK__["login_input"], password, index=1)
            log('Clicking login button')
            btn = driver.find_element(By.CLASS_NAME, __DEEPSEEK__["login_button"].split()[0])
            btn.click()
            log('Waiting 2 seconds for login to process')
            sleep(2)
            log('Login attempted successfully')
            return jsonify({'success': True, 'message': 'Login attempted'})
        except Exception as e:
            log(f'Error during login: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})

@app.route('/deepseek/new_chat', methods=['POST'])
def deepseek_new_chat():
    log('Request to start new chat')
    driver = get_driver()
    with browser['lock']:
        try:
            log('Searching for span with text "New chat"')
            new_chat_span = driver.find_element(By.XPATH, __DEEPSEEK__["new_chat"])
            log('Found "New chat" span element')
            
            log('Finding clickable parent element')
            clickable_element = new_chat_span.find_element(By.XPATH, "./ancestor::button | ./ancestor::div[@role='button'] | ./ancestor::*[contains(@class, 'button')]")
            
            log('Clicking new chat button')
            clickable_element.click()
            log('New chat button clicked successfully')
            log('Waiting 1 second for new chat to load')
            sleep(1)
            log('New chat started successfully')
            return jsonify({'success': True, 'message': 'New chat started'})
        except Exception as e:
            log(f'Error starting new chat: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})
        
@app.route('/deepseek/send_message', methods=['POST'])
def deepseek_send_message():
    data = request.get_json() or {}
    message = data.get('message')
    log(f'Request to send message: {message}')
    if not message:
        log('Error: Missing message')
        return jsonify({'success': False, 'error': 'Missing message'}), 400
    driver = get_driver()
    with browser['lock']:
        try:
            input_selector = '.' + __DEEPSEEK__["input"].replace(' ', '.')
            log(f'Typing message in input field')
            typing(driver, By.CSS_SELECTOR, input_selector, message, index=0)
            sleep(0.5)
            
            send_selector = '.' + __DEEPSEEK__["send"].replace(' ', '.')
            log('Finding and clicking send button')
            btn = driver.find_elements(By.CSS_SELECTOR, send_selector)[0]
            btn.click()
            log(f'Message sent successfully: {message}')

            max_wait = 60
            waited = 0
            button_disabled_false = False
            log('Starting to monitor aria-disabled attribute...')
            
            while waited < max_wait:
                sleep(0.5)
                waited += 0.5
                
                try:
                    btn_elements = driver.find_elements(By.CSS_SELECTOR, send_selector)
                    if btn_elements:
                        btn = btn_elements[0]
                        aria_disabled = btn.get_attribute('aria-disabled')
                        log(f'Button aria-disabled: {aria_disabled}')
                        
                        if aria_disabled == 'false':
                            button_disabled_false = True
                            log(f'Button disabled (aria-disabled=false) at {waited}s - generating response')
                        
                        elif button_disabled_false and aria_disabled == 'true':
                            log(f'Button enabled (aria-disabled=true) at {waited}s - response complete')
                            log('Bot answer received and chat is ready.')
                            return jsonify({'success': True, 'message': 'Message sent and answer received'})
                except Exception as e:
                    log(f'Error checking aria-disabled: {str(e)}')
                    continue
            
            log(f'Timeout after {max_wait}s')
            if button_disabled_false:
                log('Error: Response generation did not complete (timeout)')
                return jsonify({'success': False, 'error': 'Timeout waiting for response completion'})
            else:
                log('Error: Response generation never started')
                return jsonify({'success': False, 'error': 'Failed to send message or generation never started'})
        except Exception as e:
            log(f'Error sending message: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})

@app.route('/deepseek/send_message_stream', methods=['POST'])
def deepseek_send_message_stream():
    """
    Envia uma mensagem e faz streaming da resposta em tempo real.
    Retorna um stream de texto com chunks de SSE.
    """
    data = request.get_json() or {}
    message = data.get('message')
    log(f'Request to send message with streaming: {message}')
    if not message:
        log('Error: Missing message')
        return jsonify({'success': False, 'error': 'Missing message'}), 400
    
    def generate():
        driver = get_driver()
        try:
            with browser['lock']:
                input_selector = '.' + __DEEPSEEK__["input"].replace(' ', '.')
                log(f'Typing message in input field')
                typing(driver, By.CSS_SELECTOR, input_selector, message, index=0)
                sleep(0.5)
                
                send_selector = '.' + __DEEPSEEK__["send"].replace(' ', '.')
                log('Finding and clicking send button')
                btn = driver.find_elements(By.CSS_SELECTOR, send_selector)[0]
                btn.click()
                log(f'Message sent: {message}')
                
                max_wait = 10
                waited = 0
                button_disabled_false = False
                while waited < max_wait and not button_disabled_false:
                    sleep(0.5)
                    waited += 0.5
                    btn_elements = driver.find_elements(By.CSS_SELECTOR, send_selector)
                    if btn_elements:
                        aria_disabled = btn_elements[0].get_attribute('aria-disabled')
                        if aria_disabled == 'false':
                            button_disabled_false = True
                            log('Response generation started')
                            yield f"data: {json.dumps({'status': 'generating'})}\n\n"
            
            max_wait = 120
            waited = 0
            last_text = ""
            response_started = False
            no_change_count = 0
            max_no_change = 20
            
            while waited < max_wait:
                sleep(0.2)
                waited += 0.2
                
                try:
                    with browser['lock']:
                        script = f"""
                        var parent = {__DEEPSEEK__["$class_1"](__DEEPSEEK__["answer"])};
                        if (!parent || !parent.children) return {{"text": "", "index": -1}};
                        var children = Array.from(parent.children);
                        if (children.length === 0) return {{"text": "", "index": -1}};
                        
                        // Mensagens de bot estão nos índices ímpares (1, 3, 5...)
                        var lastBotIndex = -1;
                        var lastBotText = "";
                        
                        for (var i = children.length - 1; i >= 0; i--) {{
                            if (i % 2 === 1) {{  // Índice ímpar = mensagem do bot
                                var text = (children[i].innerText || "").trim();
                                if (text.length > 0) {{
                                    lastBotText = text;
                                    lastBotIndex = i;
                                    break;
                                }}
                            }}
                        }}
                        
                        return {{"text": lastBotText, "index": lastBotIndex}};
                        """
                        result = driver.execute_script(script)
                        current_text = result.get('text', '').strip()
                        
                        btn_elements = driver.find_elements(By.CSS_SELECTOR, send_selector)
                        btn_enabled = False
                        if btn_elements:
                            aria_disabled = btn_elements[0].get_attribute('aria-disabled')
                            btn_enabled = (aria_disabled == 'true')
                        
                        if current_text != last_text:
                            if len(current_text) > len(last_text):
                                new_chunk = current_text[len(last_text):]
                                yield f"data: {json.dumps({'text': new_chunk})}\n\n"
                                response_started = True
                                no_change_count = 0
                                log(f'Sent chunk: {len(new_chunk)} chars, total: {len(current_text)}')
                            last_text = current_text
                        else:
                            if response_started:
                                no_change_count += 1
                        
                        if btn_enabled and response_started and no_change_count > max_no_change:
                            log(f'Generation completed - button enabled and no changes for {no_change_count * 0.2}s')
                            yield f"data: {json.dumps({'status': 'completed'})}\n\n"
                            log('Response streaming completed')
                            return
                            
                except Exception as e:
                    log(f'Error during streaming: {str(e)}')
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    return
            
            # Timeout
            yield f"data: {json.dumps({'status': 'timeout'})}\n\n"
            log('Streaming timeout')
        except Exception as e:
            log(f'Error in stream generator: {str(e)}')
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')
        
@app.route('/deepseek/get_latest_answer', methods=['GET'])
def deepseek_get_latest_answer():
    log('Request to get latest answer')
    driver = get_driver()
    with browser['lock']:
        try:
            script = f"""
            var parent = {__DEEPSEEK__["$class_1"](__DEEPSEEK__["answer"])};
            var trash = [{__DEEPSEEK__["$class_name"](__DEEPSEEK__["search_trash"][0])},
                {__DEEPSEEK__["$class_name"](__DEEPSEEK__["search_trash"][1])}];
            if (!parent) return [];
            while (trash[0].length > 0)
                trash[0][0].remove();
            while (trash[1].length > 0)
                trash[1][0].remove();
            parent.querySelectorAll('a').forEach(a => a.textContent = "");
            var children = Array.from(parent.children);
            return children.map(e => e.innerText);
            """
            log('Executing script to retrieve chat messages')
            messages = driver.execute_script(script)
            log(f'Retrieved {len(messages)} total messages')
            bot_msgs = [msg for i, msg in enumerate(messages) if i % 2 == 1]
            log(f'Found {len(bot_msgs)} bot messages')
            answer = bot_msgs[-1] if bot_msgs else None
            log(f'Latest answer retrieved: {answer[:100] if answer else None}...' if answer and len(answer) > 100 else f'Latest answer: {answer}')
            return jsonify({'success': True, 'answer': answer})
        except Exception as e:
            log(f'Error getting latest answer: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})
        
@app.route('/deepseek/get_all_answers', methods=['GET'])
def deepseek_get_all_answers():
    log('Request to get all answers')
    driver = get_driver()
    with browser['lock']:
        try:
            script = f"""
            var parent = {__DEEPSEEK__["$class_1"](__DEEPSEEK__["answer"])};
            var trash = [{__DEEPSEEK__["$class_name"](__DEEPSEEK__["search_trash"][0])},
                {__DEEPSEEK__["$class_name"](__DEEPSEEK__["search_trash"][1])}];
            if (!parent) return [];
            while (trash[0].length > 0)
                trash[0][0].remove();
            while (trash[1].length > 0)
                trash[1][0].remove();
            parent.querySelectorAll('a').forEach(a => a.textContent = "");
            var children = Array.from(parent.children);
            return children.map(e => e.innerText);
            """
            log('Executing script to retrieve all chat messages')
            messages = driver.execute_script(script)
            log(f'Retrieved {len(messages)} total messages')
            bot_msgs = [msg for i, msg in enumerate(messages) if i % 2 == 1]
            log(f'Found {len(bot_msgs)} bot messages')
            log(f'All bot answers retrieved successfully')
            return jsonify({'success': True, 'answers': bot_msgs})
        except Exception as e:
            log(f'Error getting all answers: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})
        
@app.route('/deepseek/get_history', methods=['GET'])
def deepseek_get_history():
    log('Request to get chat history')
    driver = get_driver()
    with browser['lock']:
        try:
            results = []
            script = f"""
            var parent = {__DEEPSEEK__["$class_1"](__DEEPSEEK__["chat"])};
            if (!parent) return [];
            var children = Array.from(parent.children);
            return children.map(e => e.innerText);
            """
            log('Executing script to retrieve chat history')
            messages = driver.execute_script(script)
            log(f'Retrieved {len(messages)} total messages in chat history')
            for i, msg in enumerate(messages):
                role = 'user' if i % 2 == 0 else 'bot'
                results.append({'role': role, 'message': msg})
            log('Chat history retrieved successfully')
            return jsonify({'success': True, 'history': results})
        except Exception as e:
            log(f'Error getting chat history: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})

@app.route('/deepseek/list_chats', methods=['GET'])
def deepseek_list_chats():
    log('Request to list all chats')
    driver = get_driver()
    with browser['lock']:
        try:
            script = """
            return [...document.querySelectorAll("a")].filter(a => a.href.includes("/a/chat/s/")).map(a => ({title: a.textContent.trim(), url: a.href}))
            """
            log('Executing script to retrieve all chats')
            chats = driver.execute_script(script)
            if chats is None:
                chats = []
            log(f'Retrieved {len(chats)} chats')
            return jsonify({'success': True, 'chats': chats, 'count': len(chats)})
        except Exception as e:
            log(f'Error listing chats: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})

@app.route('/deepseek/chat/open/<int:chat_index>', methods=['PATCH'])
def deepseek_open_chat(chat_index):
    log (f'Request to open chat at index {chat_index}')
    driver = get_driver()
    with browser['lock']:
        try:
            log(f'Finding chat link at index {chat_index}')
            script = f"""
            var chats = [...document.querySelectorAll("a")].filter(a => a.href.includes("/a/chat/s/"));
            if (chats.length > {chat_index}) {{
                chats[{chat_index}].click();
                return true;
            }} else {{
                return false;
            }}
            """
            found = driver.execute_script(script)
            if not found:
                log(f'Error: Chat index {chat_index} out of range')
                return jsonify({'success': False, 'error': 'Chat index out of range'}), 400
            log(f'Chat at index {chat_index} opened successfully')
            sleep(1)
            return jsonify({'success': True, 'message': f'Chat at index {chat_index} opened'})
        except Exception as e:
            log(f'Error opening chat: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})

@app.route('/deepseek/chat/delete_all', methods=['DELETE'])
def deepseek_delete_all_chats():
    log('Request to delete all chats')
    data = request.get_json(force=True, silent=True) or {}
    driver = get_driver()
    
    with browser['lock']:
        try:
            length = driver.execute_script(f"""
                return document.getElementsByClassName("_2090548 ds-icon-button ds-icon-button--m ds-icon-button--sizing-container").length
            """)
            log(f'Found {length} chats to delete')

            for i in range((length - 1), -1, -1):
                try:
                    log(f'Deleting chat at index {i}')
                    driver.execute_script(f"""
                        document.getElementsByClassName("_2090548 ds-icon-button ds-icon-button--m ds-icon-button--sizing-container")[{i}].click()
                    """)
                    sleep(0.2)
                    driver.execute_script("""
                        document.getElementsByClassName("ds-dropdown-menu ds-elevated")[0].children[3].click()
                    """)
                    sleep(0.5)
                    
                    delete_btn = driver.execute_script("""
                        return [...document.querySelectorAll("button")].filter(btn => btn.textContent.trim() === "Delete")
                    """)
                    if delete_btn:
                        driver.execute_script("""
                            [...document.querySelectorAll("button")].filter(btn => btn.textContent.trim() === "Delete")[0].click()
                        """)
                        log(f'Chat at index {i} deleted successfully')
                    else:
                        log(f'Delete button not found for chat at index {i}')
                    sleep(0.5)
                except Exception as e:
                    log(f'Error deleting chat at index {i}: {str(e)}')
                    continue
            
            log('All chats deleted successfully')
            return jsonify({'success': True, 'message': 'All chats deleted successfully'})
        except Exception as e:
            log(f'Error during delete all chats: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})

@app.route('/deepseek/chat/<int:chat_index>/<action>', methods=['PATCH'])
def deepseek_chat_action(chat_index, action):
    log(f'Request to perform action "{action}" on chat index {chat_index}')
    data = request.get_json(force=True, silent=True) or {}
    driver = get_driver()
    driver.execute_script(f"""
        document.getElementsByClassName("_2090548 ds-icon-button ds-icon-button--m ds-icon-button--sizing-container")[{chat_index}].click()
    """)
    with browser['lock']:
        try:
            if action == 'delete':
                log('Clicking delete option')
                driver.execute_script("""
                document.getElementsByClassName("ds-dropdown-menu ds-elevated")[0].children[3].click()
                """)
                sleep(0.5)
                log('Confirming delete')
                driver.execute_script("""
                [...document.querySelectorAll("button")].filter(btn => btn.textContent === "Delete")[0].click()
                """)
                sleep(1)
                log('Chat deleted successfully')
                return jsonify({'success': True, 'message': 'Chat deleted successfully'})
            
            elif action == 'rename':
                new_name = data.get('name')
                if not new_name:
                    log('Error: Missing name for rename action')
                    return jsonify({'success': False, 'error': 'Missing name parameter'}), 400
                log('Clicking rename option')
                driver.execute_script("""
                document.getElementsByClassName("ds-dropdown-menu ds-elevated")[0].children[0].click()
                """)
                sleep(0.5)
                log(f'Typing new name: {new_name}')
                typing(driver, By.CSS_SELECTOR, "input[type='text']", new_name, index=0)
                sleep(0.3)
                input_elem = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")[0]
                input_elem.send_keys(Keys.ENTER)
                sleep(1)
                log('Chat renamed successfully')
                return jsonify({'success': True, 'message': f'Chat renamed to: {new_name}'})
            
            elif action == 'pin':
                log('Opening chat menu for pin')
                log('Clicking pin option')
                driver.execute_script("""
                document.getElementsByClassName("ds-dropdown-menu ds-elevated")[0].children[1].click()
                """)
                sleep(1)
                log('Chat pinned successfully')
                return jsonify({'success': True, 'message': 'Chat pinned successfully'})
            
            elif action == 'unpin':
                log('Opening chat menu for unpin')
                log('Clicking unpin option')
                driver.execute_script("""
                document.getElementsByClassName("ds-dropdown-menu ds-elevated")[0].children[1].click()
                """)
                sleep(1)
                log('Chat unpinned successfully')
                return jsonify({'success': True, 'message': 'Chat unpinned successfully'})
            
            else:
                log(f'Error: Unknown action "{action}"')
                return jsonify({'success': False, 'error': f'Unknown action: {action}'}), 400
        
        except Exception as e:
            log(f'Error performing action: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})

@app.route('/deepseek/chat_options/<option>', methods=['PATCH'])
def deepseek_chat_options(option):
    log(f'Request to toggle chat option: {option}')
    driver = get_driver()
    with browser['lock']:
        try:
            if option == 'deepthink':
                log('Toggling deep think mode')
                driver.execute_script("""
                document.getElementsByClassName("ec4f5d61")[0].children[0].click()
                """)
                sleep(0.5)
                result = driver.execute_script("""
                return JSON.parse(localStorage.getItem("thinkingEnabled")).value
                """)
                log(f'Deep think mode is now: {result}')
                return jsonify({'success': True, 'option': 'deepthink', 'enabled': result})
            
            elif option == 'search':
                log('Toggling search mode')
                driver.execute_script("""
                document.getElementsByClassName("ec4f5d61")[0].children[1].click()
                """)
                sleep(0.5)
                result = driver.execute_script("""
                return JSON.parse(localStorage.getItem("searchEnabled")).value
                """)
                log(f'Search mode is now: {result}')
                return jsonify({'success': True, 'option': 'search', 'enabled': result})
            
            else:
                log(f'Error: Unknown option "{option}"')
                return jsonify({'success': False, 'error': f'Unknown option: {option}'}), 400
        
        except Exception as e:
            log(f'Error toggling chat option: {str(e)}')
            return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    log('Starting DeepSeek Server...')
    log(f'VERBOSE mode: {VERBOSE}')
    app.run(host='0.0.0.0', port=5001, debug=True)
