#!/usr/bin/env python3
"""快速修复配置文件"""

import json
from pathlib import Path

config_file = Path("config/config.json")

# 读取配置
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 修复字段名
changed = False

if 'google_sheets_credentials' in config:
    config['google_credentials_file'] = config.pop('google_sheets_credentials')
    changed = True
    print("✅ 更新字段: google_sheets_credentials → google_credentials_file")

# 修复路径
if config.get('google_credentials_file') == 'config/google-credentials.json':
    config['google_credentials_file'] = 'config/credentials.json'
    changed = True
    print("✅ 更新路径: google-credentials.json → credentials.json")

if changed:
    # 保存配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print("\n✅ 配置文件已更新！")
else:
    print("✅ 配置文件已经是最新的")

# 显示Google相关配置
print("\n当前配置：")
print(f"  google_credentials_file: {config.get('google_credentials_file')}")
print(f"  google_sheet_id: {config.get('google_sheet_id')}")
