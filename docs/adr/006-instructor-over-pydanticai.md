# ADR-006 Instructor as structured output engine

## 状态
已采纳（v1.0）

## 背景
需要选择 LLM 结构化输出方案。考虑因素：Pydantic 兼容性、自动重试、多模型支持。

## 决策
LLM 调用统一 LiteLLM；结构化输出优先 Instructor（Pydantic v2 原生 + 自动重试）。

## 备选方案
1. **PydanticAI**：Anthropic 官方，但生态较新
2. **Outlines**：语法约束强，但复杂度高
3. **Guidance**：微软出品，但学习曲线陡
4. **手动 JSON 解析**：最大控制力，但容易出错

## 拒绝原因
- PydanticAI：生态较新，稳定性待验证，保留为未来候选
- Outlines：复杂度高，不适合快速迭代
- Guidance：学习曲线陡，社区支持有限
- 手动解析：容易出错，缺少自动重试

## 后果
- 优：结构化输出稳定、Pydantic v2 原生支持、自动重试
- 负：依赖 Instructor 库更新

## 实现
- LLM 调用：LiteLLM（多模型统一接口）
- 结构化输出：Instructor（Pydantic v2 + 自动重试）
- Agent 框架：PydanticAI 保留为未来候选
