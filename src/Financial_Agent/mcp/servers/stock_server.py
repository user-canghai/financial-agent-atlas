from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("证券持仓管理系统")

DATA_FILE = Path(__file__).parent / "stock_portfolio.json"

STOCK_NAMES = {
    "600519": "贵州茅台",
    "000001": "平安银行",
    "300750": "宁德时代",
    "601318": "中国平安",
}

SIMULATED_PRICES = {
    "600519": 1680.00,
    "000001": 12.50,
    "300750": 210.00,
    "601318": 45.00,
}

DEFAULT_PORTFOLIO = {
    "account_id": "证券模拟账户",
    "cash_balance": 50000.0,
    "currency": "CNY",
    "holdings": {
        "600519": {"name": "贵州茅台", "shares": 100, "cost_price": 1500.0},
    },
}


def load_portfolio() -> dict:
    if not DATA_FILE.exists():
        save_portfolio(DEFAULT_PORTFOLIO)
        return json.loads(json.dumps(DEFAULT_PORTFOLIO))
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_portfolio(data: dict) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def _price(symbol: str) -> float:
    return SIMULATED_PRICES.get(symbol, 20.0)


@mcp.resource("portfolio://status")
def get_portfolio_status() -> str:
    """查看证券账户现金、持仓与市值。"""
    portfolio = load_portfolio()
    lines = [
        f"--- 账户状态 [{portfolio['account_id']}] ---",
        f"现金余额: {portfolio['cash_balance']:,.2f} {portfolio['currency']}",
        "持仓:",
    ]
    market_value = 0.0
    for symbol, holding in portfolio["holdings"].items():
        value = holding["shares"] * _price(symbol)
        market_value += value
        lines.append(
            f"  {symbol} {holding['name']}: {holding['shares']} 股, "
            f"成本 {holding['cost_price']:.2f} 元, 现价 {_price(symbol):.2f} 元, "
            f"市值 {value:,.2f} 元"
        )
    lines.append(f"持仓总市值: {market_value:,.2f} {portfolio['currency']}")
    lines.append(f"总资产: {portfolio['cash_balance'] + market_value:,.2f} {portfolio['currency']}")
    return "\n".join(lines)


@mcp.tool()
def get_stock_price(symbol: str) -> str:
    """获取指定股票的模拟行情。

    Args:
        symbol: 六位股票代码，如 ``600519``。
    """
    if symbol not in STOCK_NAMES:
        return f"未找到股票 {symbol}；模拟环境支持: {', '.join(STOCK_NAMES)}。"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        f"## {symbol} {STOCK_NAMES[symbol]}（{now}）\n"
        f"- 现价: {_price(symbol):.2f} 元\n"
        "- 数据来源: 模拟行情"
    )


@mcp.tool()
def buy_stock(symbol: str, shares: int, price_cny: float | None = None) -> str:
    """买入股票。

    Args:
        symbol: 股票代码。
        shares: 买入股数（正整数）。
        price_cny: 成交价（元/股）；为空时使用模拟现价。
    """
    if symbol not in STOCK_NAMES:
        return f"交易失败：未知股票 {symbol}。"
    if shares <= 0:
        return "交易失败：买入股数必须大于 0。"

    price = price_cny if price_cny is not None else _price(symbol)
    if price <= 0:
        return "交易失败：成交价必须大于 0。"

    portfolio = load_portfolio()
    cost = shares * price
    if portfolio["cash_balance"] < cost:
        return (
            f"交易失败：余额不足。需要 {cost:,.2f} 元，"
            f"当前余额 {portfolio['cash_balance']:,.2f} 元。"
        )

    holding = portfolio["holdings"].get(symbol)
    if holding is None:
        portfolio["holdings"][symbol] = {
            "name": STOCK_NAMES[symbol],
            "shares": shares,
            "cost_price": price,
        }
    else:
        total_shares = holding["shares"] + shares
        holding["cost_price"] = (
            holding["cost_price"] * holding["shares"] + price * shares
        ) / total_shares
        holding["shares"] = total_shares

    portfolio["cash_balance"] -= cost
    save_portfolio(portfolio)
    return (
        "交易成功！\n"
        f"买入: {symbol} {STOCK_NAMES[symbol]} {shares} 股\n"
        f"成交价: {price:.2f} 元/股\n"
        f"花费金额: {cost:,.2f} 元\n"
        f"当前现金余额: {portfolio['cash_balance']:,.2f} 元"
    )


