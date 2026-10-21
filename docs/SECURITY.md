# AitMate — Security Architecture & Policy Specification

## 1. Core Security Tenets

1. **Useful Autonomy Under Human Control:** The agent assists with task planning and execution, but consequential side effects always require explicit human authorization.
2. **Zero Unrestricted Shell:** Under no circumstances does the LLM receive arbitrary or unmediated terminal/operating-system execution privileges.
3. **Server-Side Enforcement:** The frontend UI is treated as untrusted presentation; all security checks, permission validations, and tool execution boundaries are enforced strictly on the local backend server.
4. **Treat External Data as Hostile:** All web content, email messages, documents, and external API responses are classified as untrusted data and strictly prevented from acting as executable instructions.
5. **No Secret Infiltration:** Passwords, API tokens, session cookies, and private credentials are never written to unencrypted databases, logs, or shared model contexts.

---

## 2. Central Permission Engine

The **Central Permission Engine** (`backend/app/core/policy.py`) is the single gatekeeper through which every tool request must pass.

### 2.1 Tool Classification & Risk Levels

| Risk Level | Policy Rule | Examples | Approval Required? |
| :--- | :--- | :--- | :--- |
| **LOW** | Safe read-only inspection within AitMate's own boundary or user-provided text. | Inspect local task history, read application health, summarize text provided in chat. | **No** (Auto-permitted) |
| **MEDIUM** | Scoped local reading or drafting with no external mutation. | Read explicitly authorized local file, generate draft email, navigate to allowlisted public URL. | **Conditional** (Domain/Folder check) |
| **HIGH** | Outward mutation, message transmission, file writing/deletion, or account actions. | Send email, submit web form, overwrite local file, execute allowlisted CLI template. | **Yes** (Strict Human Approval) |

### 2.2 Approval Gate Invariants
- **Exact Action Display:** Approvals must explicitly state:
  1. The exact tool name.
  2. The target (URL, email recipient, file path).
  3. The exact payload (message text, parameter diff).
  4. The justification/reason and risk level.
- **No Approval Laundering:** Approval granted for Action A on Target X does not authorize Action A on Target Y, nor Action B on Target X.
- **Expiration:** Approval requests automatically expire after 10 minutes if not acted upon.
- **Denial Finality:** A rejected approval immediately transitions the task step to `rejected` and aborts further execution; the system will not silently retry the action.

---

## 3. Defense Against Prompt Injection

External content (webpages visited by Playwright, emails fetched from servers, files parsed by tools) frequently contains indirect prompt injections designed to hijack the agent.

### Mitigations:
1. **Instruction vs. Data Segregation:** External text is passed to model prompts in strictly delineated XML/JSON data containers (e.g., `<untrusted_content>...</untrusted_content>`).
2. **Model Cannot Self-Authorize:** Tool invocation does not depend on LLM text output alone. The Orchestrator validates the requested tool against the hardcoded registry and server-side policy rules before any invocation.
3. **No Dynamic Code Evaluation:** The agent does not execute `eval()`, `exec()`, or pass untrusted input into shell strings.

---

## 4. Local API Security

The FastAPI backend runs on the user's desktop, presenting a potential local attack surface from malicious local processes or browser tabs.

### Controls:
- **Loopback Binding:** Listens exclusively on `127.0.0.1` (never `0.0.0.0`).
- **Session Authentication:** Upon initialization, the backend generates an ephemeral cryptographic token (32-byte hex). All API requests from the frontend must present this token via an `Authorization: Bearer <token>` header.
- **Strict CORS:** CORS is locked to `http://localhost:*` and the Tauri origin (`tauri://localhost`).
- **Body & Size Limits:** Request bodies are constrained by Pydantic schemas with strict size limits to prevent Denial of Service.

---

## 5. Credential & Privacy Protection

- **No Plaintext Secrets in Database:** Application SQLite database stores task state and audit logs. No passwords or API keys are stored in plaintext.
- **Credential Storage:** When external AI providers (OpenAI, Anthropic) or GitLab tokens are configured, they are read from environment variables or stored using the Windows Credential Manager.
- **Secret Redaction in Audit Logs:** The audit logger runs all log payloads through a regex redactor that masks API keys (`sk-...`), Bearer tokens, passwords, and authorization headers before writing to `aitmate_audit.log`.

---

## 6. Emergency & Circuit-Breaker Controls

1. **Immediate Task Cancellation:** The user can click "Cancel Task" at any point. Active asyncio tasks are cancelled cleanly, and browser automation sessions are terminated immediately.
2. **Master Automation Pause:** A global toggle in Settings pauses all background operations and tool executions.
3. **Browser Automation Kill-Switch:** Disables Playwright browser launching globally.
