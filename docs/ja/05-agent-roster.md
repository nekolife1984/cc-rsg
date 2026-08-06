# Agent Roster — フェーズ別モデル最適化

## 概要

**Agent Roster** は、各ADWフェーズに異なるLLMモデルを割り当てる仕組みです。すべてのフェーズを同じモデルで実行する代わりに、単純なフェーズには安価なモデルを、深い推論が必要なフェーズには高価なモデルを割り当てることで、コストを最適化できます。

## 仕組み

### 設定

すべてのロスター設定は `adws/adw_sssf_config/sssf.config.yaml` にあります：

```yaml
# グローバルデフォルト（全エージェントが継承）
defaults:
  provider: opencode-zen
  model: ds-v4-flash
  cli: opencode

# フェーズ → エージェント ロスター
roster:
  setup: engineer
  recon: scout
  wbs: engineer
  investigate: investigator
  verify: engineer
  refine: engineer
  deliver: engineer
  drift: engineer
  changespec: changespec

# エージェント定義
agents:
  engineer:
    provider: opencode-zen
    model: ds-v4-flash
    cli: opencode
  scout:
    provider: opencode-zen
    model: ds-v4-flash
    cli: opencode
  investigator:
    provider: opencode-zen
    model: ds-v4-flash
    cli: opencode
  changespec:
    provider: opencode-zen
    model: ds-v4-flash
    cli: opencode
```

### 解決順序

フェーズがLLM呼び出しを必要とするとき、以下の順序でエージェントを解決します：

1. **ロスター検索** — 設定の `roster.{phase_name}`
2. **コードのフォールバック** — `session.py` の `_PHASE_TO_AGENT` 辞書
3. **フェーズ名フォールバック** — フェーズ名そのものをエージェント名として使用
4. **デフォルトマージ** — エージェント定義の各フィールドが `defaults` をオーバーライド。欠落フィールドは `defaults` から継承

### CLIバックエンド解決順序

1. エージェントごとの `cli` フィールド
2. 設定の `defaults.cli`
3. `ADW_CLI` 環境変数
4. ハードデフォルト: `opencode`

### モデル解決順序

1. エージェントごとの `model` フィールド
2. 設定の `defaults.model`
3. `ADW_MODEL` 環境変数
4. ハードデフォルト: `ds-v4-flash`

## コスト最適化戦略

| フェーズ | 必要な能力 | 推奨モデルクラス | 相対コスト |
|---------|-----------|-----------------|-----------|
| Setup | ゴール定義 | Flash級 | 💰 低 |
| Recon | ファイルスキャン＋要約 | Flash級 | 💰 低 |
| WBS | 構造化＋分類 | Flash級 | 💰 低 |
| Investigate | 深いコード理解 | Reasoning級 | 💰💰 中 |
| Verify | コードフェーズ（LLM不要） | — | $0 |
| Refine | ユーザー対話 | High-reasoning級 | 💰💰💰 高 |
| Deliver | 集約 | Flash級 | 💰 低 |
| Drift | 差分分析 | Flash級 | 💰 低 |
| Changespec | 変更説明 | Flash級 | 💰 低 |

### 最適化ロスターの例

フェーズごとに異なるモデルを使うには、`sssf.config.yaml` の `roster` と `agents` セクションを編集します：

```yaml
roster:
  recon: recon-agent            # スキャンには安価なモデル
  investigate: deep-investigator  # 深い分析には高価なモデル
  refine: dialogue-agent        # 対話的な推論
  # その他のフェーズは engineer（デフォルト）

agents:
  recon-agent:
    provider: opencode-zen
    model: google/gemini-3.6-flash    # 安価で高速
    cli: opencode
  deep-investigator:
    provider: fireworks
    model: fireworks/accounts/fireworks/models/kimi-k3  # 深い推論
    cli: opencode
  dialogue-agent:
    provider: openai
    model: openai/gpt-5.6-terra       # 高推論力
    cli: opencode
```

### コスト比較（1000ファイルのコードベース想定）

| シナリオ | 入力トークン | 推定コスト |
|---------|-------------|-----------|
| すべてFlash級 | 全量×1モデル | $2.50 |
| 最適化（Flash + K3 + Terra） | フェーズ別 | $10–20 |
| すべてハイエンド（Opus 5） | 全量×1モデル | $150+ |

→ 最適化ロスターは **ハイエンド一括と比較して約87%削減** しながら、必要なフェーズにのみ高価なモデルを割り当てます。

## プログラムAPI

### `agents.get_defaults()`

`sssf.config.yaml` から `defaults` セクションを読み込みます：

```python
from adws.adw_modules import agents
defaults = agents.get_defaults()
# 戻り値: {"provider": "opencode-zen", "model": "ds-v4-flash", "cli": "opencode"}
```

### `session._resolve_agent_def(phase_name)`

フェーズのマージ済みエージェント定義を解決します（内部API）：

```python
from adws.adw_modules import session
agent_def = session._resolve_agent_def("investigate")
# 戻り値: defaults + エージェント固有のオーバーライドをマージした辞書
```

## フェーズ種別

| 種別 | 説明 | LLM必要？ |
|------|------|----------|
| `engineer` | 対話型エンジニアリングフェーズ | はい |
| `agent` | 自動エージェントフェーズ | はい |
| `code` | 純粋なコードフェーズ（LLM不要） | いいえ |

`code` 種別のフェーズ（verify, deliver, drift）はLLM呼び出しを行わないため、モデル予算を消費しません。これらは純粋にPythonスクリプトとして実行されます。
