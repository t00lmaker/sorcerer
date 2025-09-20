import java.util.Optional;
import java.util.stream.Stream;

public class MultipleChanges {
    public static void main(String[] args) {
        Optional<String> value = Optional.ofNullable(null);
        value.ifPresentOrElse(
            v -> System.out.println("Value: " + v),
            () -> System.out.println("No value present")
        );

        Stream.of(1, 2, 3).forEach(System.out::println);
    }
}