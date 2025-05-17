# 私有库头文件目录

这个目录用于存放私有库的头文件和库文件，HumanEval-X 在编译测试代码时会自动包含这个目录。

## 目录结构

```
includes/
├── README.md             # 本文件
├── lib_config.json       # 库配置文件
├── lib_setup.md          # 链接库文件配置说明
├── VSD.h                 # 示例私有库头文件
├── example_usage.cpp     # 示例使用代码
└── libs/                 # 存放 .lib, .a, .so 等库文件
    └── ... 
```

## 使用方法

### 1. 添加头文件

1. 将你的私有库头文件（`.h`或`.hpp`文件）直接放在此目录下
2. 在你的代码中正常引用这些头文件，例如：

```cpp
// 方式1: 不使用子目录
#include <VSD.h>

// 方式2: 使用子目录组织头文件
#include <mysubdir/mylib.h>
```

### 2. 添加链接库

如果你的私有库需要链接额外的库文件：

1. 将 `.lib`, `.a` 或 `.so` 文件放在 `includes/libs` 目录下
2. 编辑 `lib_config.json` 文件，添加需要链接的库名称：

```json
{
  "lib_paths": ["./includes/libs"],
  "libs": ["mylib1", "mylib2"]
}
```

## 示例：使用 VSD.h

VSD.h 是一个示例私有库，提供了字符串向量处理功能。使用示例：

```cpp
#include <iostream>
#include <VSD.h>

int main() {
    using namespace VSD;
    
    VectorStringData vsd;
    vsd.addString("Hello");
    vsd.addString("World");
    
    std::string processed = processString("test");
    
    std::cout << "Processed string: " << processed << std::endl;
    std::cout << "Vector contents:" << std::endl;
    for (const auto& str : vsd.getData()) {
        std::cout << "- " << str << std::endl;
    }
    
    return 0;
}
```

## 注意事项

- 库名称不包含前缀 `lib` 和扩展名，例如 `libmylib.so` 应该写为 `mylib`
- Windows 下的库文件通常是 `.lib` 文件，Linux 下通常是 `.a` 或 `.so` 文件
- 如果有更复杂的依赖关系，可能需要修改 `execution.py` 中的编译命令
- 确保你的代码中正确引用了头文件，使用 `<>` 而不是 `""`
- 对于纯头文件实现的库（如示例中的 VSD.h），不需要在 `lib_config.json` 中添加任何库 