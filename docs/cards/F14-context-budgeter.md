# F14 — Context Window Budgeter（强制模块）

## 职责
- TokenCounter（精确/估算）
- 分块预算、裁剪策略、位置策略审计

## 不变量
- INV-014：ContextPack 组装过程必须完整记录（retrieval_session + context_pack_items）
- plan/style 尾部锚定永远保留（见 04-runtime.md B4 位置策略）
- estimate 模式预留 margin（建议 15%）

## 测试
- token 计数双轨
- 裁剪顺序与锚定保护
