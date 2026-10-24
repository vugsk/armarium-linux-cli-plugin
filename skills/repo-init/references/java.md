# Java

**Файлы:** `src/Main.java`. Файл сборки (Maven, Gradle) не создавай, пока пользователь не выбрал систему сборки: спроси.

**`src/Main.java`:**
```java
// Класс, имя которого совпадает с именем файла (Main.java).
public class Main {
    // Точка входа программы.
    public static void main(String[] args) {
        // System.out — стандартный вывод; println печатает строку с переводом строки.
        System.out.println("Hello, world!");
    }
}
```

**`.gitignore`:** `out/`, `*.class` (скомпилированные файлы), `target/` (Maven), `build/` (Gradle) — оставь только то, что соответствует выбранной системе сборки.

**Проверка без системы сборки:** `javac -d out src/Main.java`, затем `java -cp out Main`. Версию JDK уточни: возможности языка зависят от неё.
