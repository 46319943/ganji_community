import os
# 更改当前目录为文件锁在目录
current_path = os.path.abspath(__file__)
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

import json
# 读取配置文件
CONFIG_FILE = './setting.json'
f = open(CONFIG_FILE, "r", encoding='utf-8')
SETTING = json.load(f)
print(SETTING)



