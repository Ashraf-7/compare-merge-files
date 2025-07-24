# app.py
from flask import Flask, request, jsonify, send_file
import tempfile
import os
import sqlparse

app = Flask(__name__)

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def split_statements(sql_text):
    return [str(stmt).strip() for stmt in sqlparse.parse(sql_text) if str(stmt).strip()]

def write_file(filepath, statements):
    with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
        for stmt in statements:
            f.write(stmt.strip() + '\n\n')

def generate_diff_report(file1, file2, report_file):
    stmts1 = split_statements(read_file(file1))
    stmts2 = split_statements(read_file(file2))

    set1 = set(stmts1)
    set2 = set(stmts2)

    added = [stmt for stmt in stmts2 if stmt not in set1]
    removed = [stmt for stmt in stmts1 if stmt not in set2]
    common = [stmt for stmt in stmts1 if stmt in set2]

    with open(report_file, 'w', encoding='utf-8', errors='ignore') as f:
        f.write(f"=== Statements only in {os.path.basename(file2)} (ADDED): ===\n\n")
        for stmt in added:
            f.write(stmt + '\n\n')
        f.write(f"\n=== Statements only in {os.path.basename(file1)} (REMOVED): ===\n\n")
        for stmt in removed:
            f.write(stmt + '\n\n')
        f.write(f"\n=== Statements in BOTH files: ===\n\n")
        for stmt in common:
            f.write(stmt + '\n\n')

def merge_files_accept_all_from_second(file1, file2, output_file):
    stmts1 = split_statements(read_file(file1))
    stmts2 = split_statements(read_file(file2))
    merged = stmts2[:]
    for stmt in stmts1:
        if stmt not in merged:
            merged.append(stmt)
    write_file(output_file, merged)

@app.route('/compare', methods=['POST'])
def compare():
    file1 = request.files['file1']
    file2 = request.files['file2']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as f1, \
         tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as f2, \
         tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as report:
        f1.write(file1.read())
        f2.write(file2.read())
        f1.close()
        f2.close()
        report.close()
        generate_diff_report(f1.name, f2.name, report.name)
        with open(report.name, 'r', encoding='utf-8', errors='ignore') as rf:
            report_content = rf.read()
        os.unlink(f1.name)
        os.unlink(f2.name)
        os.unlink(report.name)
    return jsonify({'report': report_content})

@app.route('/merge', methods=['POST'])
def merge():
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
        merge_files_accept_all_from_second(f1.name, f2.name, merged.name)
        response = send_file(merged.name, as_attachment=True, download_name='merged.sql')
        # Clean up after sending
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
    app.run(host='0.0.0.0', port=3001)