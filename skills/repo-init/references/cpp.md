# C++

**Файлы:** `CMakeLists.txt`, `src/main.cpp`.

**`CMakeLists.txt`** (с комментариями): `cmake_minimum_required(VERSION 3.16)`, `project(<имя> LANGUAGES CXX)`, `set(CMAKE_CXX_STANDARD 17)`, `set(CMAKE_CXX_STANDARD_REQUIRED ON)`, `add_executable(<имя> src/main.cpp)`. **Стандарт (17, 20, 23) и минимальную версию CMake спроси у пользователя:** они зависят от его компилятора и версии CMake.

**`src/main.cpp`:**
```cpp
// Подключаем заголовок с потоками ввода-вывода.
#include <iostream>

// Точка входа программы.
int main() {
    // std::cout — стандартный вывод; "\n" — перевод строки.
    std::cout << "Hello, world!\n";
    return 0;  // 0 означает успешное завершение
}
```

**`.gitignore`:** `build/` — каталог сборки CMake.

**Проверка:** `cmake -S . -B build && cmake --build build`, затем запуск файла из `build/`.
