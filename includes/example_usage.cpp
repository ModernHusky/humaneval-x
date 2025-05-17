#include <iostream>
#include <VSD.h>

int main() {
    // 使用VSD命名空间
    using namespace VSD;
    
    // 创建VectorStringData对象
    VectorStringData vsd;
    
    // 添加一些字符串
    vsd.addString("Hello");
    vsd.addString("World");
    
    // 处理字符串
    std::string processed = processString("test");
    
    // 输出结果
    std::cout << "Processed string: " << processed << std::endl;
    std::cout << "Vector contents:" << std::endl;
    for (const auto& str : vsd.getData()) {
        std::cout << "- " << str << std::endl;
    }
    
    return 0;
} 