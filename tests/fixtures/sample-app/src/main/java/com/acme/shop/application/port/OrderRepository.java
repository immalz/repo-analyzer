package com.acme.shop.application.port;

import com.acme.shop.domain.Order;

public interface OrderRepository {
    Order findById(String id);
}
