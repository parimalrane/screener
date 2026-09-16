# System Architecture Specification: Event-Driven CI/CD Pipeline

## 1. Executive Summary
This document outlines the architectural refactoring of the ASTA Screener automation environment. The system was transitioned from a passive, native cron-based execution model to an **Event-Driven Architecture (EDA)** leveraging external webhooks, RESTful API communication, and CI/CD runner containerization via GitHub Actions.

---

## 2. CI/CD Runner Allocation & The Context of Refactoring

### 2.1 The Native Cron Limitation
GitHub Actions supports time-based execution via the `on: schedule` block (POSIX cron syntax). However, because GitHub utilizes a shared runner pool for free-tier and standard operations, cron tasks are not guaranteed to execute instantaneously. They are added to a global queue. During peak global loads, workflow execution can experience severe latency (measured in hours). 

### 2.2 Event-Driven Architecture (EDA)
To achieve sub-minute execution precision necessary for quantitative financial algorithms, the pipeline was transitioned to utilize the `on: repository_dispatch` webhook listener. By utilizing a dedicated external scheduling service (Cron-job.org) to ping the GitHub REST API securely, the workflow execution bypasses the passive scheduling backlog and is treated as a high-priority, on-demand API event.

---

## 3. Remote Procedure Call (RPC) via REST API

The implementation relies heavily on synchronous HTTP POST requests to the GitHub v3 API endpoint.

### 3.1 Endpoint Specification
*   **Base URL:** `https://api.github.com`
*   **Endpoint:** `/repos/{owner}/{repo}/dispatches`
*   **Method:** `POST`

### 3.2 Protocol Headers & Content Negotiation
To successfully interface with the API, the following headers are strictly required:

1.  `Accept: application/vnd.github.v3+json`
    *   *Purpose:* Content negotiation. This explicitly defines the API version the client expects the server to respond with, ensuring backward compatibility.
2.  `Content-Type: application/json`
    *   *Purpose:* Informs the receiving web server that the payload body represents serialized JSON data.
3.  `Authorization: Bearer <PAT>`
    *   *Purpose:* Implements the RFC 6750 standard for HTTP Authentication. The `Bearer` keyword specifies the authentication scheme (OAuth 2.0 access token usage), informing the GitHub firewall how to parse the subsequent token string.

### 3.3 Payload Structure
The HTTP request body requires a stringified JSON payload:
```json
{"event_type": "trigger-main-screener"}
```
The `event_type` parameter is a critical bridging mechanism. When the GitHub API receives this packet, it parses the string and broadcasts it internally across the repository. The `.yml` files configured with `types: [trigger-main-screener]` capture the broadcast and boot their respective runner containers.

---

## 4. Authentication & Security Model

### 4.1 Personal Access Tokens (PAT)
Authentication is handled via a **Classic Personal Access Token**. Because the REST endpoint invokes scripts affecting repository state, the token requires the master `repo` scope. 

### 4.2 Security Vulnerabilities
If a PAT is exposed in plaintext (e.g., in a public chat, script, or log file), GitHub's native "Secret Scanning" engine will automatically detect the leak and instantly revoke the token, returning `HTTP 401 Unauthorized` on all subsequent pipeline triggers. Best practice dictates injecting these tokens as encrypted secrets (e.g., `${{ secrets.GMAIL_PASSWORD }}`) within the repository UI rather than hardcoding them into client-side apps.

---

## 5. Working Tree Conflict Resolution 

### 5.1 The Concurrency Problem
During execution, the Python logic dynamically creates and modifies `.csv` files inside the runner's ephemeral container. Due to potential upstream modifications to `main` occurring while the container is executing, invoking a standard `git pull --rebase` will throw a `128 modify/delete` tree conflict, crashing the CI/CD pipeline.

### 5.2 The Git Implementation
To achieve absolute idempotency and fault tolerance during the artifact upload cycle, the pipeline executes the following sequence:

```bash
git stash --include-untracked
git pull origin main --rebase
git stash pop || true
git add .
git commit -m "Automated Pipeline Update [skip ci]" || echo "No changes"
git push origin main
```

**Mechanics:**
1.  `stash`: Isolates the locally generated output files securely into the Git stash stack.
2.  `pull --rebase`: Realigns the runner's local HEAD with the remote `main` branch cleanly.
3.  `stash pop`: Applies the generated binaries back into the working directory on top of the newly synced tree.
4.  `[skip ci]`: Appended to the commit message to prevent recursive runner-looping (where a push action triggers another push action infinitely).
