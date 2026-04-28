# Python AI Development Standards

1. **强类型约束**：所有函数参数与返回值必须使用 Type Hints；所有 API 输入输出必须定义 Pydantic Schema。
2. **防御性编程**：关键代码块必须包裹在 `try-except` 中，严禁出现裸异常。
3. **副作用隔离**：拒绝全局变量，优先使用依赖注入。
4. **异步安全**：在 async 函数中，必须确保所有 IO 操作有 timeout 机制。
5. **日志规范**：关键路径必须包含带有上下文（context）的结构化日志。
