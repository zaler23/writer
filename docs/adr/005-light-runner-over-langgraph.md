# ADR-005 Light runner first

## 状态
已采纳（v1.0）

## 背景
需要选择工作流编排方案。考虑因素：成本控制、死循环防护、可替换性。

## 决策
先实现显式状态机 + step registry 的轻 runner，保持 runs/run_steps 契约稳定；未来可替换 LangGraph。

## 备选方案
1. **LangGraph**：功能强大，但复杂度高
2. **Prefect/Airflow**：生产级，但过于重量级
3. **Temporal**：分布式友好，但需要额外服务
4. **自定义状态机**：最大控制力

## 拒绝原因（M0–M1）
- LangGraph：复杂度高，学习成本大，不利于快速迭代
- Prefect/Airflow/Temporal：过于重量级，不适合本地单人场景
- 选择轻 runner 是因为：易控成本与死循环、便于调试、契约稳定

## 后果
- 优：易控成本与死循环、便于调试、runs/run_steps 契约稳定
- 负：初期缺少高级编排特性（并行分支、条件路由等）

## 迁移路径
- 未来可替换为 LangGraph，但保持 runs/run_steps 表结构不变
- 状态机定义见 STATE_MACHINES.md
