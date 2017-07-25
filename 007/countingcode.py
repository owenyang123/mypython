import os

def walk_dir(path):
    file_path = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.lower().endswith('py'):
                file_path.append(os.path.join(root, f))
    return file_path


def count_the_code(path):
    file_name = os.path.basename(path)
    note_flag = False
    line_num = 0
    empty_line_num = 0
    note_num = 0
    with open(path) as f:
        for line in f.read().split('\n'):
            line_num += 1
            if line.strip().startswith('\"\"\"') and not note_flag:
                note_flag =True
                note_num += 1
                continue

            if line.strip().startswith('\"\"\"'):
                note_flag = False
                note_num += 1

            if line.strip().startswith('#') or note_flag:
                note_num += 1

            if len(line) == 0:
                empty_line_num += 1

    print str(file_name)
    print str(line_num)
    print str(empty_line_num)
    print str(note_num)


if __name__ == '__main__':
    for f in walk_dir('C:\github\mypython'):
        print f
        count_the_code(f)