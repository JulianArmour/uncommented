# Uncommented
Find all those pesky public APIs missing documentation.
The intent is to run this on header files.

## Supported checks
### C
- [x] C function declarations
- [x] C inline functions definitions
- [ ] C structs with function pointer members

### C++
- [x] C++ member functions (A.K.A Methods)
    - [x] public member declarations
    - [ ] protected member declarations
- [ ] C++ class declarations (https://www.cppreference.com/w/cpp/language/class.html)

### Preprocessor
- [x] Preprocessor macros
