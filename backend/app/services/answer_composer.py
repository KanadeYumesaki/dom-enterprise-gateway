from typing import Dict, AsyncGenerator
import re

class AnswerComposerService:
    """
    LLMの最終出力を「Decision」「Why」「Next 3 Actions」のMarkdownセクションに整形するサービス。
    """
    def __init__(self):
        pass

    async def compose_ic5_light_response(self, raw_llm_output: str) -> Dict[str, str]:
        """
        生のLLM出力をパースし、IC-5ライト形式の辞書に整形します。
        """
        # 正規表現パターンを定義
        patterns = {
            "Decision": r"Decision:\s*(.*?)(?=\nWhy:|\nNext 3 Actions:|$)",
            "Why": r"Why:\s*(.*?)(?=\nNext 3 Actions:|$)",
            "Next 3 Actions": r"Next 3 Actions:\s*(.*)",
        }

        composed_response = {
            "Decision": "",
            "Why": "",
            "Next 3 Actions": "",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, raw_llm_output, re.DOTALL)
            if match:
                composed_response[key] = match.group(1).strip()
        
        return composed_response

    async def stream_composed_ic5_light_response(self, raw_llm_token_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """
        LLMトークンストリームを受け取り、IC-5ライト形式に整形しながらストリームします。
        これはより複雑な実装となり、トークンをバッファリングして
        セクションの区切りを検出する必要があります。
        PoCでは、一旦全ての出力を受け取ってから整形する方式を想定し、
        このメソッドは非同期ジェネレータの例として残します。
        """
        full_output = ""
        async for token in raw_llm_token_stream:
            full_output += token
            # ここで部分的なパースを試みることも可能だが、複雑性が増す
            yield token # とりあえずは受け取ったトークンをそのまま流す

        # ストリームが終了した後で整形する場合の例
        # composed = await self.compose_ic5_light_response(full_output)
        # for key, value in composed.items():
        #     yield f"**{key}**\n{value}\n\n"
