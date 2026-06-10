with open('logs/error.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    # 显示最后50行
    for line in lines[-50:]:
        print(line, end='')