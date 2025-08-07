import os

import matplotlib.pyplot as plt
import pandas as pd


def run(params: dict) -> dict:
    """
    简单移动平均策略实现
    """
    symbol = params["symbol"]
    start = params["start_date"]
    end = params["end_date"]
    window = int(params.get("window", 20))

    # 这里应该添加实际的数据获取和策略逻辑
    # 此处仅作示例返回

    # 确保静态文件目录存在
    os.makedirs("static", exist_ok=True)

    # 生成示例图表
    plt.figure(figsize=(10, 6))
    plt.plot([1, 2, 3, 4], [1, 4, 2, 3])
    plt.title(f"SMA script: {symbol}")

    # 保存图表
    image_filename = f"sma_{symbol}_{window}.png"
    plt.savefig(f"static/{image_filename}")
    plt.close()

    return {
        "metrics": {"profit": 0.12, "drawdown": 0.03},
        "image_path": f"/static/{image_filename}",
    }
