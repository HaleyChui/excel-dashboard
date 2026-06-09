"""
LLM Agent：建議圖表配置、生成戰情表佈局
"""
import json
import os
import subprocess
import sys

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
                    if _v and not _v.startswith('***'):
                        os.environ.setdefault(_k.strip(), _v)

LLM_BACKEND = os.environ.get('LLM_BACKEND', 'openrouter')


def call_llm(prompt, system='', expect_json=False):
    if LLM_BACKEND == 'openrouter':
        return _call_openrouter(prompt, system, expect_json)
    elif LLM_BACKEND == 'hermes':
        return _call_hermes(prompt, system, expect_json)
    else:
        return _mock_response(prompt, expect_json)


def _call_openrouter(prompt, system, expect_json):
    try:
        from openai import OpenAI
        client = OpenAI(base_url='https://openrouter.ai/api/v1',
                        api_key=os.environ.get('OPENROUTER_API_KEY', ''))
        msgs = []
        if system:
            msgs.append({'role': 'system', 'content': system[:4000]})
        msgs.append({'role': 'user', 'content': prompt[:8000]})
        resp = client.chat.completions.create(model='openrouter/auto', messages=msgs,
                                               temperature=0.3, max_tokens=8192)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[OpenRouter] error: {e}", file=sys.stderr)
        return _mock_response(prompt, expect_json)


def _call_hermes(prompt, system, expect_json):
    full = f"{system}\n\n{prompt}" if system else prompt
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(full)
        tmp = f.name
    try:
        r = subprocess.run(['hermes', 'chat', '-q', f'@{tmp}', '-Q', '--yolo'],
                           capture_output=True, text=True, timeout=600,
                           env={**os.environ, 'HERMES_YOLO_MODE': '1'})
        if r.returncode != 0:
            return _mock_response(prompt, expect_json)
        out = r.stdout.strip()
        if out.startswith('session_id:'):
            out = out.split('\n', 1)[1].strip() if '\n' in out else ''
        return out
    finally:
        os.unlink(tmp)


def _mock_response(prompt, expect_json):
    return json.dumps([]) if expect_json else ''


SYSTEM_PROMPT_BASE = """你是一個戰情表生成專家。你的工作是分析使用者上傳的 Excel 資料，
並生成一個可用的戰情表 HTML 頁面（Vue 3 + Bootstrap 5 + ECharts）。

生成原則：
1. 使用者提供的是 **實際資料**，不要捏造
2. 圖表必須使用 ECharts CDN
3. Vue 3 使用 CDN 載入
4. Bootstrap 5 使用 CDN 載入
5. 所有圖表容器必須有固定高度（240-280px）
6. 繁體中文 UI
7. 配色參考 Trading Terminal 深色主題"""

DESIGN_SYSTEM_CONTEXT = """
## 設計系統參考
### Trading Terminal 暗色主題
--terminal-bg: #0D0D0D; --terminal-surface: #141414;
--terminal-gain: #00D4AA; --terminal-loss: #FF4757;
--terminal-warning: #FFB800; --terminal-border: #2A2A2A;

### Dashboard 佈局
- 左側邊欄 + 右側內容區
- 頂部 KPI 卡片列
- 主圖表區 2-column grid
- 底部資料表格（zebra stripe, sticky header）
- 底部洞察分析區塊
"""


def _build_prompt(selected_sheets, user_refinements=''):
    sheets_json = json.dumps(selected_sheets, ensure_ascii=False, indent=2)
    return (f"{SYSTEM_PROMPT_BASE}\n{DESIGN_SYSTEM_CONTEXT}\n\n"
            f"## 使用者上傳的資料\n{sheets_json}\n\n"
            f"## 使用者需求\n{user_refinements or '請根據資料特性，自動選取最佳圖表類型並生成戰情表。'}\n\n"
            f"## 輸出格式\n請輸出一個完整的 HTML 檔案。只輸出 HTML 程式碼，不要加任何說明文字。")


