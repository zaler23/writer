# 06 — JSON Schemas（v1.4）

> 所有 schema 建议另存为 `schemas/*.json`；此处为了“单文件可读/可复制”，以 Markdown code block 形式提供全量定义。


## ChapterPlan → `chapter_plan.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ChapterPlan",
  "type": "object",
  "required": [
    "schema_version",
    "chapter_id",
    "segments",
    "goals",
    "threads"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "1.2"
    },
    "chapter_id": {
      "type": "string"
    },
    "volume_no": {
      "type": "integer",
      "minimum": 1
    },
    "chapter_no": {
      "type": "integer",
      "minimum": 1
    },
    "working_title": {
      "type": "string"
    },
    "logline": {
      "type": "string"
    },
    "segments": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/ChapterSegmentPlan"
      }
    },
    "goals": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "minItems": 1
    },
    "threads": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/ThreadBeat"
      },
      "minItems": 1
    },
    "retrieval_query": {
      "$ref": "#/$defs/RetrievalQuery"
    },
    "constraints": {
      "$ref": "#/$defs/PlanConstraints"
    },
    "notes": {
      "type": "string"
    }
  },
  "$defs": {
    "ChapterSegmentPlan": {
      "type": "object",
      "required": [
        "segment_no",
        "segment_type",
        "beats"
      ],
      "properties": {
        "segment_no": {
          "type": "integer",
          "minimum": 1
        },
        "title": {
          "type": "string"
        },
        "pov_node_id": {
          "type": "string"
        },
        "segment_type": {
          "type": "string",
          "enum": [
            "action",
            "emotion",
            "reveal",
            "setup",
            "payoff",
            "transition",
            "dialogue",
            "other"
          ]
        },
        "desired_length_tokens": {
          "type": "integer",
          "minimum": 100
        },
        "beats": {
          "type": "array",
          "minItems": 1,
          "items": {
            "$ref": "#/$defs/Beat"
          }
        }
      }
    },
    "Beat": {
      "type": "object",
      "required": [
        "beat_no",
        "intent",
        "details"
      ],
      "properties": {
        "beat_no": {
          "type": "integer",
          "minimum": 1
        },
        "intent": {
          "type": "string"
        },
        "details": {
          "type": "string"
        },
        "entities": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "expected_state_changes": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "ThreadBeat": {
      "type": "object",
      "required": [
        "thread_node_id",
        "action"
      ],
      "properties": {
        "thread_node_id": {
          "type": "string"
        },
        "action": {
          "type": "string",
          "enum": [
            "advance",
            "foreshadow",
            "payoff",
            "park",
            "close",
            "open"
          ]
        },
        "description": {
          "type": "string"
        },
        "visibility": {
          "type": "string",
          "enum": [
            "explicit",
            "implicit"
          ]
        },
        "priority": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        }
      }
    },
    "RetrievalQuery": {
      "type": "object",
      "properties": {
        "keywords": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "focus_entities": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "top_k_vector": {
          "type": "integer",
          "minimum": 1,
          "maximum": 50
        },
        "top_k_graph": {
          "type": "integer",
          "minimum": 1,
          "maximum": 50
        },
        "segment_type": {
          "type": "string"
        }
      },
      "additionalProperties": false
    },
    "PlanConstraints": {
      "type": "object",
      "properties": {
        "must_include": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "must_avoid": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "pov_rotation": {
          "type": "string"
        },
        "tone": {
          "type": "string"
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```


## SwarmProfile → `swarm_profile.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SwarmProfile",
  "type": "object",
  "required": [
    "schema_version",
    "profile_version",
    "steps",
    "budget"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "1.2"
    },
    "profile_version": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "default_model": {
      "type": "string"
    },
    "budget": {
      "$ref": "#/$defs/Budget"
    },
    "concurrency": {
      "$ref": "#/$defs/ConcurrencyBudget"
    },
    "steps": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/StepSpec"
      }
    }
  },
  "$defs": {
    "Budget": {
      "type": "object",
      "properties": {
        "max_tokens_total": {
          "type": "integer",
          "minimum": 1
        },
        "max_cost_total": {
          "type": "number",
          "minimum": 0
        },
        "max_revision_rounds": {
          "type": "integer",
          "minimum": 0,
          "maximum": 10
        },
        "step_timeout_seconds": {
          "type": "integer",
          "minimum": 1
        },
        "budget_alert_threshold": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        }
      },
      "additionalProperties": true
    },
    "ConcurrencyBudget": {
      "type": "object",
      "properties": {
        "max_inflight_calls": {
          "type": "integer",
          "minimum": 1
        },
        "rate_limit_bucket": {
          "type": "string"
        },
        "retry_budget": {
          "type": "integer",
          "minimum": 0
        }
      },
      "additionalProperties": true
    },
    "StepSpec": {
      "type": "object",
      "required": [
        "step_type",
        "role"
      ],
      "properties": {
        "step_type": {
          "type": "string",
          "enum": [
            "plan",
            "retrieve",
            "draft",
            "review",
            "revise",
            "validate",
            "finalize_preview",
            "finalize_apply"
          ]
        },
        "role": {
          "type": "string",
          "enum": [
            "system",
            "planner",
            "writer",
            "critic",
            "editor",
            "validator",
            "finalizer"
          ]
        },
        "model": {
          "type": "string"
        },
        "requires_approval": {
          "type": "boolean"
        },
        "draft_n": {
          "type": "integer",
          "minimum": 1,
          "maximum": 3
        },
        "review_n": {
          "type": "integer",
          "minimum": 1,
          "maximum": 3
        },
        "select_strategy": {
          "type": "string",
          "enum": [
            "min_issues",
            "weighted_score",
            "human_only"
          ]
        },
        "input_template": {
          "type": "string"
        },
        "output_schema": {
          "type": "string"
        },
        "budget": {
          "$ref": "#/$defs/StepBudget"
        }
      },
      "additionalProperties": true
    },
    "StepBudget": {
      "type": "object",
      "properties": {
        "max_tokens": {
          "type": "integer",
          "minimum": 1
        },
        "max_cost": {
          "type": "number",
          "minimum": 0
        },
        "timeout_seconds": {
          "type": "integer",
          "minimum": 1
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```


## TraversalProfile → `traversal_profile.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TraversalProfile",
  "type": "object",
  "required": [
    "schema_version",
    "profile_version",
    "weights"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "1.2"
    },
    "profile_version": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "weights": {
      "$ref": "#/$defs/TraversalWeights"
    },
    "cold_start": {
      "$ref": "#/$defs/ColdStart"
    },
    "rules": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "$defs": {
    "TraversalWeights": {
      "type": "object",
      "properties": {
        "thread_advance": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "foreshadow": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "payoff": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "state_consistency": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "novelty": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        }
      },
      "additionalProperties": true
    },
    "ColdStart": {
      "type": "object",
      "properties": {
        "min_threads": {
          "type": "integer",
          "minimum": 0
        },
        "template": {
          "type": "string"
        },
        "seed_entities": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```


## StyleGuide → `style_guide.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "StyleGuide",
  "type": "object",
  "required": [
    "schema_version",
    "guide_version",
    "style_rules"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "1.2"
    },
    "guide_version": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "style_rules": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string"
      }
    },
    "do_not": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "exemplars": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "voice": {
      "type": "string"
    },
    "pacing": {
      "type": "string"
    }
  },
  "additionalProperties": true
}
```


## EntityResolveRequest → `entity_resolve_request.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EntityResolveRequest",
  "type": "object",
  "required": [
    "project_id",
    "inputs"
  ],
  "properties": {
    "project_id": {
      "type": "string"
    },
    "chapter_id": {
      "type": "string"
    },
    "inputs": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/ResolveInput"
      }
    },
    "thresholds": {
      "$ref": "#/$defs/Thresholds"
    }
  },
  "$defs": {
    "ResolveInput": {
      "type": "object",
      "required": [
        "text",
        "kind"
      ],
      "properties": {
        "text": {
          "type": "string"
        },
        "kind": {
          "type": "string",
          "enum": [
            "node",
            "event",
            "location",
            "item",
            "faction",
            "thread",
            "other"
          ]
        },
        "context": {
          "type": "string"
        },
        "hint_node_type": {
          "type": "string"
        }
      },
      "additionalProperties": true
    },
    "Thresholds": {
      "type": "object",
      "properties": {
        "auto_accept": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "needs_review": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```


## EntityResolveResponse → `entity_resolve_response.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EntityResolveResponse",
  "type": "object",
  "required": [
    "run_id",
    "results"
  ],
  "properties": {
    "run_id": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/ResolveResult"
      }
    }
  },
  "$defs": {
    "ResolveResult": {
      "type": "object",
      "required": [
        "input_text",
        "decision",
        "candidates"
      ],
      "properties": {
        "input_text": {
          "type": "string"
        },
        "decision": {
          "type": "string",
          "enum": [
            "matched",
            "ambiguous",
            "new",
            "rejected"
          ]
        },
        "chosen_node_id": {
          "type": "string"
        },
        "score": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "score_breakdown": {
          "type": "object"
        },
        "candidates": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/Candidate"
          }
        }
      },
      "additionalProperties": true
    },
    "Candidate": {
      "type": "object",
      "required": [
        "node_id",
        "score"
      ],
      "properties": {
        "node_id": {
          "type": "string"
        },
        "score": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "name_score": {
          "type": "number"
        },
        "context_score": {
          "type": "number"
        },
        "embedding_score": {
          "type": "number"
        },
        "evidence": {
          "type": "object"
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```


## GraphSnapshotResponse → `graph_snapshot_response.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "GraphSnapshotResponse",
  "type": "object",
  "required": [
    "project_id",
    "as_of_chapter_id",
    "nodes",
    "edges",
    "state_assertions",
    "conflicts"
  ],
  "properties": {
    "project_id": {
      "type": "string"
    },
    "as_of_chapter_id": {
      "type": "string"
    },
    "nodes": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/SnapshotNode"
      }
    },
    "edges": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/SnapshotEdge"
      }
    },
    "state_assertions": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/SnapshotAssertion"
      }
    },
    "conflicts": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/Conflict"
      }
    }
  },
  "$defs": {
    "SnapshotNode": {
      "type": "object",
      "required": [
        "node_id",
        "node_type",
        "title",
        "canonical_id"
      ],
      "properties": {
        "node_id": {
          "type": "string"
        },
        "canonical_id": {
          "type": "string"
        },
        "node_type": {
          "type": "string"
        },
        "title": {
          "type": "string"
        },
        "summary": {
          "type": "string"
        },
        "tags": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "attrs": {
          "type": "object"
        }
      },
      "additionalProperties": true
    },
    "SnapshotEdge": {
      "type": "object",
      "required": [
        "edge_id",
        "edge_type",
        "src_canonical_id",
        "dst_canonical_id"
      ],
      "properties": {
        "edge_id": {
          "type": "string"
        },
        "edge_type": {
          "type": "string"
        },
        "src_canonical_id": {
          "type": "string"
        },
        "dst_canonical_id": {
          "type": "string"
        },
        "weight": {
          "type": "number"
        },
        "attrs": {
          "type": "object"
        }
      },
      "additionalProperties": true
    },
    "SnapshotAssertion": {
      "type": "object",
      "required": [
        "assertion_id",
        "subject_canonical_id",
        "predicate",
        "object",
        "truth_mode",
        "valid_from_chapter_id"
      ],
      "properties": {
        "assertion_id": {
          "type": "string"
        },
        "subject_canonical_id": {
          "type": "string"
        },
        "predicate": {
          "type": "string"
        },
        "object": {
          "type": "object"
        },
        "truth_mode": {
          "type": "string",
          "enum": [
            "asserted",
            "rumored",
            "mislead",
            "retconned"
          ],
          "default": "asserted",
          "description": "断言真值模式：asserted=确定事实, rumored=传闻, mislead=误导性信息, retconned=追溯修正"
        },
        "anchor_mode": {
          "type": "string",
          "enum": [
            "chapter_based",
            "event_based"
          ],
          "default": "chapter_based",
          "description": "有效期锚定方式：chapter_based（确定性）/ event_based（增强）"
        },
        "valid_from_chapter_id": {
          "type": "string"
        },
        "valid_to_chapter_id": {
          "type": "string"
        }
      },
      "additionalProperties": true
    },
    "Conflict": {
      "type": "object",
      "required": [
        "subject_canonical_id",
        "predicate",
        "values"
      ],
      "properties": {
        "subject_canonical_id": {
          "type": "string"
        },
        "predicate": {
          "type": "string"
        },
        "values": {
          "type": "array",
          "items": {
            "type": "object"
          }
        },
        "severity": {
          "type": "string",
          "enum": [
            "soft",
            "hard"
          ]
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```


## ChatQueryRequest → `chat_query_request.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ChatQueryRequest",
  "type": "object",
  "required": [
    "project_id",
    "question"
  ],
  "properties": {
    "project_id": {
      "type": "string"
    },
    "session_id": {
      "type": "string"
    },
    "question": {
      "type": "string"
    },
    "at_chapter_id": {
      "type": "string",
      "description": "按章节 ID（ULID）限制检索视角"
    },
    "at_chapter_no": {
      "type": "integer",
      "minimum": 1,
      "description": "兼容字段：按 chapter_no 限制检索视角；与 at_chapter_id 二选一"
    },
    "history_turns": {
      "type": "integer",
      "minimum": 0,
      "maximum": 20
    },
    "mode": {
      "type": "string",
      "enum": [
        "quick",
        "precise"
      ],
      "default": "quick"
    },
    "include_sources": {
      "type": "boolean",
      "default": true
    }
  },
  "additionalProperties": true
}
```


## ChatQueryResponse → `chat_query_response.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ChatQueryResponse",
  "type": "object",
  "required": [
    "answer",
    "request_id"
  ],
  "properties": {
    "answer": {
      "type": "string"
    },
    "request_id": {
      "type": "string"
    },
    "sources": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/SourceRef"
      }
    }
  },
  "$defs": {
    "SourceRef": {
      "type": "object",
      "required": [
        "kind",
        "id"
      ],
      "properties": {
        "kind": {
          "type": "string",
          "enum": [
            "chapter",
            "chunk",
            "node",
            "edge",
            "assertion",
            "event"
          ]
        },
        "id": {
          "type": "string"
        },
        "note": {
          "type": "string"
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```


## TimelineValidateRequest → `timeline_validate_request.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TimelineValidateRequest",
  "type": "object",
  "required": [
    "project_id"
  ],
  "properties": {
    "project_id": {
      "type": "string"
    },
    "chapter_id": {
      "type": "string"
    },
    "event_ids": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "include_soft_warnings": {
      "type": "boolean",
      "default": true
    }
  },
  "additionalProperties": true
}
```


## TimelineValidateResponse → `timeline_validate_response.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TimelineValidateResponse",
  "type": "object",
  "required": [
    "project_id",
    "is_blocking",
    "hard_conflicts",
    "soft_warnings",
    "cycles"
  ],
  "properties": {
    "project_id": {
      "type": "string"
    },
    "is_blocking": {
      "type": "boolean"
    },
    "cycles": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/Cycle"
      }
    },
    "hard_conflicts": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/Conflict"
      }
    },
    "soft_warnings": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/Conflict"
      }
    }
  },
  "$defs": {
    "Cycle": {
      "type": "object",
      "required": [
        "event_ids",
        "relations"
      ],
      "properties": {
        "event_ids": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "relations": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "additionalProperties": true
    },
    "Conflict": {
      "type": "object",
      "required": [
        "kind",
        "message"
      ],
      "properties": {
        "kind": {
          "type": "string",
          "enum": [
            "cycle",
            "order",
            "interval",
            "missing_time",
            "other"
          ]
        },
        "message": {
          "type": "string"
        },
        "details": {
          "type": "object"
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```


## ErrorResponse → `error_response.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ErrorResponse",
  "type": "object",
  "required": [
    "error_code",
    "message",
    "request_id"
  ],
  "properties": {
    "error_code": {
      "type": "string",
      "description": "机器可读错误码"
    },
    "message": {
      "type": "string"
    },
    "request_id": {
      "type": "string"
    },
    "details": {
      "type": "object"
    },
    "retry_after_seconds": {
      "type": "integer"
    }
  },
  "additionalProperties": true
}
```


## WritebackPlan → `writeback_plan.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "WritebackPlan",
  "title": "WritebackPlan",
  "description": "v1.4: finalize.apply 的写回计划，包含所有待执行的原子操作",
  "type": "object",
  "required": ["version", "chapter_id", "writeback_plan_hash", "ops"],
  "properties": {
    "version": {
      "type": "string",
      "enum": ["1.4"]
    },
    "chapter_id": {
      "type": "string",
      "description": "目标章节 ID"
    },
    "writeback_plan_hash": {
      "type": "string",
      "description": "计划内容的哈希值，用于幂等检查"
    },
    "plan_hash": {
      "type": "string",
      "description": "兼容字段（deprecated）：等价于 writeback_plan_hash"
    },
    "base_lock_version": {
      "type": "integer",
      "minimum": 0,
      "description": "基于的章节乐观锁版本"
    },
    "mutation_set": {
      "type": "object",
      "required": ["kind"],
      "properties": {
        "kind": {
          "type": "string",
          "enum": ["chapter", "global"],
          "description": "mutation 作用域类型"
        },
        "chapter_id": {
          "type": ["string", "null"],
          "description": "若 kind=chapter，则为目标章节"
        }
      }
    },
    "ops": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/WriteOp" },
      "description": "按依赖顺序排列的写操作列表"
    },
    "generated_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "$defs": {
    "WriteOp": {
      "type": "object",
      "required": ["op_id", "object_type", "action"],
      "properties": {
        "op_id": {
          "type": "string",
          "description": "操作的全局唯一 ID（对应 mutations.op_id）"
        },
        "object_type": {
          "type": "string",
          "description": "目标对象类型（如 graph_node, state_assertion 等）"
        },
        "object_id": {
          "type": ["string", "null"],
          "description": "目标对象 ID（upsert 时可为 null，由系统生成）"
        },
        "action": {
          "type": "string",
          "enum": ["upsert", "update", "delete", "merge", "redirect", "restore"],
          "description": "操作类型"
        },
        "before_json": {
          "type": ["object", "null"],
          "description": "操作前的对象快照（用于回滚）"
        },
        "after_json": {
          "type": ["object", "null"],
          "description": "操作后的期望对象状态"
        },
        "patch_json": {
          "type": ["object", "null"],
          "description": "增量补丁（仅 update 时使用）"
        },
        "depends_on_op_ids": {
          "type": "array",
          "items": { "type": "string" },
          "default": [],
          "description": "依赖的前置操作 ID 列表"
        }
      }
    }
  },
  "additionalProperties": true
}
```


## ConflictReport → `conflict_report.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "ConflictReport",
  "title": "ConflictReport",
  "description": "v1.4: 回滚冲突检测报告",
  "type": "object",
  "required": ["version", "mutation_set_id", "status", "conflicts"],
  "properties": {
    "version": {
      "type": "string",
      "enum": ["1.4"]
    },
    "mutation_set_id": {
      "type": "string",
      "description": "待回滚的 mutation_set ID"
    },
    "status": {
      "type": "string",
      "enum": ["blocked", "forceable", "resolved"],
      "description": "冲突状态：blocked=无法回滚，forceable=可强制，resolved=已解决"
    },
    "dependents": {
      "type": "array",
      "items": { "$ref": "#/$defs/Ref" },
      "default": [],
      "description": "依赖此 mutation_set 的后续对象列表"
    },
    "conflicts": {
      "type": "array",
      "items": { "$ref": "#/$defs/ConflictItem" },
      "description": "冲突项列表"
    },
    "summary": {
      "type": "object",
      "properties": {
        "dependent_count": {
          "type": "integer",
          "minimum": 0
        },
        "conflict_count": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "generated_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "$defs": {
    "Ref": {
      "type": "object",
      "required": ["object_type", "object_id"],
      "properties": {
        "object_type": {
          "type": "string"
        },
        "object_id": {
          "type": "string"
        },
        "chapter_id": {
          "type": ["string", "null"],
          "description": "若对象属于特定章节"
        },
        "reason": {
          "type": ["string", "null"],
          "description": "依赖原因说明"
        }
      }
    },
    "ConflictItem": {
      "type": "object",
      "required": ["object_type", "object_id", "reason"],
      "properties": {
        "object_type": {
          "type": "string"
        },
        "object_id": {
          "type": "string"
        },
        "reason": {
          "type": "string",
          "description": "冲突原因"
        },
        "blocking_object": {
          "$ref": "#/$defs/Ref",
          "description": "导致阻塞的对象"
        },
        "suggested_action": {
          "type": ["string", "null"],
          "description": "建议的解决方案"
        }
      }
    }
  },
  "additionalProperties": true
}
```