@mcp.tool()
def sell_stock(symbol: str, shares: int, price_cny: float | None = None) -> str:
    """卖出股票。

    Args:
        symbol: 股票代码。
        shares: 卖出股数（正整数）。
        price_cny: 成交价（元/股）；为空时使用模拟现价。
    """
    if shares <= 0:
        return "交易失败：卖出股数必须大于 0。"

    portfolio = load_portfolio()
    holding = portfolio["holdings"].get(symbol)
    if holding is None or holding["shares"] < shares:
        current = holding["shares"] if holding else 0
        return f"交易失败：持仓不足。当前持有 {current} 股。"

    price = price_cny if price_cny is not None else _price(symbol)
    if price <= 0:
        return "交易失败：成交价必须大于 0。"

    revenue = shares * price
    holding["shares"] -= shares
    if holding["shares"] == 0:
        portfolio["holdings"].pop(symbol, None)
    portfolio["cash_balance"] += revenue
    save_portfolio(portfolio)
    return (
        "交易成功！\n"
        f"卖出: {symbol} {STOCK_NAMES.get(symbol, '')} {shares} 股\n"
        f"成交价: {price:.2f} 元/股\n"
        f"收入金额: {revenue:,.2f} 元\n"
        f"当前现金余额: {portfolio['cash_balance']:,.2f} 元"
    )


@mcp.tool()
def deposit_cash(amount_cny: float, description: str = "") -> str:
    """向证券账户存入现金。"""
    if amount_cny <= 0:
        return "存款失败：金额必须大于 0。"
    portfolio = load_portfolio()
    portfolio["cash_balance"] += amount_cny
    save_portfolio(portfolio)
    result = (
        "存款成功！\n"
        f"存入金额: +{amount_cny:,.2f} {portfolio['currency']}\n"
        f"当前现金余额: {portfolio['cash_balance']:,.2f} {portfolio['currency']}"
    )
    if description:
        result += f"\n说明: {description}"
    return result


@mcp.tool()
def withdraw_cash(amount_cny: float, description: str = "") -> str:
    """从证券账户取出现金。"""
    if amount_cny <= 0:
        return "取款失败：金额必须大于 0。"
    portfolio = load_portfolio()
    if portfolio["cash_balance"] < amount_cny:
        return (
            "取款失败：余额不足。"
            f"需要 {amount_cny:,.2f} 元，当前余额 {portfolio['cash_balance']:,.2f} 元。"
        )
    portfolio["cash_balance"] -= amount_cny
    save_portfolio(portfolio)
    result = (
        "取款成功！\n"
        f"取出金额: -{amount_cny:,.2f} {portfolio['currency']}\n"
        f"当前现金余额: {portfolio['cash_balance']:,.2f} {portfolio['currency']}"
    )
    if description:
        result += f"\n说明: {description}"
    return result


@mcp.prompt()
def instruction_manual() -> str:
    """证券账户操作规范。"""
    return (
        "你是一位证券交易模拟助手。操作规范：\n"
        "1. 每次买卖前后都必须读取 `portfolio://status` 核对现金和持仓。\n"
        "2. 买入前先使用 `get_stock_price` 获取模拟行情，确认价格参数。\n"
        "3. 禁止裸卖空：卖出股数不得超过当前持仓。\n"
        "4. 本服务器仅用于模拟演示，不连接真实交易所。\n"
    )


if __name__ == "__main__":
    mcp.run()
