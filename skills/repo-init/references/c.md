# C

**Файлы:** `CMakeLists.txt`, `src/main.c`. Для прошивок сборка зависит от тулчейна МК: спроси, какой тулчейн, и не угадывай; hello-world для МК не создавай (нужна плата и периферия), только структуру.

**`CMakeLists.txt`** (с комментариями): `cmake_minimum_required(VERSION 3.16)`, `project(<имя> LANGUAGES C)`, `set(CMAKE_C_STANDARD 11)`, `add_executable(<имя> src/main.c)`. Стандарт языка (11, 17) и версию CMake спроси у пользователя.

**`src/main.c`:**
```c
/* Подключаем заголовок стандартного ввода-вывода (printf). */
#include <stdio.h>

/* Точка входа программы. */
int main(void) {
    /* printf печатает отформатированную строку; \n — перевод строки. */
    printf("Hello, world!\n");
    return 0; /* 0 означает успешное завершение */
}
```

**`.gitignore`:** `build/`, `*.o` (объектные файлы), `*.exe`.

**Проверка:** `cmake -S . -B build && cmake --build build`, затем запуск файла из `build/`.
