import sys
import os
import sqlparse
import difflib

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

def generate_diff_report(file1, file2, report_file):
    sql1 = format_sql(read_file(file1))
    sql2 = format_sql(read_file(file2))
    lines1 = sql1.splitlines()
    lines2 = sql2.splitlines()

    diff = list(difflib.ndiff(lines1, lines2))

    with open(report_file, 'w', encoding='utf-8', errors='ignore') as f:
        for line in diff:
            if line.startswith('- '):
                f.write(f"REMOVED: {line[2:]}\n")
            elif line.startswith('+ '):
                f.write(f"ADDED:   {line[2:]}\n")
            elif line.startswith('? '):
                # This line shows detailed char-level changes, can skip or keep for debugging
                continue
            else:
                f.write(f"        {line[2:]}\n")
    print(f"Readable diff report written to {report_file}")

def merge_files_line_by_line(file1, file2, output_file):
    sql1 = format_sql(read_file(file1))
    sql2 = format_sql(read_file(file2))
    lines1 = sql1.splitlines()
    lines2 = sql2.splitlines()

    # Use difflib to merge only the changed lines
    merged = []
    sm = difflib.SequenceMatcher(None, lines1, lines2)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            merged.extend(lines1[i1:i2])
        elif tag == 'replace':
            merged.extend(lines2[j1:j2])
        elif tag == 'delete':
            # Optionally, skip or keep deletions
            pass
        elif tag == 'insert':
            merged.extend(lines2[j1:j2])
    write_file(output_file, merged)
    print(f"Merged file written to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage:")
        print("  python compare_and_merge_sql.py compare <file1.sql> <file2.sql>")
        print("  python compare_and_merge_sql.py merge <file1.sql> <file2.sql> <output.sql>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    file1 = sys.argv[2]
    file2 = sys.argv[3]

    if mode == "compare":
        report_file = "diff_report.txt"
        generate_diff_report(file1, file2, report_file)
    elif mode == "merge":
        if len(sys.argv) < 5:
            print("Please specify output file for merge.")
            sys.exit(1)
        output_file = sys.argv[4]
        merge_files_line_by_line(file1, file2, output_file)
    else:
        print("Unknown mode. Use 'compare' or 'merge'.")