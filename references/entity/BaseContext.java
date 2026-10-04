package com.company.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.time.OffsetDateTime;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class BaseContext {

    @JsonProperty("client_source")
    @NotNull
    private String clientSource;

    @JsonProperty("trace_id")
    @NotNull
    @Pattern(regexp = "^[a-f0-9]{32}$", message = "Trace ID must be a valid 32-character hex string")
    private String traceId;

    @JsonProperty("request_timestamp")
    @NotNull
    private OffsetDateTime requestTimestamp;

    @JsonProperty("environment_target")
    @NotNull
    private String environmentTarget;

    // Standard Getters and Setters
    public String getClientSource() { return clientSource; }
    public void setClientSource(String clientSource) { this.clientSource = clientSource; }
    public String getTraceId() { return traceId; }
    public void setTraceId(String traceId) { this.traceId = traceId; }
    public OffsetDateTime getRequestTimestamp() { return requestTimestamp; }
    public void setRequestTimestamp(OffsetDateTime requestTimestamp) { this.requestTimestamp = requestTimestamp; }
    public String getEnvironmentTarget() { return environmentTarget; }
    public void setEnvironmentTarget(String environmentTarget) { this.environmentTarget = environmentTarget; }
}
