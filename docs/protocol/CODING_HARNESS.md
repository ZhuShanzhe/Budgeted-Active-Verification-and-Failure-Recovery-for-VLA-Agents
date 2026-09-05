# 决策程序与失败驱动代码迭代

## 1. 双层职责

运行时程序回答：证据是否充分、下一项工具是什么、是否继续或请求恢复。离线 coding agent 回答：当前程序在哪些开发案例上出错，如何修改其条件、工具选择与停止逻辑。

两个层次共享任务方向，但不共享权限。生成器只交付一个 `decide(ctx)` 候选文件。预算、critic、工具实现、仿真标签、数据划分、评测程序和正式结果文件由操作者管理，不能成为生成器的改写目标。

## 2. 程序接口

允许读取字段为 risk、uncertainty、evidence_sufficient、failure_hypothesis、remaining_units、remaining_queries、queried_tools、available_tools、step、history_length、last_tool_status。

输出 action 取 query、accept、abstain、recover、stop。query 指定已登记 tool；recover 指定已登记 recovery。Runtime 再次验证返回值，并实施查询预算限制。未配置 critic 时风险为空，参考程序拒绝把空值当作安全。

程序采用 Python 语法的受限 AST 解释器，不执行 Python `exec/eval`。允许局部赋值、有限表达式、条件判断和返回；禁止 import、任意函数调用、属性访问、循环、文件、网络和修改上下文。设置源码、节点和操作次数上限。模型仍可生成 Python 风格的判断程序，但不能运行任意 Python 项目。

这是可执行决策表示的最小可信边界，不是通用 coding agent 沙箱。若后续允许修改工具代码或使用完整 Python，必须在无密钥、无测试数据挂载、无网络、有限 CPU/内存/时间的独立隔离环境执行，并重新审核权限。

## 3. 固定 critic 接口

受信任操作者通过 `module:factory` 配置 critic。模块返回 artifact_id、target、calibrated 和 assess(inputs, evidence)。target 必须声明 current_goal_unmet 或 eventual_failure。返回风险概率、不确定性、证据充分性、失败假设及真实调用开销。

参考 NullCritic 只用于确认管线能够运行，返回 risk=null；不能用它报告失败检测或证据价值成绩。现有 SAFE WidowX checkpoint 的特征、机器人和标签不同，没有被强行包装成 LIBERO 多模态 critic。后续在主训练根训练新的轻量 critic，再在独立校准根定阈值；冻结其版本后比较路由程序。

## 4. 失败驱动迭代流程

1. 在开发根上执行当前程序并记录错误、拒绝、预算和恢复请求。
2. failure-pack 汇总训练/开发案例及有来源的反馈；校准与测试标签拒绝进入该包。成功案例和右删失案例保留真实状态，不伪装失败。
3. coding agent 读取允许的案例及接口说明，生成新的 decide(ctx)。记录模型版本、提示版本、输入/输出 token、尝试次数、墙钟时间和程序哈希。
4. 候选通过语法、资源、权限检查；固定 critic、固定根、固定预算下与旧程序配对重评。候选不能自行宣布通过。
5. 比較独立 held-in 改善与回归集合结果。当前 check 接口要求相同协议/critic/评测器/数据、独立根、有效指标，拒绝无 critic、样本不足、执行错误、回归和缺少 held-in 改善。
6. 闸门只输出报告，不执行自动部署。正式测试由操作者在冻结方案后运行；反复回归的集合不得继续称为最终未见测试。

目前没有连接或调用付费 coding 模型，没有自动提交、改写主仓库或自我部署。代码生成成本字段保持未配置，不能记作零成本实证。当前闸门读取的是操作者生成的报告，不是防 root 篡改的安全认证，也没有总体统计非劣保证。

## 5. 闭环边界

离线程序评测能够检验证据路由与固定 critic 的变化，但不能从一条已有轨迹推断另一种控制决策的闭环成功率。recover 输出在离线结果中记为 not_simulated。真实恢复实验单独启动，从同一状态恢复并执行分支。

将训练后的 critic 与程序接入在线控制，需要进一步实现全轨迹恢复次数、动作步数、总计算与机器人暂停预算，执行确认，以及恢复技能失败后的停止行为。本轮接口把这一步与离线可执行程序明确分开，不把恢复请求数量当作已经成功恢复。
