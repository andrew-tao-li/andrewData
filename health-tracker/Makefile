.PHONY: help install setup test parse sync stats report clean

help:
	@echo "Health Tracker - 可用命令:"
	@echo ""
	@echo "  make install    - 安装依赖"
	@echo "  make setup      - 初始化配置"
	@echo "  make test       - 运行测试"
	@echo "  make parse      - 解析今天的笔记"
	@echo "  make sync       - 同步到 Google Sheets"
	@echo "  make stats      - 显示统计数据"
	@echo "  make report     - 生成周报"
	@echo "  make clean      - 清理临时文件"

install:
	pip install -r requirements.txt

setup:
	@if [ ! -f config/config.json ]; then \
		cp config/config.example.json config/config.json; \
		echo "✓ 已创建 config/config.json，请编辑填写配置"; \
	else \
		echo "config/config.json 已存在"; \
	fi

test:
	python tests/test_parser.py

parse:
	python cli.py parse --date today

sync:
	python cli.py sync --days 7

stats:
	python cli.py stats --days 30

report:
	python cli.py report --period week

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