def suggest_charts(selected_sheets):
    prompt = _build_prompt(selected_sheets)
    prompt += "\n請回傳 JSON 格式的圖表建議，格式如下：\n[\n  {\n    \"id\": \"chart_1\",\n    \"title\": \"圖表標題\",\n    \"type\": \"bar|line|pie|radar|scatter\",\n    \"source\": {\"file\": \"檔名\", \"sheet\": \"Sheet名\"},\n    \"xColumn\": \"X軸欄位\",\n    \"yColumn\": \"Y軸欄位\",\n    \"description\": \"為什麼選這個圖表\"\n  }\n]\n只回傳 JSON，不要其他文字。"
    raw = call_llm(prompt, expect_json=True)
    try:
        result = json.loads(raw)
        if isinstance(result, list) and len(result) > 0:
            return result
    except (json.JSONDecodeError, TypeError):
        pass
    return _mock_suggest(selected_sheets)


def generate_layout(suggestions, user_refinements='', sheet_data=None):
    data_json = json.dumps(sheet_data or {}, ensure_ascii=False, indent=2)
    if len(data_json) > 3000:
        data_json = data_json[:3000] + '\n... (truncated)'
    prompt = (f"{SYSTEM_PROMPT_BASE}\n{DESIGN_SYSTEM_CONTEXT}\n\n"
              f"## 圖表配置\n{json.dumps(suggestions, ensure_ascii=False, indent=2)}\n\n"
              f"## 實際資料\n{data_json}\n\n"
              f"## 使用者補充需求\n{user_refinements or '無'}\n\n"
              f"請生成完整的戰情表 HTML 頁面。只輸出 HTML 程式碼。\n\n"
              f"**重要提醒**：\n"
              f"- 所有 JavaScript 程式碼必須是標準 JS 語法，不要用 Python 語法\n"
              f"- 例如：用 key.split('/').pop() 而非 key.rsplit('/', 1)[-1]\n"
              f"- 例如：用 Object.keys(obj).length 而非 len(obj)\n"
              f"- 例如：用 array.isArray(x) 而非 isinstance(x, list)")
    raw = call_llm(prompt, system=SYSTEM_PROMPT_BASE)
    if raw.startswith('<'):
        return raw
    return _generate_mock_html(suggestions, sheet_data)


def regenerate_component(session_id, component_id, config):
    return f'<!-- Updated component {component_id} -->'


def _mock_suggest(selected_sheets):
    suggestions = []
    for idx, sheet in enumerate(selected_sheets):
        cols = sheet.get('columns', [])
        dtypes = sheet.get('dtypes', {})
        numeric_cols = [c for c in cols if dtypes.get(c) == 'numeric']
        text_cols = [c for c in cols if dtypes.get(c) == 'text']
        datetime_cols = [c for c in cols if dtypes.get(c) == 'datetime']
        base_id = f'{sheet["file"]}_{sheet["sheet"]}'.replace('.', '_').replace(' ', '_')

        if datetime_cols and numeric_cols:
            suggestions.append({
                'id': f'{base_id}_line', 'title': f'{sheet["sheet"]} - {numeric_cols[0]}趨勢',
                'type': 'line', 'source': {'file': sheet['file'], 'sheet': sheet['sheet']},
                'xColumn': datetime_cols[0], 'yColumn': numeric_cols[0],
                'description': '時間序列建議用折線圖'
            })
        if text_cols and numeric_cols:
            suggestions.append({
                'id': f'{base_id}_bar', 'title': f'{sheet["sheet"]} - {text_cols[0]} vs {numeric_cols[0]}',
                'type': 'bar', 'source': {'file': sheet['file'], 'sheet': sheet['sheet']},
                'xColumn': text_cols[0], 'yColumn': numeric_cols[0],
                'description': '類別比較建議用長條圖'
            })
            if len(numeric_cols) >= 2:
                suggestions.append({
                    'id': f'{base_id}_pie', 'title': f'{sheet["sheet"]} - {text_cols[0]}佔比',
                    'type': 'pie', 'source': {'file': sheet['file'], 'sheet': sheet['sheet']},
                    'xColumn': text_cols[0], 'yColumn': numeric_cols[0],
                    'description': '佔比分析建議用圓餅圖'
                })
    return suggestions


