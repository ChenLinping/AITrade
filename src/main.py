# -*- coding: utf-8 -*-
"""
红利-科技 周频调仓模拟器（Python GUI 版）
特点：
- 手动输入周涨跌幅
- 给出是否调仓 + 调仓金额（10万总仓位）
- 内部模拟仓位
- 自动持久化保存历史记录（JSON）
- 支持删除指定记录（用于清理测试数据）

适合实盘“决策支持”，不自动交易
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

# ================= 基础参数 =================
TOTAL_CAPITAL = 100000
TARGET_DIVIDEND = 0.60
MAX_WEEKLY_SHIFT = 0.03      # 单周最大调仓 3%
TRIGGER_THRESHOLD = 0.01     # 触发阈值 1%
DATA_FILE = "rebalance_history.json"

# ================= 数据处理 =================
def load_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


# ================= 核心策略 =================
def run_strategy(dividend_ret, state):
    action = "不调仓"
    amount = 0

    if abs(dividend_ret) >= TRIGGER_THRESHOLD:
        shift_ratio = min(abs(dividend_ret), MAX_WEEKLY_SHIFT)
        shift_amount = TOTAL_CAPITAL * shift_ratio

        if dividend_ret > 0 and state['dividend'] > 0:
            action = "红利 → 科技"
            amount = shift_amount
            state['dividend'] -= shift_ratio
            state['tech'] += shift_ratio

        elif dividend_ret < 0 and state['tech'] > 0:
            action = "科技 → 红利"
            amount = shift_amount
            state['tech'] -= shift_ratio
            state['dividend'] += shift_ratio

    # 仓位归一化保护
    total = state['dividend'] + state['tech']
    state['dividend'] /= total
    state['tech'] /= total

    return action, round(amount, 2)


# ================= GUI =================
class RebalanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("红利-科技 周频调仓模拟器")
        self.geometry("820x520")

        self.state = {'dividend': TARGET_DIVIDEND, 'tech': 1 - TARGET_DIVIDEND}
        self.records = load_history()

        self.create_widgets()
        self.refresh_table()

    def create_widgets(self):
        # 输入区
        frame = ttk.LabelFrame(self, text="本周输入")
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="红利低波周涨跌幅（%）：").pack(side="left")
        self.ret_entry = ttk.Entry(frame, width=10)
        self.ret_entry.pack(side="left", padx=5)

        ttk.Button(frame, text="运行策略", command=self.run).pack(side="left", padx=10)

        # 状态区
        self.status = ttk.Label(self, text="", foreground="blue")
        self.status.pack(fill="x", padx=10, pady=5)

        # 表格
        cols = ("时间", "红利涨跌", "操作", "调仓金额", "红利仓位", "科技仓位")
        self.table = ttk.Treeview(self, columns=cols, show="headings", height=15)
        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, anchor="center")
        self.table.pack(fill="both", expand=True, padx=10)

        # 删除按钮
        ttk.Button(self, text="删除选中记录", command=self.delete_record).pack(pady=5)

    def run(self):
        try:
            dividend_ret = float(self.ret_entry.get()) / 100
        except ValueError:
            messagebox.showerror("错误", "请输入合法的涨跌幅")
            return

        action, amount = run_strategy(dividend_ret, self.state)

        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ret": f"{dividend_ret*100:.2f}%",
            "action": action,
            "amount": f"{amount:.2f}",
            "dividend": f"{self.state['dividend']*100:.1f}%",
            "tech": f"{self.state['tech']*100:.1f}%"
        }

        self.records.append(record)
        save_history(self.records)
        self.refresh_table()

        self.status.config(text=f"结果：{action}，建议调仓 {amount:.2f} 元")

    def refresh_table(self):
        for row in self.table.get_children():
            self.table.delete(row)
        for r in self.records:
            self.table.insert("", "end", values=(r['time'], r['ret'], r['action'], r['amount'], r['dividend'], r['tech']))

    def delete_record(self):
        selected = self.table.selection()
        if not selected:
            return
        index = self.table.index(selected[0])
        del self.records[index]
        save_history(self.records)
        self.refresh_table()


if __name__ == '__main__':
    app = RebalanceApp()
    app.mainloop()
