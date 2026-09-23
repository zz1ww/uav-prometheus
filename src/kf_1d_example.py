"""
卡尔曼滤波 完整示例
==================
从定义协方差矩阵开始，一步步实现 1D 卡尔曼滤波
公式全部显式写出，对照看

场景：用激光测距仪跟踪一个匀速运动的目标
真实值：x(t) = 0.5 * t² + 2*t + 10  （匀加速运动，但我们的模型假设匀速——这样能看出滤波效果）
"""

import numpy as np
import matplotlib.pyplot as plt

# =============================================
# 问题设定
# =============================================
np.random.seed(42)

dt = 0.1           # 采样间隔 0.1s
T = 15             # 总时长 15s
N = int(T / dt)    # 总步数

# =============================================
# 真实运动（目标在做匀加速运动，但我们用匀速模型去跟踪）
# =============================================
t = np.arange(0, T, dt)
true_pos = 0.5 * 0.3 * t**2 + 2 * t + 10   # 加速度 0.3 m/s²
true_vel = 0.3 * t + 2                       # 速度

# =============================================
# 观测：激光测距，每 0.1s 测一次，带噪声
# =============================================
R = 0.5**2          # 观测噪声方差 σ² = 0.25（标准差 0.5m）
observations = true_pos + np.sqrt(R) * np.random.randn(N)

# =============================================
# 卡尔曼滤波实现（从零开始，每一步标注协方差的变化）
# =============================================

# ---------- 状态向量 ----------
# x = [位置, 速度]ᵀ
#
# 卡尔曼的 P 矩阵在这里：
# P = [ Var(pos)       Cov(pos, vel) ]
#     [ Cov(vel, pos)  Var(vel)      ]

# ---------- 1. 初始状态 ----------
x_hat = np.array([0.0, 0.0])        # 初始猜测：位置0，速度0

# 初始协方差矩阵 P₀（不确定度很大）
# P₀ = [ Var(pos)       Cov(pos, vel) ]
#       [ Cov(vel, pos)  Var(vel)      ]
# 初始时：
#   - 位置方差很大：Var(pos) = 500（不确定位置）
#   - 速度方差很大：Var(vel) = 50（不确定速度）
#   - 位置和速度的协方差 = 0（初始时假设两者无关）
P = np.array([[500,   0],
              [  0,  50]])

print("========== 初始状态 ==========")
print(f"初始协方差矩阵 P₀:")
print(P)
print(f"对角线（方差）：位置={P[0,0]:.1f}, 速度={P[1,1]:.1f}")
print(f"非对角线（协方差）：{P[0,1]:.1f}（初始无关）")
print(f"正定性检查：P 正定？{np.all(np.linalg.eigvals(P) > 0)}")
print()

# ---------- 2. 模型参数 ----------

# 状态转移矩阵 F（匀速模型）
# xₖ = F·xₖ₋₁
# [posₖ]   = [1  dt] [posₖ₋₁]
# [velₖ]     [0   1] [velₖ₋₁]
F = np.array([[1, dt],
              [0,  1]])

# 观测矩阵 H（我们只观测位置）
# zₖ = H·xₖ + 噪声
# zₖ = [1  0] [posₖ]
#            [velₖ]
H = np.array([[1.0, 0.0]])

# 过程噪声协方差矩阵 Q
# Q 代表"卡尔曼模型不准确"的不确定度
# 因为我们假设匀速模型，但实际有加速，所以 Q 不能太小
# Q 越大 → 滤波越相信观测（反应快但不平滑）
# Q 越小 → 滤波越相信模型（平滑但有延迟）
q_pos = 0.1      # 位置过程噪声
q_vel = 0.3      # 速度过程噪声
Q = np.array([[q_pos,     0],
              [    0,  q_vel]])

# 观测噪声方差 R
R_mat = np.array([[R]])   # 做成矩阵形式，跟 H·P·Hᵀ 的维度匹配

print("========== 模型参数 ==========")
print(f"状态转移矩阵 F:")
print(F)
print(f"过程噪声 Q:")
print(Q)
print(f"观测噪声 R = {R}")
print()

# ---------- 存储结果 ----------
estimates = np.zeros((N, 2))   # [位置, 速度]
cov_trace = np.zeros(N)         # 记录协方差的迹（=总不确定度）

# =============================================
# 主循环：卡尔曼五公式
# =============================================

