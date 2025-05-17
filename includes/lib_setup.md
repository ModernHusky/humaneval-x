# 链接库文件配置

如果你的私有库除了头文件外，还需要链接 `.lib`, `.a` 或 `.so` 文件，可以按照以下步骤操作：

## 创建库配置文件

1. 在 `includes` 目录下创建一个 `lib_config.json` 文件
2. 使用以下格式配置需要链接的库文件：

```json
{
  "lib_paths": ["./includes/libs"],
  "libs": ["mylib1", "mylib2"]
}
```

其中：
- `lib_paths`: 库文件所在的路径列表（相对于项目根目录或绝对路径）
- `libs`: 需要链接的库名称列表（不包含前缀 `lib` 和扩展名）

## 修改execution.py

如果你的库链接配置比较复杂，你需要修改 `execution.py` 文件中的编译命令：

```python
# 读取库配置
lib_config_path = os.path.join(current_path, "includes", "lib_config.json")
if os.path.exists(lib_config_path):
    with open(lib_config_path, 'r') as f:
        lib_config = json.loads(f.read())
    
    # 添加库路径
    for lib_path in lib_config.get("lib_paths", []):
        compile_cmd.extend(["-L", lib_path])
    
    # 添加库
    for lib in lib_config.get("libs", []):
        compile_cmd.extend(["-l", lib])
``` 