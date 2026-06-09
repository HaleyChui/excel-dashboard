"""
Excel 解析器：支援多檔案、多 Sheet、自動清理髒資料
"""
import pandas as pd
import json


def parse_excel(file_path):
    """解析 Excel 檔案，回傳結構化資訊"""
    try:
        xls = pd.ExcelFile(file_path)
    except Exception as e:
        return {'error': f'無法解析 Excel: {str(e)}', 'sheets': []}

    result = {
        'filename': file_path.split('/')[-1],
        'path': file_path,
        'sheets': []
    }

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

            # ── 嘗試自動偵測 header row ──
            header_row = _detect_header(df)
            if header_row is not None:
                df = pd.read_excel(file_path, sheet_name=sheet_name,
                                   header=header_row)
            else:
                # 完全沒有 header，自動命名
                df.columns = [f'col_{i}' for i in range(len(df.columns))]

            # ── 清理 ──
            df = _clean_dataframe(df)

            # ── 型別推斷 ──
            dtypes = {}
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    dtypes[col] = 'numeric'
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    dtypes[col] = 'datetime'
                else:
                    dtypes[col] = 'text'

            # ── 統計摘要 ──
            stats = {}
            for col in df.columns:
                if dtypes[col] == 'numeric':
                    stats[col] = {
                        'min': None if df[col].isna().all() else _to_num(df[col].min()),
                        'max': None if df[col].isna().all() else _to_num(df[col].max()),
                        'mean': None if df[col].isna().all() else _to_num(df[col].mean()),
                        'unique': int(df[col].nunique())
                    }
                elif dtypes[col] == 'text':
                    stats[col] = {
                        'unique': int(df[col].nunique()),
                        'top_values': df[col].value_counts().head(5).to_dict()
                    }

            # ── 空值比例 ──
            null_ratios = {col: round(float(df[col].isna().mean()), 2)
                           for col in df.columns}

            sheet_info = {
                'name': sheet_name,
                'columns': list(df.columns),
                'rows': len(df),
                'dtypes': dtypes,
                'stats': stats,
                'null_ratios': null_ratios,
                'data': df.fillna('').head(10).to_dict('records'),
                'data_json_compatible': json.loads(df.fillna('').head(10).to_json(orient='records', date_format='iso')),
            }
            result['sheets'].append(sheet_info)

        except Exception as e:
            result['sheets'].append({
                'name': sheet_name,
                'error': str(e),
                'columns': [],
                'rows': 0
            })

    return result


def _to_num(val):
    """Convert numpy types to native Python types for JSON serialization."""
    import math
    if isinstance(val, (float, int)):
        return val
    try:
        v = float(val)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def _detect_header(df):
    """
    偵測哪一行是 header。
    啟發式：如果第一行的值大部分是字串型且唯一值夠多，視為 header。
    """
    if len(df) < 2:
        return 0 if df.iloc[0].dtype == object else None

    first_row = df.iloc[0]
    non_numeric = sum(1 for v in first_row if isinstance(v, str))
    total = len(first_row)

    # 如果第一行超過 60% 是字串 → 可能是 header
    if total > 0 and non_numeric / total > 0.6:
        return 0
    return None


def _clean_dataframe(df):
    """清理 DataFrame：去重複列名、解 merge cells、填 null"""
    # 去重複列名
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = \
            [f'{dup}_{i}' for i in range(sum(cols == dup))]
    df.columns = cols

    # 全部轉字串的欄位可能是 merge cells 造成的
    # (維持原始狀態，交給 LLM 判斷)
    return df


def parse_excel_batch(file_paths):
    """批次解析多個 Excel"""
    return [parse_excel(p) for p in file_paths]


def parse_csv_text(csv_text, delimiter=','):
    """解析 CSV 文字內容，回傳與 parse_excel 相同格式的結構"""
    import io
    import pandas as pd
    import json
    
    try:
        df = pd.read_csv(io.StringIO(csv_text), delimiter=delimiter, header=0)
    except Exception as e:
        return {'error': f'無法解析 CSV: {str(e)}', 'sheets': []}
    
    # 型別推斷
    dtypes = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            dtypes[col] = 'numeric'
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            dtypes[col] = 'datetime'
        else:
            dtypes[col] = 'text'
    
    # 統計摘要
    stats = {}
    for col in df.columns:
        if dtypes[col] == 'numeric':
            stats[col] = {
                'min': None if df[col].isna().all() else _to_num(df[col].min()),
                'max': None if df[col].isna().all() else _to_num(df[col].max()),
                'mean': None if df[col].isna().all() else _to_num(df[col].mean()),
                'unique': int(df[col].nunique())
            }
        elif dtypes[col] == 'text':
            stats[col] = {
                'unique': int(df[col].nunique()),
                'top_values': df[col].value_counts().head(5).to_dict()
            }
    
    # 空值比例
    null_ratios = {col: round(float(df[col].isna().mean()), 2)
                   for col in df.columns}
    
    sheet_info = {
        'name': 'CSV輸入',
        'columns': list(df.columns),
        'rows': len(df),
        'dtypes': dtypes,
        'stats': stats,
        'null_ratios': null_ratios,
        'data': df.fillna('').head(10).to_dict('records'),
        'data_json_compatible': json.loads(df.fillna('').head(10).to_json(orient='records', date_format='iso')),
    }
    
    return {
        'filename': 'manual_csv_input',
        'path': '',
        'sheets': [sheet_info]
    }
