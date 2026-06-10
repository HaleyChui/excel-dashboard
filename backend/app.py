from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os
import uuid

# Load env from ~/.hermes/.env
if not os.environ.get('OPENROUTER_API_KEY'):
    _env_path = os.path.expanduser('~/.hermes/.env')
    if os.path.exists(_env_path):
        with open(_env_path) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _v = _line.split('=', 1)
                    _v = _v.strip().strip('"').strip("'")
                    if _v and not _v.startswith('***') and not os.environ.get(_k.strip()):
                        os.environ[_k.strip()] = _v

from models import init_db, save_version, get_versions, get_version_html, save_template, list_templates, get_template, _get_conn

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ──────────────────────────── Session Store ────────────────────────────
sessions = {}  # uuid -> {files: [...], sheets: [...], config: {...}}

def _get_session(sid):
    return sessions.get(sid)

# ──────────────────────────── Routes ────────────────────────────

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/config/<path:_>')
def config_view(_):
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/dashboard/<path:_>')
def dashboard_view_route(_):
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/templates')
def templates_view():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """接收多個 Excel 檔案，回傳每個檔案的 Sheet 清單 + 欄位預覽"""
    session_id = request.form.get('session_id') or str(uuid.uuid4())
    if not _get_session(session_id):
        sessions[session_id] = {'files': [], 'sheets': {}, 'suggestions': []}

    files = request.files.getlist('files')
    from parser import parse_excel
    results = []
    for f in files:
        path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{f.filename}")
        f.save(path)
        info = parse_excel(path)
        info['path'] = path
        info['filename'] = f.filename
        sess = _get_session(session_id)
        sess['files'].append(info)
        sess['sheets'][f.filename] = info
        sessions[session_id] = sess
        results.append({
            'filename': f.filename,
            'sheets': [{k: v for k, v in s.items() if k != 'data'}
                       for s in info['sheets']]
        })

    return jsonify({'session_id': session_id, 'files': results})


@app.route('/api/sheets', methods=['POST'])
def get_sheet_preview():
    """回傳指定檔案/Sheet 的前 N 列資料"""
    data = request.get_json()
    session_id = data['session_id']
    filename = data['filename']
    sheet_name = data['sheet_name']
    file_info = sessions.get(session_id, {}).get('sheets', {}).get(filename)
    if not file_info:
        return jsonify({'error': 'file not found'}), 404
    for s in file_info['sheets']:
        if s['name'] == sheet_name:
            return jsonify({'columns': s['columns'], 'rows': s['rows'], 'preview': s.get('data', [])[:20]})
    return jsonify({'error': 'sheet not found'}), 404


