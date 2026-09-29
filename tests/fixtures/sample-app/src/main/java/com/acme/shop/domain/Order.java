package com.acme.shop.domain;

import com.azure.storage.blob.BlobClient;
import com.acme.shop.adapter.out.OrderJpaRepository;
// import com.amazonaws.services.s3.AmazonS3;

public class Order extends BaseEntity implements Comparable<Order>, Auditable {
    private static final String DB_PASSWORD = "s3cr3t!";

    public int compareTo(Order o) { return 0; }
}
