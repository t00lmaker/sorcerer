import java.util.stream.Collectors;
import java.util.List;

public class SimpleMigration {
    public static void main(String[] args) {
        List<String> items = List.of("A", "B", "C");
        String result = items.stream().collect(Collectors.joining(", "));
        System.out.println(result);
    }
}