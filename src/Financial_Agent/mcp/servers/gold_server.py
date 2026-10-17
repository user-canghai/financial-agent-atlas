from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("黄金交易模拟系统")

DATA_FILE = Path(__file__).parent / "gold_account.json"

DEFAULT_ACCOUNT = {
    "account_id": "上海金",
    "cash_balance": 100000.0,
    "gold_weight_gram": 166.67,
    "currency": "CNY",
}


def load_account() -> dict:
    if not DATA_FILE.exists():
        save_account(DEFAULT_ACCOUNT)
        return dict(DEFAULT_ACCOUNT)
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_account(data: dict) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


@mcp.resource("account://status")
def get_account_status() -> str:
    """查看当前黄金账户的现金余额与黄金储量情况。"""
    account = load_account()
    return (
        f"--- 账户状态 [{account['account_id']}] ---\n"
        f"现金余额: {account['cash_balance']:,.2f} {account['currency']}\n"
        f"黄金储备: {account['gold_weight_gram']:.2f} 克"
    )


@mcp.tool()
def buy_gold(amount_grams: float, current_price_cny: float) -> str:
    """使用现金买入黄金。

    Args:
        amount_grams: 欲买入的黄金克数。
        current_price_cny: 当前市场金价（元/克），由 Agent 从外部获取。
    """
    if amount_grams <= 0 or current_price_cny <= 0:
        return "交易失败：买入克数与金价必须大于 0。"

    account = load_account()
    cost = amount_grams * current_price_cny
    if account["cash_balance"] < cost:
        return (
            f"交易失败：余额不足。需要 {cost:,.2f} 元，当前余额 {account['cash_balance']:,.2f} 元。"
        )

    account["cash_balance"] -= cost
    account["gold_weight_gram"] += amount_grams
    save_account(account)
    return (
        "交易成功！\n"
        f"买入重量: {amount_grams} 克\n"
        f"成交单价: {current_price_cny} 元/克\n"
        f"花费金额: {cost:,.2f} 元\n"
        f"当前持有黄金: {account['gold_weight_gram']:.2f} 克"
    )


@mcp.tool()
def sell_gold(amount_grams: float, current_price_cny: float) -> str:
    """卖出黄金以换取现金。

    Args:
        amount_grams: 欲卖出的黄金克数。
        current_price_cny: 当前市场金价（元/克）。
    """
    if amount_grams <= 0 or current_price_cny <= 0:
        return "交易失败：卖出克数与金价必须大于 0。"

    account = load_account()
    if account["gold_weight_gram"] < amount_grams:
        return f"交易失败：黄金储备不足。当前持有: {account['gold_weight_gram']:.2f} 克。"

    revenue = amount_grams * current_price_cny
    account["cash_balance"] += revenue
    account["gold_weight_gram"] -= amount_grams
    save_account(account)
    return (
        "交易成功！\n"
        f"卖出重量: {amount_grams} 克\n"
        f"成交单价: {current_price_cny} 元/克\n"
        f"收入金额: {revenue:,.2f} 元\n"
        f"当前现金余额: {account['cash_balance']:,.2f} 元"
    )


@mcp.tool()
def get_gold_price() -> str:
    """获取上海黄金交易所 Au99.99 / Au99.95 的实时模拟行情。"""
    price_data = [
        {"name": "Au99.99（现货黄金）", "price": 892.00, "change": "+0.82%"},
        {"name": "Au99.95", "price": 897.60, "change": "+0.75%"},
    ]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"## 上海黄金交易所 - 黄金价格（{now}）",
        "| 品种 | 价格（元/克） | 涨跌幅 |",
        "|------|---------------|--------|",
    ]
    for item in price_data:
        lines.append(f"| {item['name']} | {item['price']:.2f} | {item['change']} |")
    lines.extend(
        [
            "",
            "**数据来源**：上海黄金交易所模拟行情",
            f"**获取时间**：{now}",
        ]
    )
    return "\n".join(lines)


@mcp.tool()
def deposit(amount_cny: float, description: str = "") -> str:
    """向账户存入现金。

    Args:
        amount_cny: 存入金额（元）。
        description: 存款说明（可选），用于审计追踪。
    """
    if amount_cny <= 0:
        return "存款失败：金额必须大于 0。"
    account = load_account()
    account["cash_balance"] += amount_cny
    save_account(account)
    result = (
        "存款成功！\n"
        f"存入金额: +{amount_cny:,.2f} {account['currency']}\n"
        f"当前现金余额: {account['cash_balance']:,.2f} {account['currency']}"
    )
    if description:
        result += f"\n说明: {description}"
    return result


@mcp.tool()
def withdraw(amount_cny: float, description: str = "") -> str:
    """从账户取出现金。

    Args:
        amount_cny: 取款金额（元）。
        description: 取款说明（可选），用于审计追踪。
    """
    if amount_cny <= 0:
        return "取款失败：金额必须大于 0。"
    account = load_account()
    if account["cash_balance"] < amount_cny:
        return (
            "取款失败：余额不足。"
            f"需要 {amount_cny:,.2f} {account['currency']}，"
            f"当前余额 {account['cash_balance']:,.2f} {account['currency']}。"
        )
    account["cash_balance"] -= amount_cny
    save_account(account)
    result = (
        "取款成功！\n"
        f"取出金额: -{amount_cny:,.2f} {account['currency']}\n"
        f"当前现金余额: {account['cash_balance']:,.2f} {account['currency']}"
    )
    if description:
        result += f"\n说明: {description}"
    return result


@mcp.prompt()
def instruction_manual() -> str:
    """提供黄金账户的功能介绍和操作规范。"""
    return (
        "你是一位金融模拟交易助手。请介绍本 MCP 工具的操作流程：\n\n"
        "【操作规范-必须遵循】\n"
        "**每次操作前后都必须查询账户状态！**\n"
        "1. 操作前查询：使用 `account://status` 查看当前现金和黄金克数，确认是否可以执行操作。\n"
        "2. 操作后查询：再次使用 `account://status` 验证操作结果，确认数据变化正确。\n\n"
        "【重要】在执行任何买卖操作之前，必须先获取最新的黄金价格：\n"
        "1. 使用 `get_gold_price` 工具获取 Au99.99、Au99.95 实时模拟金价；\n"
        "2. 或使用 `fetch` MCP 工具访问 https://www.sge.com.cn/ 上海黄金交易所官网；\n"
        "3. 将获取到的价格作为参数传入 `buy_gold` 或 `sell_gold` 工具。\n\n"
        "【账户功能】\n"
        "1. **实时查询**：使用 `account://status` 资源查看当前的现金和黄金克数。\n"
        "2. **存取款**：\n"
        "   - 存款：使用 `deposit` 工具，存入现金到账户。\n"
        "   - 取款：使用 `withdraw` 工具，从账户取出现金。\n"
        "3. **模拟交易**：\n"
        "   - 买入：使用 `buy_gold` 工具，**必须传入**最新金价（元/克）。\n"
        "   - 卖出：使用 `sell_gold` 工具，**必须传入**最新金价（元/克）。\n\n"
        "**观察重点**：关注金价波动时，总资产"
        "（现金 + 黄金克数 × 实时金价）的变化。"
        "执行任何买卖前都需确认用户提供的最新金价参数。"
    )


if __name__ == "__main__":
    mcp.run()
