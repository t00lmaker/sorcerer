import java.util.Date;
import java.text.SimpleDateFormat;

public class ComplexMigration {
    public static void main(String[] args) {
        Date now = new Date();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        System.out.println("Current date: " + sdf.format(now));
    }
}