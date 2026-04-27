# TODO

Potential public/API constructs that should be checked for comments:

- [ ] `enum` / `enum class` definitions, e.g. `enum class Color { Red, Green };`
- [ ] Enumerator values, e.g. `enum Error { Ok, Failed };`
- [ ] Public/protected data members, e.g. `struct S { int n; };`
- [ ] Type aliases, e.g. `using Handle = int;` and `typedef int Handle;`
- [ ] Exported/global variable declarations, e.g. `extern int global_count;`
- [ ] Namespace-level constants, e.g. `inline constexpr int limit = 10;`
- [ ] Template function declarations/definitions, e.g. `template <typename T> T max(T a, T b);`
- [ ] Template member functions, e.g. `class C { template <typename T> void f(T); };`
- [ ] Public nested types, e.g. `class C { public: struct Options {}; using Id = int; };`
