from flask import Flask, request, jsonify, send_file
import tempfile
import os
import sqlparse
import difflib
import base64

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB upload limit

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def format_sql(sql_text):
    # Format SQL for consistent comparison
    return sqlparse.format(sql_text, reindent=True, keyword_case='upper')

def write_file(filepath, lines):
    # Write lines, removing consecutive blank lines
    with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
        prev_blank = False
        for line in lines:
            if line.strip() == '':
                if not prev_blank:
                    f.write('\n')
                prev_blank = True
            else:
                f.write(line.rstrip() + '\n')
                prev_blank = False

def generate_diff_report(file1, file2):
    sql1 = format_sql(read_file(file1))
    sql2 = format_sql(read_file(file2))
    lines1 = sql1.splitlines()
    lines2 = sql2.splitlines()

    diff = list(difflib.ndiff(lines1, lines2))
    report_lines = []
    for line in diff:
        if line.startswith('- '):
            report_lines.append(f"REMOVED: {line[2:]}")
        elif line.startswith('+ '):
            report_lines.append(f"ADDED:   {line[2:]}")
        elif line.startswith('? '):
            continue
        else:
            report_lines.append(f"        {line[2:]}")
    return '\n'.join(report_lines)

def merge_files_line_by_line(file1, file2, output_file):
    sql1 = format_sql(read_file(file1))
    sql2 = format_sql(read_file(file2))
    lines1 = sql1.splitlines()
    lines2 = sql2.splitlines()

    merged = []
    sm = difflib.SequenceMatcher(None, lines1, lines2)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            merged.extend(lines1[i1:i2])
        elif tag == 'replace':
            merged.extend(lines2[j1:j2])
        elif tag == 'delete':
            pass
        elif tag == 'insert':
            merged.extend(lines2[j1:j2])
    write_file(output_file, merged)

@app.route('/compare', methods=['POST'])
def compare():
    app.logger.info('Request files: %s', request.files)
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({'error': 'Both file1 and file2 are required.'}), 400
    file1 = request.files['file1']
    file2 = request.files['file2']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as f1, \
         tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as f2:
        f1.write(file1.read())
        f2.write(file2.read())
        f1.close()
        f2.close()
        report = generate_diff_report(f1.name, f2.name)
        os.unlink(f1.name)
        os.unlink(f2.name)
    return jsonify({'report': report})

@app.route('/compare_base64', methods=['POST'])
def compare_base64():
    data = request.get_json()
    if not data or 'file1' not in data or 'file2' not in data:
        return jsonify({'error': 'Both file1 and file2 are required.'}), 400
    try:
        file1_content = base64.b64decode(data['file1'])
        file2_content = base64.b64decode(data['file2'])
    except Exception as e:
        return jsonify({'error': f'Base64 decode error: {str(e)}'}), 400
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as f1, \
         tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as f2:
        f1.write(file1_content)
        f2.write(file2_content)
        f1.close()
        f2.close()
        report = generate_diff_report(f1.name, f2.name)
        os.unlink(f1.name)
        os.unlink(f2.name)
    return jsonify({'report': report})

@app.route('/merge', methods=['POST'])
def merge():
    print('Request files:', request.files)
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({'error': 'Both file1 and file2 are required.'}), 400
    file1 = request.files['file1']
    file2 = request.files['file2']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as f1, \
         tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as f2, \
         tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as merged:
        f1.write(file1.read())
        f2.write(file2.read())
        f1.close()
        f2.close()
        merged.close()
        merge_files_line_by_line(f1.name, f2.name, merged.name)
        response = send_file(merged.name, as_attachment=True, download_name='merged.sql')
        @response.call_on_close
        def cleanup():
            os.unlink(f1.name)
            os.unlink(f2.name)
            os.unlink(merged.name)
        return response

@app.route('/')
def index():
    return "SQL Compare/Merge API is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)