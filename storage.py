import os
import json
import shutil

SHEETS_FILE = "sheets_data.json"
DOCS_FILE = "docs_data.json"
SLIDES_FILE = "slides_data.json"
CODE_FILE = "code_data.json"
NOTEPAD_FILE = "notepad_data.txt"
MAP_FILE = "map_data.json"

def save_sheets(sheets):
    with open(SHEETS_FILE, 'w') as f:
        json.dump(sheets, f)

def load_sheets():
    if not os.path.exists(SHEETS_FILE):
        return []
    with open(SHEETS_FILE, 'r') as f:
        return json.load(f)

def save_sheet_cells(sheet_id, data):
    sheets = load_sheets()
    for sheet in sheets:
        if sheet['id'] == sheet_id:
            sheet['data'] = data
            break
    save_sheets(sheets)

def save_docs(docs):
    with open(DOCS_FILE, 'w') as f:
        json.dump(docs, f)

def load_docs():
    if not os.path.exists(DOCS_FILE):
        return []
    with open(DOCS_FILE, 'r') as f:
        return json.load(f)

def save_doc_content(doc_id, content):
    docs = load_docs()
    for doc in docs:
        if doc['id'] == doc_id:
            doc['content'] = content
            break
    save_docs(docs)

SLIDES_FILE = "slides_data.json"

def save_slides(slides):
    with open(SLIDES_FILE, 'w') as f:
        json.dump(slides, f)

def load_slides():
    if not os.path.exists(SLIDES_FILE):
        return []
    with open(SLIDES_FILE, 'r') as f:
        return json.load(f)

def save_slide_content(pres_id, content):
    slides = load_slides()
    for pres in slides:
        if pres['id'] == pres_id:
            pres['content'] = content
            break
    save_slides(slides)

def save_codes(codes):
    with open(CODE_FILE, 'w') as f:
        json.dump(codes, f)

def load_codes():
    if not os.path.exists(CODE_FILE):
        return []
    with open(CODE_FILE, 'r') as f:
        return json.load(f)

def save_code_content(code_id, content):
    codes = load_codes()
    for code in codes:
        if code['id'] == code_id:
            code['content'] = content
            break
    save_codes(codes)

def save_notepad(content):
    with open(NOTEPAD_FILE, 'w') as f:
        f.write(content)

def load_notepad():
    if not os.path.exists(NOTEPAD_FILE):
        return ''
    with open(NOTEPAD_FILE, 'r') as f:
        return f.read()

def save_map(data):
    with open(MAP_FILE, 'w') as f:
        json.dump(data, f)

def load_map():
    if not os.path.exists(MAP_FILE):
        return []
    with open(MAP_FILE, 'r') as f:
        return json.load(f)

def get_special_folder(name):
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
            r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
        folders = {
            'Desktop': winreg.QueryValueEx(key, 'Desktop')[0],
            'Documents': winreg.QueryValueEx(key, 'Personal')[0],
            'Downloads': os.path.join(os.path.expanduser('~'), 'Downloads'),
            'Pictures': winreg.QueryValueEx(key, 'My Pictures')[0],
            'Music': winreg.QueryValueEx(key, 'My Music')[0],
            'Videos': winreg.QueryValueEx(key, 'My Video')[0],
        }
        winreg.CloseKey(key)
        return folders.get(name, os.path.expanduser('~'))
    except Exception as e:
        print("Registry error:", e)
        return os.path.expanduser('~')
def get_files(path):
    try:
        items = []
        for name in os.listdir(path):
            try:
                full = os.path.join(path, name)
                items.append({
                    'name': name,
                    'path': full.replace('\\', '\\\\'),
                    'isDir': os.path.isdir(full)
                })
            except Exception:
                continue
        items.sort(key=lambda x: (not x['isDir'], x['name'].lower()))
        return {'path': path, 'files': items}
    except Exception as e:
        print("Error:", e)
        return {'path': path, 'files': [], 'error': str(e)}
    
STORE_FILE = "store_data.json"

def save_store(data):
    with open(STORE_FILE, 'w') as f:
        json.dump(data, f)

def load_store():
    if not os.path.exists(STORE_FILE):
        return []
    with open(STORE_FILE, 'r') as f:
        return json.load(f)
    
WATCHLIST_FILE = "watchlist_data.json"

def save_watchlist(data):
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(data, f)

def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return []
    with open(WATCHLIST_FILE, 'r') as f:
        return json.load(f)
    
GOALS_FILE = "goals_data.json"

def save_goals(data):
    with open(GOALS_FILE, 'w') as f:
        json.dump(data, f)

def load_goals():
    if not os.path.exists(GOALS_FILE):
        return []
    with open(GOALS_FILE, 'r') as f:
        return json.load(f)
    
COURSES_FILE = "courses_data.json"

def save_courses(data):
    with open(COURSES_FILE, 'w') as f:
        json.dump(data, f)

def load_courses():
    if not os.path.exists(COURSES_FILE):
        return []
    with open(COURSES_FILE, 'r') as f:
        return json.load(f)
