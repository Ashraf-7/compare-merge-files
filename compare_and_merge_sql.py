import sys
import os
import sqlparse

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def split_statements(sql_text):
    # Use sqlparse for robust splitting
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
    print(f"Diff report written to {report_file}")

def merge_files_accept_all_from_second(file1, file2, output_file):
    stmts1 = split_statements(read_file(file1))
    stmts2 = split_statements(read_file(file2))
    merged = stmts2[:]
    for stmt in stmts1:
        if stmt not in merged:
            merged.append(stmt)
    write_file(output_file, merged)
    print(f"Merged file written to {output_file}")

def interactive_merge(file1, file2, output_file):
    stmts1 = split_statements(read_file(file1))
    stmts2 = split_statements(read_file(file2))

    set1 = set(stmts1)
    set2 = set(stmts2)

    merged = []
    # Add all statements from file1, ask about conflicts
    for stmt in stmts1:
        if stmt in set2:
            merged.append(stmt)
        else:
            print("\nStatement only in first file:\n")
            print(stmt)
            choice = input("Keep this statement? (y/n): ").strip().lower()
            if choice == 'y':
                merged.append(stmt)
    # Add statements only in file2
    for stmt in stmts2:
        if stmt not in set1:
            print("\nStatement only in second file:\n")
            print(stmt)
            choice = input("Add this statement? (y/n): ").strip().lower()
            if choice == 'y':
                merged.append(stmt)
    write_file(output_file, merged)
    print(f"Interactive merge complete. Output written to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage:")
        print("  python compare_and_merge_sql.py compare <file1.sql> <file2.sql>")
        print("  python compare_and_merge_sql.py merge <file1.sql> <file2.sql> <output.sql>")
        print("  python compare_and_merge_sql.py interactive-merge <file1.sql> <file2.sql> <output.sql>")
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
        merge_files_accept_all_from_second(file1, file2, output_file)
    elif mode == "interactive-merge":
        if len(sys.argv) < 5:
            print("Please specify output file for interactive merge.")
            sys.exit(1)
        output_file = sys.argv[4]
        interactive_merge(file1, file2, output_file)
    else:
        print("Unknown mode. Use 'compare', 'merge', or 'interactive-merge'.")