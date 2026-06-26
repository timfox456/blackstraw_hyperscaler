---
name: model-armor-integration
description: Guides implementing input/output safety filters (Jailbreaks and PII redaction) inside Agent Runtime hooks.
---
# Model Armor Integration Skill

This skill documents how to integrate Model Armor safety shields into generative AI applications to scan inputs for jailbreaks and outputs for sensitive data leakage.

## Implementation Flow

1.  **Jailbreak Filter (Input Protection)**:
    Screen user input string against prompt injection signatures before executing chat turns:
    ```python
    jailbreak_patterns = [
        r"(?i)ignore\s+(?:all\s+)?previous\s+instructions",
        r"(?i)system\s+override",
    ]
    for pattern in jailbreak_patterns:
        if re.search(pattern, user_input):
            raise ValueError("Model Armor Verdict: BLOCKED (Prompt Injection Threat)")
    ```

2.  **PII Redaction (Output Protection)**:
    Screen model responses to prevent leaking credit cards or social security numbers:
    ```python
    pii_patterns = [
        r"\b(?:\d[ -]??){15,16}\b",  # Credit Cards
        r"\b\d{3}-\d{2}-\d{4}\b",     # SSN
    ]
    for pattern in pii_patterns:
        text = re.sub(pattern, "[REDACTED_PII]", text)
    ```

3.  **UI Error Propagation**:
    Handle safety exceptions raised in the chat API. Return HTTP 500/400 containing the error detail, and print a warning banner to the user interface:
    ```javascript
    } catch (err) {
        appendMessage('system', `⚠️ ${err.message}`);
    }
    ```
