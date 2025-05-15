#include<stdlib.h>
#include<algorithm>
#include<math.h>
#include<climits>
#include<cstring>
#include<iostream>

/*
Out of vector of strings, return the longest one. Return the first one in case of multiple
strings of the same length. Return None in case the input vector is empty.
>>> longest({})

>>> longest({"a", "b", "c"})
"a"
>>> longest({"a", "bb", "ccc"})
"ccc"
*/
#include<stdio.h>
#include<vector>
#include<string>
using namespace std;
string longest(vector<string> strings){
    if (strings.empty()) {
        return "None";
    }
    string longestString = strings[0];
    for (const string& str : strings) {
        if (str.length() > longestString.length()) {
            longestString = str;
        }
    }
    return longestString;
}
#undef NDEBUG
#include<assert.h>
int main(){
    assert (longest({}) == "");
    assert (longest({"x", "y", "z"}) == "x");
    assert (longest({"x", "yyy", "zzzz", "www", "kkkk", "abc"}) == "zzzz");
}
