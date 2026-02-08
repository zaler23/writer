# 错误码枚举（统一 ErrorResponse）

所有 API 错误响应使用 `ErrorResponse` Schema（docs/spec/06-schemas.md）。

## 通用错误（E0xx）
| Code | HTTP | 含义 | 可重试 |
|---|---:|---|---|
| E001_NOT_FOUND | 404 | 资源不存在 | 否 |
| E002_VALIDATION | 422 | 请求校验失败 | 否（修改后可重试） |
| E003_INTERNAL | 500 | 内部错误 | 是 |

## 幂等与并发（E1xx）
| Code | HTTP | 含义 | 可重试 |
|---|---:|---|---|
| E101_IDEMPOTENCY_CONFLICT | 409 | 相同 key 不同 payload(hash) | 否 |
| E102_VERSION_CONFLICT | 409 | 乐观锁失败（expected_lock_version 不匹配） | 是（刷新后） |
| E103_WRITE_BUSY | 503 | 写锁繁忙（busy/timeout） | 是（retry_after_seconds） |
| E104_PROCESSING | 202 | 幂等请求处理中（lease 未过期） | 是（稍后） |

## 业务规则（E2xx）
| Code | HTTP | 含义 | 可重试 |
|---|---:|---|---|
| E201_ENTITY_AMBIGUOUS | 409 | 消歧需人审 | 否 |
| E202_BUDGET_EXCEEDED | 429 | 预算超限 | 否（调整预算） |
| E203_CHECKLIST_INCOMPLETE | 400 | onboarding 未完成 | 否 |
| E204_CYCLE_DETECTED | 422 | 时间线存在环（hard） | 否 |
| E205_ROLLBACK_DEPENDENTS | 409 | 回滚存在下游依赖冲突 | 否（需 force） |
| E206_RUN_NOT_PAUSABLE | 409 | 当前状态不允许暂停/恢复 | 否 |
| E207_SCHEMA_INVALID | 422 | 配置 JSON Schema 校验失败 | 否 |
| E208_FINALIZE_BLOCKED | 409 | validate 阻断 finalize | 否 |
| E209_REDIRECT_CYCLE | 422 | redirect 设置导致环 | 否 |
| E210_REDIRECT_SELF | 422 | redirect 不能指向自身 | 否 |
| E211_MERGE_CONFLICT | 409 | merge 操作存在冲突 | 否（需人工解决） |
| E212_DRAFT_NOT_FOUND | 404 | draft 记录不存在 | 否 |
| E213_ALREADY_FINALIZED | 409 | 章节已 finalize，不可重复操作 | 否 |

## 认证与权限（E3xx）
| Code | HTTP | 含义 | 可重试 |
|---|---:|---|---|
| E301_UNAUTHORIZED | 401 | 未认证 | 否（需认证） |
| E302_FORBIDDEN | 403 | 无权限访问资源 | 否 |
| E303_PROJECT_SCOPE_VIOLATION | 403 | 跨项目访问被拒绝 | 否 |

## LLM 调用（E4xx）
| Code | HTTP | 含义 | 可重试 |
|---|---:|---|---|
| E401_LLM_TIMEOUT | 504 | LLM 调用超时 | 是 |
| E402_LLM_RATE_LIMIT | 429 | LLM 速率限制 | 是（retry_after_seconds） |
| E403_LLM_INVALID_RESPONSE | 502 | LLM 返回无效响应 | 是 |
| E404_LLM_QUOTA_EXCEEDED | 429 | LLM 配额耗尽 | 否（需充值/等待） |
