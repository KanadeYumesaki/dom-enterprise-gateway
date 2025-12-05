from typing import AsyncGenerator
import asyncio

class MockLLMClient:
    """
    LLMからのストリーミング応答をシミュレートするモッククライアント。
    IC-5ライト形式に整形可能なダミー応答を返します。
    """
    async def stream_chat_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        プロンプトに基づいてチャット応答をトークンごとにストリーミングします。
        IC-5ライト形式のダミー応答を生成します。
        """
        raw_llm_response = f"""
Decision: The request to implement IC-5 Light format for LLM responses has been acknowledged and will be processed.
Why: Implementing IC-5 Light format ensures structured and actionable responses, improving clarity and decision-making for enterprise users. This aligns with the project's governance and explainability goals.
Next 3 Actions:
1. Implement AnswerComposerService to parse raw LLM output into IC-5 Light Markdown sections.
2. Integrate AnswerComposerService into DomOrchestratorService to format streamed tokens.
3. Update unit tests to verify correct IC-5 Light formatting and streaming behavior.
"""
        words = raw_llm_response.split(" ")
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05) # 短い遅延をシミュレート
        yield "[END]" # ストリームの終了を示す特別なトークン

