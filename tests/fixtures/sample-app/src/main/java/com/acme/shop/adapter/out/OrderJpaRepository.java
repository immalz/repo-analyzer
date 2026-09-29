package com.acme.shop.adapter.out;

import jakarta.persistence.EntityManager;
import org.springframework.data.jpa.repository.Query;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.cache.annotation.Cacheable;
import com.azure.identity.DefaultAzureCredentialBuilder;
import javax.crypto.Cipher;
import java.security.MessageDigest;
import java.io.FileOutputStream;

@Repository
public abstract class OrderJpaRepository implements com.acme.shop.application.port.OrderRepository {

    private final String apiToken = "tok_live_123";

    @Query(value = "SELECT TOP 10 * FROM orders WITH (NOLOCK)", nativeQuery = true)
    public abstract java.util.List<Object> top();

    @Cacheable("orders")
    @KafkaListener(topics = "orders-created", groupId = "shop")
    public void onEvent(String payload) throws Exception {
        String url = "https://acmestore.blob.core.windows.net/orders";
        String sql = "SELECT * FROM orders WHERE id = ?";
        String dbHost = System.getenv("DB_HOST");
        String region = System.getProperty("app.region");
        Cipher c = Cipher.getInstance("DES/ECB/PKCS5Padding");
        MessageDigest md = MessageDigest.getInstance("MD5");
        new FileOutputStream("/var/data/orders.csv");
        Runtime.getRuntime().exec("sh -c cleanup.sh");
        System.loadLibrary("legacycrypto");
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {}));
        new DefaultAzureCredentialBuilder().build();
    }

    private native int nativeChecksum(byte[] data);
}
