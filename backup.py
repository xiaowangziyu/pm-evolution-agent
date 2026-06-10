import shutil
import os
from datetime import datetime, timedelta

def backup_database():
    """每日全量备份数据库，保留最近7天"""
    db_file = 'pm_evolution.db'
    backup_dir = 'backup'
    
    # 创建备份目录
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 清理7天前的旧备份
    now = datetime.now()
    for filename in os.listdir(backup_dir):
        if filename.startswith('pm_evolution_') and filename.endswith('.db'):
            try:
                file_datetime = datetime.strptime(filename.split('_')[2], '%Y%m%d_%H%M%S')
                if (now - file_datetime).days > 7:
                    os.remove(os.path.join(backup_dir, filename))
                    print(f'🗑️ 删除旧备份: {filename}')
            except:
                pass
    
    # 执行备份
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'pm_evolution_{timestamp}.db')
    
    if os.path.exists(db_file):
        shutil.copy(db_file, backup_file)
        print(f'✅ 备份成功: {backup_file}')
        print(f'📦 备份大小: {os.path.getsize(backup_file) // 1024} KB')
    else:
        print(f'❌ 数据库文件不存在')

if __name__ == '__main__':
    backup_database()