@app.route('/api/parse_csv', methods=['POST'])
def parse_csv_endpoint():
    """解析 CSV 文字輸入，回傳欄位與預覽資料"""
    data = request.get_json()
    csv_text = data.get('csv_text', '')
    delimiter = data.get('delimiter', ',')
    
    if not csv_text.strip():
        return jsonify({'error': 'CSV 內容不可為空'}), 400
    
    from parser import parse_csv_text
    result = parse_csv_text(csv_text, delimiter)
    
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    
    # Return the first sheet info
    sheet = result['sheets'][0]
    return jsonify({
        'columns': sheet['columns'],
        'rows': sheet['rows'],
        'dtypes': sheet['dtypes'],
        'stats': sheet['stats'],
        'preview': sheet['data_json_compatible'][:20],
        'full_data': sheet['data_json_compatible']
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """AI 分析已勾選的 Sheet，建議圖表配對"""
    data = request.get_json()
    session_id = data['session_id']
    selections = data['selections']  # [{filename, sheetName, columns}]

    selected_sheets = []
    for sel in selections:
        file_info = sessions.get(session_id, {}).get('sheets', {}).get(sel['filename'])
        if file_info:
            for s in file_info['sheets']:
                if s['name'] == sel['sheetName']:
                    selected_sheets.append({
                        'file': sel['filename'],
                        'sheet': sel['sheetName'],
                        'columns': s['columns'],
                        'dtypes': s['dtypes'],
                        'stats': s.get('stats', {}),
                        'preview': s.get('data_json_compatible', s.get('data', []))[:5]
                    })

    from llm_agent import suggest_charts
    suggestions = suggest_charts(selected_sheets)
    sessions[session_id]['suggestions'] = suggestions
    return jsonify({'suggestions': suggestions})


@app.route('/api/session/<session_id>/files', methods=['GET'])
def get_session_files(session_id):
    """取得 session 的檔案列表"""
    sess = sessions.get(session_id)
    if not sess:
        return jsonify({'error': 'session not found'}), 404
    return jsonify({'files': sess.get('files', [])})


@app.route('/api/session/<session_id>/suggestions', methods=['GET'])
def get_session_suggestions(session_id):
    """取得 session 的圖表建議"""
    sess = sessions.get(session_id)
    if not sess:
        return jsonify({'error': 'session not found'}), 404
    return jsonify({'suggestions': sess.get('suggestions', [])})


@app.route('/api/session/<session_id>/selected-sheets', methods=['GET'])
def get_session_selected_sheets(session_id):
    """取得 session 的已勾選工作表"""
    sess = sessions.get(session_id)
    if not sess:
        return jsonify({'error': 'session not found'}), 404
    return jsonify({'selectedSheets': sess.get('selectedSheets', [])})


@app.route('/api/session/<session_id>/refinements', methods=['GET'])
def get_session_refinements(session_id):
    """取得 session 的使用者補充需求"""
    sess = sessions.get(session_id)
    if not sess:
        return jsonify({'error': 'session not found'}), 404
    return jsonify({'refinements': sess.get('userRefinements', '')})


@app.route('/api/session/<session_id>/versions', methods=['GET'])
def get_session_versions_api(session_id):
    """取得 session 的版本列表"""
    from models import get_versions
    versions = get_versions(session_id)
    return jsonify({'versions': versions})


@app.route('/api/session/<session_id>/dashboard-url', methods=['GET'])
def get_session_dashboard_url(session_id):
    """取得 session 的儀表板 URL"""
    from models import get_versions
    versions = get_versions(session_id)
    if not versions:
        return jsonify({'dashboard_url': ''})
    latest_version = versions[0]['version']
    return jsonify({'dashboard_url': f'/dashboard/{session_id}/v{latest_version}'})


@app.route('/api/session/<session_id>/selected-sheets', methods=['GET'])
def get_session_selected_sheets_endpoint(session_id):
    """取得 session 的已勾選工作表"""
    sess = sessions.get(session_id)
    if not sess:
        return jsonify({'error': 'session not found'}), 404
    return jsonify({'selectedSheets': sess.get('selectedSheets', [])})


@app.route('/api/generate', methods=['POST'])
def generate_dashboard():
    """LLM 生成戰情表 HTML"""
    try:
        data = request.get_json()
        session_id = data['session_id']
        user_refinements = data.get('refinements', '')
        suggestions = data.get('suggestions') or sessions.get(session_id, {}).get('suggestions', [])
        if not suggestions:
            suggestions = _mock_suggest_from_sheets(session_id)

        # Collect actual data from all sheets in this session
        sheet_data = {}
        sheets_info = sessions.get(session_id, {}).get('sheets', {})
        for filename, info in sheets_info.items():
            for s in info.get('sheets', []):
                key = f"{filename}/{s['name']}"
                sheet_data[key] = s.get('data_json_compatible', s.get('data', []))

        # Also include custom data from manually added charts
        for s in suggestions:
            if s.get('_customData') and s.get('source'):
                src_key = f"{s['source']['file']}/{s['source']['sheet']}"
                if src_key not in sheet_data:
                    sheet_data[src_key] = s['_customData']

        from llm_agent import generate_layout
        try:
            dashboard_html = generate_layout(suggestions, user_refinements, sheet_data)
        except Exception as e2:
            return jsonify({'error': f'generate_layout failed: {e2}', 'suggestions_preview': str(suggestions)[:200]}), 500

        from models import save_version
        version_id = save_version(session_id, dashboard_html)

        return jsonify({
            'dashboard_url': f'/dashboard/{session_id}/v{version_id}',
            'version': version_id
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


def _mock_suggest_from_sheets(session_id):
    """Generate basic suggestions from uploaded sheets."""
    sheets_data = sessions.get(session_id, {}).get('sheets', {})
    suggestions = []
    for filename, info in sheets_data.items():
        for sheet in info.get('sheets', []):
            cols = sheet.get('columns', [])
            dtypes = sheet.get('dtypes', {})
            numeric_cols = [c for c in cols if dtypes.get(c) == 'numeric']
            text_cols = [c for c in cols if dtypes.get(c) == 'text']
            if text_cols and numeric_cols:
                suggestions.append({
                    'id': f'{filename}_{sheet["name"]}_bar_0'.replace('.', '_').replace(' ', '_'),
                    'title': f'{sheet["name"]} - {text_cols[0]} vs {numeric_cols[0]}',
                    'type': 'bar',
                    'source': {'file': filename, 'sheet': sheet['name']},
                    'xColumn': text_cols[0],
                    'yColumn': numeric_cols[0],
                    'description': '資料視覺化'
                })
    return suggestions[:4]


@app.route('/api/regenerate/<session_id>/<component_id>', methods=['POST'])
def regenerate_component(session_id, component_id):
    """微調模式：只重新生成特定元件"""
    data = request.get_json()
    from llm_agent import regenerate_component
    updated_html = regenerate_component(session_id, component_id, data)
    return jsonify({'html': updated_html})


@app.route('/api/versions/<session_id>', methods=['GET'])
def list_versions(session_id):
    from models import get_versions
    return jsonify({'versions': get_versions(session_id)})


@app.route('/dashboard/<session_id>/<version>', methods=['GET'])
def view_dashboard(session_id, version):
    html = get_version_html(session_id, int(version.lstrip('v')))
    if not html:
        return 'Dashboard not found', 404
    resp = make_response(html)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/api/templates', methods=['GET'])
def list_templates_route():
    return jsonify({'templates': list_templates()})


@app.route('/api/templates', methods=['POST'])
def save_template_route():
    data = request.get_json()
    save_template(data['name'], data.get('config', {}), data.get('insight_prompt', ''))
    return jsonify({'status': 'ok'})


@app.route('/api/templates/<int:template_id>/apply', methods=['POST'])
def apply_template(template_id):
    """套用模板 → 建立新 session 並回傳給前端跳轉"""
    tpl = get_template(template_id)
    if not tpl:
        return jsonify({'error': 'template not found'}), 404
    new_session_id = str(uuid.uuid4())
    import json
    config = json.loads(tpl['config'])
    sessions[new_session_id] = {'files': [], 'sheets': {}, 'template': config}
    return jsonify({'session_id': new_session_id})


@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template_route(template_id):
    conn = _get_conn()
    conn.execute('DELETE FROM templates WHERE id = ?', (template_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=False)
