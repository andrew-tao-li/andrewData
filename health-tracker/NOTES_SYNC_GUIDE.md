# iPhone 备忘录 -> Obsidian 自动同步（18:00 前）

## 目标
- iPhone 上继续使用「备忘录」口述记录。
- Mac 在每天 19:00、20:00、21:00 自动检查并尝试把内容并入当天 Obsidian 日记。
- 当天首次真正同步成功后，当晚后续时段不再重复同步。
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
- 19:00/20:00/21:00 自动导入到当天 Obsidian 日记的 `（今日备忘）...（今日备忘结束）` 区块。
- 已默认开启：写入 Obsidian 成功后，自动清空《晨间语音备忘》正文（保留标题）。
- 每次成功同步前，会先把本次口述内容归档到本地 `logs/notes-sync-archive/`，便于回溯。

## 清空备忘录也可继续用
- 你可以在同一个《晨间语音备忘》里随时删除或清空内容，然后继续口述。
- 脚本已开启“删减重置”识别：当检测到内容被大幅删减/重写时，会把当前内容当作新的起点继续同步，不要求你改标题。
- 相关配置在 `config/notes_sync.json`：
  - `truncate_reset_enabled`
  - `truncate_reset_min_shrink_ratio`
  - `truncate_reset_max_similarity`

## 手动触发（排障）
- `./notes-sync-guard.sh`

## 日志
- 运行日志：`logs/notes-sync-YYYYMMDD.log`
- launchd stderr：`logs/launchd-notes-sync-err.log`
