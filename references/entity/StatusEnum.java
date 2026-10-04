package com.company.api.dto;

import com.fasterxml.jackson.annotation.JsonValue;

public enum StatusEnum {
    ACTIVE("active_status"),
    SUSPENDED("suspended_status"),
    PENDING_VERIFICATION("pending_verification"),
    TERMINATED("terminated_status");

    private final String value;

    StatusEnum(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }
}
