"""Demonstrate the novelty-aware ToolGatingManager with the smart assistant."""

from __future__ import annotations

from pprint import pprint

from smart_assistant import SmartLearningAssistant


def main() -> None:
    assistant = SmartLearningAssistant()

    tasks = [
        ("整理代碼風格與測試覆蓋率報告", 0.25),
        ("使用統計方法模擬流量高峰並調整配置", 0.48),
        ("設計量子安全演算法並比較現有研究", 0.82),
    ]

    print("📚 Tool gating demo\n---------------------")
    for description, novelty in tasks:
        recommendation = assistant.recommend_tool_for_task(description, novelty)
        print(f"\n📝 任務: {description}")
        print(f"   新穎性: {recommendation['novelty_score']}")
        print(f"   建議工具: {recommendation['selected_tool'] or 'local_reflection'}")
        print("   詳細診斷:")
        pprint(recommendation['diagnostics'])


if __name__ == "__main__":
    main()
