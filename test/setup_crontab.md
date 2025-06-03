# 设置定时任务指南

在树莓派上，你可以使用crontab来设置定时任务，使天气艺术生成器能够定期自动更新。以下是设置步骤：

## 1. 确保脚本具有执行权限

首先，确保所有脚本文件都有执行权限：

```bash
chmod +x weather_art_generator.py
chmod +x display_on_eink.py
chmod +x auto_update.sh
chmod +x run_on_raspberry_pi.sh
```

## 2. 编辑crontab

打开终端，输入以下命令来编辑当前用户的crontab：

```bash
crontab -e
```

如果是第一次运行此命令，系统会提示你选择一个文本编辑器。推荐选择nano或vim，取决于你的喜好。

## 3. 添加定时任务

在打开的编辑器中，添加以下行来设置定时任务。以下是一些例子：

### 每6小时更新一次（推荐）

```
0 */6 * * * /绝对路径/auto_update.sh
```

### 每天特定时间更新（例如上午8点和下午6点）

```
0 8,18 * * * /绝对路径/auto_update.sh
```

### 每小时更新一次（不推荐，API调用频繁）

```
0 * * * * /绝对路径/auto_update.sh
```

请将`/绝对路径/`替换为你的实际脚本路径。你可以通过在脚本目录运行`pwd`命令来获取绝对路径。

## 4. 保存并退出

- 如果使用nano编辑器：按Ctrl+O保存，然后按Ctrl+X退出
- 如果使用vim编辑器：按ESC键，然后输入`:wq`并按回车键

## 5. 验证crontab是否正确设置

```bash
crontab -l
```

此命令会列出当前用户的所有cron任务。确认你的任务已正确添加。

## 6. 检查日志

脚本运行时会创建一个`weather_art.log`文件。如需查看运行情况，可以使用以下命令：

```bash
tail -f weather_art.log
```

## 注意事项

1. 确保crontab环境中能正确访问所需的环境变量和Python库。
2. 如果脚本依赖于特定的工作目录，确保在脚本中已设置好。
3. cron任务不会继承你的正常shell环境，可能需要在脚本中设置完整的路径。
4. 考虑API限制和费用，不要设置过于频繁的更新。 