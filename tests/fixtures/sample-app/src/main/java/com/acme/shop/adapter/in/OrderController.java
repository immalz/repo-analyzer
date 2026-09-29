package com.acme.shop.adapter.in;

import org.springframework.web.bind.annotation.*;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.scheduling.annotation.Scheduled;
import jakarta.servlet.http.HttpServletRequest;

@RestController
@RequestMapping("/api/v1")
public class OrderController {

    @GetMapping("/orders/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public String get(@PathVariable String id, @RequestHeader("X-Forwarded-For") String ip, HttpServletRequest req) {
        String key = req.getHeader("Ocp-Apim-Subscription-Key");
        String tp = req.getHeader("traceparent");
        return id;
    }

    @PostMapping(path = "/orders")
    public void create() { if (req().isUserInRole("OPERATOR")) { } }

    @Scheduled(cron = "0 0 * * * *")
    public void nightly() { }

    public static void main(String[] args) {
        System.exit(3);
    }

    private HttpServletRequest req() { return null; }
}
