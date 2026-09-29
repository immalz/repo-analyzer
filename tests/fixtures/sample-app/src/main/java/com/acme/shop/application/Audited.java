package com.acme.shop.application;

public @interface Audited {
    String value() default "";
}