for k in range(N):
    # --------------------------------------------------
    # 预测（Predict / Time Update）
    # --------------------------------------------------

    # (1) 状态预测
    # x̂ₖ⁻ = F·x̂ₖ₋₁
    x_pred = F @ x_hat

    # (2) 协方差预测
    # Pₖ⁻ = F·Pₖ₋₁·Fᵀ + Q
    #
    # 这一行的含义：
    #   F·Pₖ₋₁·Fᵀ  —— 合同变换，把上一帧的不确定度传播到当前帧
    #   + Q         —— 加上过程噪声（模型不完美引入的额外不确定度）
    #
    # 结果：协方差变大（我们更不确定了）
    P_pred = F @ P @ F.T + Q

    # --------------------------------------------------
    # 更新（Update / Measurement Update）
    # --------------------------------------------------

    # (3) 卡尔曼增益
    # Kₖ = Pₖ⁻·Hᵀ · (H·Pₖ⁻·Hᵀ + R)⁻¹
    #
    # K 决定：观测和预测谁更可信
    #   - 观测很准（R 小）→ K 大 → 偏向观测
    #   - 预测很准（P 小）→ K 小 → 偏向预测
    K = P_pred @ H.T @ np.linalg.inv(H @ P_pred @ H.T + R_mat)

    # (4) 状态更新
    # x̂ₖ = x̂ₖ⁻ + Kₖ·(zₖ - H·x̂ₖ⁻)
    #
    # 括号里是"创新"（innovation）= 观测值 - 预测值
    # 如果创新大 → 模型错了 → K 去修正
    # 如果创新小 → 模型准了 → 修正量很小
    innovation = observations[k] - H @ x_pred
    x_hat = x_pred + K @ innovation

    # (5) 协方差更新
    # Pₖ = (I - Kₖ·H)·Pₖ⁻
    #
    # 观测修正后，不确定度变小
    # 因为获得了新的信息
    P = (np.eye(2) - K @ H) @ P_pred

    # ---------- 存储 ----------
    estimates[k] = x_hat
    cov_trace[k] = np.trace(P)   # 协方差矩阵的迹 = 总不确定度

# =============================================
# 结果——看看协方差是怎么变化的
# =============================================
print("========== 滤波结束 ==========")
print(f"最终协方差矩阵 P:")
print(P)
print(f"对角线（最终方差）：位置={P[0,0]:.4f}, 速度={P[1,1]:.4f}")
print(f"非对角线（协方差）：{P[0,1]:.4f}")
print(f"P 正定？{np.all(np.linalg.eigvals(P) > 0)}")

# =============================================
# 画图
# =============================================
fig, axes = plt.subplots(3, 1, figsize=(12, 8))

# 图1：位置
ax = axes[0]
ax.plot(t, true_pos, 'g-', linewidth=2, label='真实位置')
ax.scatter(t[::5], observations[::5], s=8, color='gray', alpha=0.5, label='观测值')
ax.plot(t, estimates[:, 0], 'b-', linewidth=2, label='卡尔曼估计')
ax.set_ylabel('位置 (m)')
ax.legend()
ax.grid(True)
ax.set_title('卡尔曼滤波：位置跟踪')

# 图2：速度
ax = axes[1]
ax.plot(t, true_vel, 'g-', linewidth=2, label='真实速度')
ax.plot(t, estimates[:, 1], 'b-', linewidth=2, label='卡尔曼估计')
ax.set_ylabel('速度 (m/s)')
ax.legend()
ax.grid(True)
ax.set_title('速度估计')

# 图3：协方差矩阵的迹（总不确定度）
ax = axes[2]
ax.plot(t, cov_trace, 'r-', linewidth=2)
ax.set_xlabel('时间 (s)')
ax.set_ylabel('总不确定度')
ax.set_title('协方差迹的变化（P 的总不确定度随时间收敛）')
ax.grid(True)

plt.tight_layout()
plt.show()

# =============================================
# 额外：验证 P 每一步都保持正定
# =============================================
re_run_P = np.array([[500, 0], [0, 50]])
all_positive = True
for k in range(N):
    x_pred = F @ x_hat
    P_pred = F @ re_run_P @ F.T + Q
    K = P_pred @ H.T @ np.linalg.inv(H @ P_pred @ H.T + R_mat)
    innovation = observations[k] - H @ x_pred
    x_hat = x_pred + K @ innovation
    re_run_P = (np.eye(2) - K @ H) @ P_pred

    eigvals = np.linalg.eigvals(re_run_P)
    if not np.all(eigvals > 0):
        all_positive = False
        print(f"第{k}步 P 不正定！特征值={eigvals}")
        break

print(f"\n协方差矩阵 P 全程保持正定？{all_positive}")
