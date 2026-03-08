# iPhone 备忘录 -> Obsidian 自动同步（18:00 前）

## 目标
- iPhone 上继续使用「备忘录」口述记录。
- Mac 在每天 17:40 和 17:55 自动把新增内容并入当天 Obsidian 日记。
- 写入格式：
  - 开始标记：`（今日备忘）`
  - 结束标记：`（今日备忘结束）`

## 一次性设置
1. 运行：`./setup-notes-sync.sh`
2. 确认 `config/notes_sync.json` 里的 `source_note_title` 与你 iPhone 上用于口述的备忘录标题一致。
3. 如果该标题对应的备忘录不存在，脚本会在 Notes 里自动创建。

## 推荐的 iPhone 最简输入方式
- 用「快捷指令」创建一个 `晨间速记`：
  1. 动作 `听写文本`（Speak Text）
  2. 动作 `获取当前日期`
  3. 动作 `格式化日期` 为 `yyyy-MM-dd HH:mm`
  4. 动作 `文本` 组合成：`[时间戳]\n听写内容\n`
  5. 动作 `追加到备忘录`（目标标题与 `source_note_title` 一致）
- 这样每条语音天然带时间戳。

## 日常效果
- 你在 iPhone 说话记录后，无需手工复制。
- 17:40/17:55 自动导入到当天 Obsidian 日记的 `（今日备忘）...（今日备忘结束）` 区块。

## 手动触发（排障）
- `./notes-sync-guard.sh`

## 日志
- 运行日志：`logs/notes-sync-YYYYMMDD.log`
- launchd stderr：`logs/launchd-notes-sync-err.log`
