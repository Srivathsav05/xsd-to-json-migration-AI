package com.company.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

@JsonInclude(JsonInclude.Include.NON_EMPTY)
public class ServiceError {

    @JsonProperty("error_code")
    @NotNull
    @Size(min = 5, max = 12)
    private String errorCode;

    @JsonProperty("error_message")
    @NotNull
    private String errorMessage;

    @JsonProperty("error_severity")
    private String errorSeverity;

    // Standard Getters and Setters
    public String getErrorCode() { return errorCode; }
    public void setErrorCode(String errorCode) { this.errorCode = errorCode; }
    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
    public String getErrorSeverity() { return errorSeverity; }
    public void setErrorSeverity(String errorSeverity) { this.errorSeverity = errorSeverity; }
}
