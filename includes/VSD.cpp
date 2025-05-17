#include "VSD.h"
#include <algorithm>

namespace VSD {
    // 非内联函数实现
    std::string VectorStringData::sortAndJoin() {
        std::vector<std::string> sorted = data;
        std::sort(sorted.begin(), sorted.end());
        
        std::string result;
        for (const auto& str : sorted) {
            if (!result.empty()) {
                result += ", ";
            }
            result += str;
        }
        return result;
    }
    
    // 另一个非内联函数
    std::string VectorStringData::findLongestString() {
        if (data.empty()) {
            return "";
        }
        return *std::max_element(data.begin(), data.end(),
            [](const std::string& a, const std::string& b) {
                return a.length() < b.length();
            });
    }
} 