def _generate_mock_html(suggestions, sheet_data=None):
    """用模板 + 真實資料生成完整戰情表 HTML"""
    sheet_data = sheet_data or {}

    # 讀取模板
    tpl_path = os.path.join(os.path.dirname(__file__), 'templates', 'dashboard_template.html')
    if not os.path.exists(tpl_path):
        return '<!-- template not found -->'
    with open(tpl_path, encoding='utf-8') as f:
        html = f.read()

    # 準備資料
    all_rows = []
    for key, rows in sheet_data.items():
        fname = key.split('/')[0] if '/' in key else key
        sname = key.split('/', 1)[1] if '/' in key else ''
        for r in rows:
            all_rows.append(dict(r, _file=fname, _sheet=sname))

    # KPI
    kpi_list = []
    seen = set()
    for key, rows in sheet_data.items():
        if not rows:
            continue
        sname = key.rsplit('/', 1)[-1]
        for r in rows:
            for k, v in r.items():
                if isinstance(v, (int, float)) and not k.startswith('_'):
                    label = f"{sname}_{k}"
                    if label not in seen:
                        seen.add(label)
                        total = sum(x.get(k, 0) for x in rows if isinstance(x.get(k), (int, float)))
                        kpi_list.append({"label": label, "value": f"{total:,.0f}"})
        if len(kpi_list) >= 4:
            break
    kpi_list = kpi_list[:4]

    # 資料來源
    src_list = []
    for key in sheet_data:
        src_list.append({"file": key.split('/')[0] if '/' in key else key,
                         "sheet": key.split('/', 1)[1] if '/' in key else '',
                         "key": key})
    row_count = sum(len(rows) for rows in sheet_data.values())

    # Chart divs
    colors = ['#00D4AA', '#FFB800', '#5B8FF9', '#FF4757', '#A855F7', '#06B6D4']
    chart_divs_parts = []
    chart_scripts = []
    # Gridstack layout: 12 columns, place charts in a grid
    # Each chart takes 6 columns (half width), stack vertically
    for i, s in enumerate(suggestions):
        sid = s['id']
        src_key = f"{s['source']['file']}/{s['source']['sheet']}"
        rows = sheet_data.get(src_key, [])
        c = colors[i % len(colors)]
        # Gridstack position: x = (i % 2) * 6, y = floor(i / 2) * 10 (each row ~10 grid units high)
        gs_x = (i % 2) * 6
        gs_y = (i // 2) * 10
        gs_w = 6
        gs_h = 10
        chart_divs_parts.append(
            '<div class="chart-card-wrap grid-stack-item" gs-x="' + str(gs_x) + '" gs-y="' + str(gs_y) + '" gs-w="' + str(gs_w) + '" gs-h="' + str(gs_h) + '">'
            '<div class="grid-stack-item-content">'
            '<div class="chart-card">'
            '<div class="chart-header">'
            '<span class="material-symbols-outlined chart-icon">bar_chart</span>'
            '<span class="chart-title">' + s['title'] + '</span>'
            '</div>'
            '<div class="chart-body"><div id="' + sid + '" class="chart-canvas"></div></div>'
            '</div></div></div>'
        )
        chart_scripts.append(_build_chart_js(sid, s['type'], s.get('xColumn', ''),
                                             s.get('yColumn', ''), rows, c))

    # 資料表格
    table_html = ''
    if all_rows:
        disp = all_rows[:50]
        hds = [k for k in disp[0].keys() if not k.startswith('_')]
        hdr = ''
        for ii, h in enumerate(hds):
            hdr += '<th onclick="sortTable(' + str(ii) + ')">' + h + '<span style="margin-left:4px;opacity:0.4;font-size:10px">&#8645;</span></th>'
        body = ''
        for row in disp:
            cells = ''
            for h in hds:
                cells += '<td>' + str(row.get(h, '')) + '</td>'
            body += '<tr>' + cells + '</tr>'
        table_html = (
            '<div class="data-table-wrap">'
            '<div class="data-table-scroll">'
            '<table class="data-table">'
            '<thead><tr>' + hdr + '</tr></thead>'
            '<tbody>' + body + '</tbody>'
            '</table></div></div>'
        )

    # 替換占位符
    html = html.replace('__SHEET_DATA__', json.dumps(sheet_data, ensure_ascii=False))
    html = html.replace('__SOURCES__', json.dumps(src_list, ensure_ascii=False))
    html = html.replace('__KPIS__', json.dumps(kpi_list, ensure_ascii=False))
    html = html.replace('__TOTAL_ROWS__', str(row_count))
    html = html.replace('__CHART_COUNT__', str(len(suggestions)))
    html = html.replace('__CHART_DIVS__', '\n'.join(chart_divs_parts))
    html = html.replace('__TABLE_HTML__', table_html)
    html = html.replace('__CHART_SCRIPTS__', '\n'.join(chart_scripts))

    return html


def _build_chart_js(sid, chart_type, x_col, y_col, rows, color='#00D4AA'):
    """Build ECharts init JS — 使用字串拼接避免 f-string 問題"""
    if not rows:
        return '// no data for ' + sid

    def get_vals(col):
        return [r.get(col, '') for r in rows]
    def get_nums(col):
        return [float(r.get(col, 0) or 0) for r in rows]

    x_vals = get_vals(x_col) if x_col else [str(i+1) for i in range(len(rows))]

    # Color palette
    default_colors = ['#00D4AA', '#FFB800', '#5B8FF9', '#FF4757', '#A855F7', '#06B6D4', '#F59E0B', '#10B981']
    cj = json.dumps(default_colors, ensure_ascii=False)

    if chart_type == 'pie':
        from collections import defaultdict
        agg = defaultdict(float)
        for r in rows:
            k = str(r.get(x_col, '未知'))
            try: agg[k] += float(r.get(y_col, 0))
            except: agg[k] += 0
        dj = json.dumps([{'name': k, 'value': round(v, 2)} for k, v in agg.items()], ensure_ascii=False)
        return (
            "(function(){const c=echarts.init(document.getElementById('" + sid + "'));c.setOption({"
            "color:" + cj + ","
            "tooltip:{trigger:'item',formatter:'{b}: {c} ({d}%)',"
            "backgroundColor:'#1A1A1A',borderColor:'#2A2A2A',textStyle:{color:'#FFF',fontSize:12}},"
            "series:[{type:'pie',radius:['38%','68%'],data:" + dj + ","
            "label:{color:'#AAA',fontSize:11,formatter:'{b}\\n{d}%'},"
            "labelLine:{lineStyle:{color:'#2A2A2A'}},"
            "itemStyle:{borderColor:'#141414',borderWidth:2},"
            "emphasis:{itemStyle:{shadowBlur:10}}}}]})})()")

    if chart_type == 'doughnut':
        from collections import defaultdict
        agg = defaultdict(float)
        for r in rows:
            k = str(r.get(x_col, '未知'))
            try: agg[k] += float(r.get(y_col, 0))
            except: agg[k] += 0
        dj = json.dumps([{'name': k, 'value': round(v, 2)} for k, v in agg.items()], ensure_ascii=False)
        return (
            "(function(){const c=echarts.init(document.getElementById('" + sid + "'));c.setOption({"
            "color:" + cj + ","
            "tooltip:{trigger:'item',formatter:'{b}: {c} ({d}%)',"
            "backgroundColor:'#1A1A1A',borderColor:'#2A2A2A',textStyle:{color:'#FFF',fontSize:12}},"
            "series:[{type:'pie',radius:['50%','70%'],data:" + dj + ","
            "label:{color:'#AAA',fontSize:11,formatter:'{b}\\n{d}%'},"
            "labelLine:{lineStyle:{color:'#2A2A2A'}},"
            "itemStyle:{borderColor:'#141414',borderWidth:2},"
            "emphasis:{itemStyle:{shadowBlur:10}}}}]})})()")

    if chart_type == 'scatter':
        pairs = []
        for r in rows:
            try: pairs.append([float(r.get(x_col, 0) or 0), float(r.get(y_col, 0) or 0)])
            except: pass
        pj = json.dumps(pairs)
        return (
            "(function(){const c=echarts.init(document.getElementById('" + sid + "'));c.setOption({"
            "tooltip:{trigger:'item',backgroundColor:'#1A1A1A',borderColor:'#2A2A2A',textStyle:{color:'#FFF',fontSize:12}},"
            "xAxis:{type:'value',splitLine:{lineStyle:{color:'#1A1A1A'}},axisLabel:{color:'#828282'}},"
            "yAxis:{type:'value',splitLine:{lineStyle:{color:'#1A1A1A'}},axisLabel:{color:'#828282'}},"
            "series:[{type:'scatter',symbolSize:12,data:" + pj + ","
            "itemStyle:{color:'" + color + "',shadowBlur:4,shadowColor:'" + color + "33'}}]})})()")

    if chart_type == 'line':
        y_vals = get_nums(y_col)
        xj = json.dumps([str(v) for v in x_vals], ensure_ascii=False)
        yj = json.dumps(y_vals, ensure_ascii=False)
        return (
            "(function(){const c=echarts.init(document.getElementById('" + sid + "'));c.setOption({"
            "tooltip:{trigger:'axis',backgroundColor:'#1A1A1A',borderColor:'#2A2A2A',textStyle:{color:'#FFF',fontSize:12}},"
            "xAxis:{type:'category',data:" + xj + ",axisLabel:{color:'#828282',fontSize:10,rotate:30},"
            "axisLine:{lineStyle:{color:'#2A2A2A'}}},"
            "yAxis:{type:'value',splitLine:{lineStyle:{color:'#1A1A1A',type:'dashed'}},axisLabel:{color:'#828282',fontSize:11}},"
            "series:[{type:'line',data:" + yj + ",smooth:true,symbol:'circle',symbolSize:5,"
            "lineStyle:{width:2,color:'" + color + "'},itemStyle:{color:'" + color + "'},"
            "areaStyle:{color:'" + color + "15'}}]})})()")

    if chart_type == 'radar':
        # Radar chart - need multiple numeric columns
        from collections import defaultdict
        # Get all numeric columns except x_col
        numeric_cols = []
        if rows and len(rows) > 0:
            for k, v in rows[0].items():
                if k != x_col and isinstance(v, (int, float)):
                    numeric_cols.append(k)
        
        if not numeric_cols:
            numeric_cols = [y_col] if y_col else []
        
        # Aggregate by x_col
        agg = defaultdict(lambda: defaultdict(float))
        for r in rows:
            k = str(r.get(x_col, '未知'))
            for nc in numeric_cols:
                try: agg[k][nc] += float(r.get(nc, 0))
                except: agg[k][nc] += 0
        
        indicators = [{'name': nc, 'max': max((agg[k][nc] for k in agg), default=100)} for nc in numeric_cols]
        ind_j = json.dumps(indicators, ensure_ascii=False)
        series_data = []
        for k, vals in agg.items():
            series_data.append({'value': [vals[nc] for nc in numeric_cols], 'name': k})
        sd_j = json.dumps(series_data, ensure_ascii=False)
        
        return (
            "(function(){const c=echarts.init(document.getElementById('" + sid + "'));c.setOption({"
            "color:" + cj + ","
            "tooltip:{trigger:'axis',backgroundColor:'#1A1A1A',borderColor:'#2A2A2A',textStyle:{color:'#FFF',fontSize:12}},"
            "radar:{indicator:" + ind_j + ","
            "splitLine:{lineStyle:{color:'#2A2A2A'}},"
            "splitArea:{areaStyle:{color:['rgba(255,255,255,0.02)','rgba(255,255,255,0.05)']}},"
            "axisName:{color:'#828282',fontSize:11}},"
            "series:[{type:'radar',data:" + sd_j + ","
            "lineStyle:{width:2},"
            "areaStyle:{opacity:0.2}}]})})()")

    if chart_type == 'treemap':
        # Treemap - hierarchical data from x_col (category) and y_col (value)
        from collections import defaultdict
        agg = defaultdict(float)
        for r in rows:
            k = str(r.get(x_col, '未知'))
            try: agg[k] += float(r.get(y_col, 0))
            except: agg[k] += 0
        
        # Build treemap data
        tm_data = [{'name': k, 'value': round(v, 2)} for k, v in agg.items()]
        tm_j = json.dumps(tm_data, ensure_ascii=False)
        
        return (
            "(function(){const c=echarts.init(document.getElementById('" + sid + "'));c.setOption({"
            "color:" + cj + ","
            "tooltip:{trigger:'item',backgroundColor:'#1A1A1A',borderColor:'#2A2A2A',textStyle:{color:'#FFF',fontSize:12},formatter:'{b}: {c}'},"
            "series:[{type:'treemap',data:" + tm_j + ","
            "label:{color:'#FFF',fontSize:12,formatter:'{b}\\n{c}'},"
            "itemStyle:{borderColor:'#141414',borderWidth:2,shadowBlur:10,shadowColor:'rgba(0,0,0,0.5)'},"
            "emphasis:{itemStyle:{shadowBlur:20}},"
            "upperLabel:{show:true,height:30,color:'#AAA',fontSize:11}}]})})()")

    if chart_type == 'horizontal_bar' or chart_type == 'bar_horizontal':
        from collections import defaultdict
        agg = defaultdict(float)
        for r in rows:
            k = str(r.get(x_col, '未知'))
            try: agg[k] += float(r.get(y_col, 0))
            except: agg[k] += 0
        xj = json.dumps(list(agg.keys()), ensure_ascii=False)
        yj = json.dumps([round(v, 2) for v in agg.values()], ensure_ascii=False)
        return (
            "(function(){const c=echarts.init(document.getElementById('" + sid + "'));c.setOption({"
            "tooltip:{trigger:'axis',backgroundColor:'#1A1A1A',borderColor:'#2A2A2A',textStyle:{color:'#FFF',fontSize:12}},"
            "xAxis:{type:'value',splitLine:{lineStyle:{color:'#1A1A1A',type:'dashed'}},axisLabel:{color:'#828282',fontSize:11}},"
            "yAxis:{type:'category',data:" + xj + ",axisLabel:{color:'#828282',fontSize:11},"
            "axisLine:{lineStyle:{color:'#2A2A2A'}}},"
            "series:[{type:'bar',data:" + yj + ",barWidth:'45%',"
            "itemStyle:{color:'" + color + "',borderRadius:[0,3,3,0]}}]})})()")

    if chart_type == 'stacked_bar':
        # Stacked bar - need group column (x_col) and stack dimension (could be another column)
        # For simplicity, stack by a third column or use all numeric columns
        from collections import defaultdict
        # Find a stack column (categorical) - if x_col is group, use another text column
        stack_col = None
        if rows and len(rows) > 0:
            for k, v in rows[0].items():
                if k != x_col and k != y_col and isinstance(v, str):
                    stack_col = k
                    break
        
        if stack_col:
            # Stack by stack_col, group by x_col
            agg = defaultdict(lambda: defaultdict(float))
            stacks = set()
            for r in rows:
                g = str(r.get(x_col, '未知'))
                s = str(r.get(stack_col, '其他'))
                stacks.add(s)
                try: agg[g][s] += float(r.get(y_col, 0))
                except: agg[g][s] += 0
            
            stacks = list(stacks)
            series = []
            colors = default_colors
            for i, s in enumerate(stacks):
                data = [agg[g].get(s, 0) for g in agg.keys()]
                series.append({
                    'name': s,
                    'type': 'bar',
                    'stack': 'total',
                    'data': data,
                    'itemStyle': {'color': colors[i % len(colors)]}
                })
            xj = json.dumps(list(agg.keys()), ensure_ascii=False)
            series_j = json.dumps(series, ensure_ascii=False)
            return (
                "(function(){const c=echarts.init(document.getElementById('" + sid + "'));c.setOption({"
                "tooltip:{trigger:'axis',backgroundColor:'#1A1A1A',borderColor:'#2A2A2A',textStyle:{color:'#FFF',fontSize:12}},"
                "legend:{data:" + json.dumps(stacks, ensure_ascii=False) + ",textStyle:{color:'#AAA'}},"
                "xAxis:{type:'category',data:" + xj + ",axisLabel:{color:'#828282',fontSize:11},axisLine:{lineStyle:{color:'#2A2A2A'}}},"
                "yAxis:{type:'value',splitLine:{lineStyle:{color:'#1A1A1A',type:'dashed'}},axisLabel:{color:'#828282',fontSize:11}},"
                "series:" + series_j + "})})()")
        else:
            # Fallback to regular bar
            agg = defaultdict(float)
            for r in rows:
                k = str(r.get(x_col, '未知'))
                try: agg[k] += float(r.get(y_col, 0))
                except: agg[k] += 0
            xj = json.dumps(list(agg.keys()), ensure_ascii=False)
            yj = json.dumps([round(v, 2) for v in agg.values()], ensure_ascii=False)
            return (
                "(function(){const c=echarts.init(document.getElementById('" + sid + "'));c.setOption({"
                "tooltip:{trigger:'axis',backgroundColor:'#1A1A1A',borderColor:'#2A2A2A',textStyle:{color:'#FFF',fontSize:12}},"
                "xAxis:{type:'category',data:" + xj + ",axisLabel:{color:'#828282',fontSize:11},axisLine:{lineStyle:{color:'#2A2A2A'}}},"
                "yAxis:{type:'value',splitLine:{lineStyle:{color:'#1A1A1A',type:'dashed'}},axisLabel:{color:'#828282',fontSize:11}},"
                "series:[{type:'bar',data:" + yj + ",barWidth:'45%',"
                "itemStyle:{color:'" + color + "',borderRadius:[3,3,0,0]}}]})})()")

    # bar — aggregate by x_col
    from collections import defaultdict
    agg = defaultdict(float)
    for r in rows:
        k = str(r.get(x_col, '未知'))
        try: agg[k] += float(r.get(y_col, 0))
        except: agg[k] += 0
    xj = json.dumps(list(agg.keys()), ensure_ascii=False)
    yj = json.dumps([round(v, 2) for v in agg.values()], ensure_ascii=False)
    return (
        "(function(){const c=echarts.init(document.getElementById('" + sid + "'));c.setOption({"
        "tooltip:{trigger:'axis',backgroundColor:'#1A1A1A',borderColor:'#2A2A2A',textStyle:{color:'#FFF',fontSize:12}},"
        "xAxis:{type:'category',data:" + xj + ",axisLabel:{color:'#828282',fontSize:11},"
        "axisLine:{lineStyle:{color:'#2A2A2A'}}},"
        "yAxis:{type:'value',splitLine:{lineStyle:{color:'#1A1A1A',type:'dashed'}},axisLabel:{color:'#828282',fontSize:11}},"
        "series:[{type:'bar',data:" + yj + ",barWidth:'45%',"
        "itemStyle:{color:'" + color + "',borderRadius:[3,3,0,0]}}]})})()")
