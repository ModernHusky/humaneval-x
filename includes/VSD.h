#ifndef VSD_H
#define VSD_H

#include <vector>
#include <string>

namespace VSD {
    // 示例类
    class VectorStringData {
    public:
        VectorStringData() = default;
        
        // 添加字符串到向量
        void addString(const std::string& str) {
            data.push_back(str);
        }
        
        // 获取所有字符串
        const std::vector<std::string>& getData() const {
            return data;
        }
        
        // 清空数据
        void clear() {
            data.clear();
        }
        
        // 新增：排序并连接所有字符串
        std::string sortAndJoin();
        
        // 新增：查找最长的字符串
        std::string findLongestString();
        
    private:
        std::vector<std::string> data;
    };
    
    // 示例函数
    inline std::string processString(const std::string& input) {
        return "VSD_" + input;
    }
}

#endif // VSD_H 