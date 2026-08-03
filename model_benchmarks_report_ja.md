# OpenCode Zen プラットフォーム 無料モデル ベンチマーク比較レポート

> 作成日: 2026-08-01
> 参照ソース: HuggingFace Model Cards, DeepSeek V4 技術報告書, NVIDIA Nemotron 3 Ultra 技術報告書, InclusionAI Ling 2.6 Flash README, Poolside Laguna S 2.1 README, Cohere North Mini Code README, Xiaomi MiMo V2.5 README

---

## エグゼクティブサマリー

OpenCode Zen プラットフォームで利用可能な6つの無料モデルを徹底比較。モデルサイズは **3B〜550Bパラメータ** と幅広く、それぞれ異なる強みを持つ。

- **コード/エージェント性能の王者**: DeepSeek V4 Flash (284B-A13B) — 全体的に最もバランスの取れた高性能
- **エージェントコーディング特化**: Laguna S 2.1 (118B-A8.5B) — SWE-bench Multilingual で最高スコア
- **トークン効率重視**: Ling 3.0 Flash (104B-A7.4B) — 軽量で高速、エージェントタスクに最適化
- **マルチモーダル万能**: MiMo v2.5 (310B-A15B) — テキスト・画像・動画・音声対応
- **フロンティア推論**: Nemotron 3 Ultra (550B-A55B) — 最大規模、数学・推論タスクで強力
- **超軽量コード特化**: North Mini Code (30B-A3B) — わずか3B活性でコードエージェント性能

---

## 比較表

| モデル | 総パラメータ | 活性パラメータ | コンテキスト長 | MMLU-Pro | HumanEval | LiveCodeBench | SWE-bench Verified | GPQA Diamond | ライセンス |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| **DeepSeek V4 Flash** | 284B | 13B | 1M | **86.4** | 69.5% | **88.4** | **78.6%** | 87.4 | MIT |
| **Laguna S 2.1** | 118B | 8.5B | 262K (最大1M) | — | — | — | — | — | OpenMDW-1.1 |
| **Ling 3.0 Flash** | 104B | 7.4B | 262K | — | — | — | — | — | MIT |
| **MiMo v2.5** | 310B | 15B | 1M | — | — | — | — | — | MIT |
| **Nemotron 3 Ultra** | 550B | 55B | 1M | 86.8 | — | 89.0 | 70.7% | 87.0 | OpenMDW-1.1 |
| **North Mini Code** | 30B | 3B | 256K | — | — | — | — | — | Apache 2.0 |

> ※ 「—」は公開ベンチマークデータが確認できなかった項目。各モデルの提供元が異なるベンチマークを優先して報告しているため、同一基準での横比較が難しい項目がある。

---

## 1. DeepSeek V4 Flash

**モデルID**: `opencode/deepseek-v4-flash-free` (HuggingFace: `deepseek-ai/DeepSeek-V4-Flash`)

### 基本スペック
| 項目 | 値 |
|:---|---:|
| アーキテクチャ | MoE (Mixture of Experts) |
| 総パラメータ | 284B |
| 活性パラメータ | 13B |
| コンテキスト長 | 1,000,000 トークン (1M) |
| 精度 | FP4 + FP8 Mixed |
| ライセンス | MIT |
| 学習データ | 32T+ トークン |

### ベンチマークスコア（Think High モード / DeepSeek V4 READMEより）

| ベンチマーク | スコア |
|:---|---:|
| **MMLU-Pro** (EM) | 86.4 |
| **GPQA Diamond** (Pass@1) | 87.4 |
| **LiveCodeBench** (Pass@1) | 88.4 |
| **SWE-bench Verified** (Resolved) | 78.6 |
| **SimpleQA-Verified** (Pass@1) | 28.9 |
| **HLE** (Pass@1) | 29.4 |
| **Terminal Bench 2.0** (Acc) | 56.6 |
| **BrowseComp** (Pass@1) | 53.5 |
| **MCPAtlas** (Pass@1) | 67.4 |
| **MRCR 1M** (MMR, 長文) | 76.9 |

### ベースモデルのベンチマーク
| ベンチマーク | DS-V4-Flash-Base |
|:---|---:|
| MMLU (5-shot) | 88.7 |
| MMLU-Pro (5-shot) | 68.3 |
| HumanEval (Pass@1, 0-shot) | 69.5 |
| GSM8K (8-shot) | 90.8 |
| MATH (4-shot) | 57.4 |

### 主な強み
- **驚異的なコスト効率**: 284B総/13B活性で、GPT-5.4-Pro相当の性能を一部タスクで達成
- **100万トークン対応**: 最長クラスのコンテキスト窓
- **ハイブリッド注意機構**: CSA + HCA による長文効率の大幅改善
- **3段階推論モード**: Non-Think / High / Max を使い分け可能
- **最高のコード生成性能**: SWE-bench Verified 78.6%、LiveCodeBench 88.4%

### 制限事項
- **知識タスクではPro版に劣る**: MMLU-Pro 86.4 vs Pro版 87.5
- **Think Max時は多くの推論トークンを消費**
- **エージェントタスクではNemotronやLagunaに一部劣る**: Terminal Bench 56.6%
- **FP4量子化**: 理論上はBF16より精度が低下する可能性

---

## 2. Laguna S 2.1

**モデルID**: `opencode/laguna-s-2.1-free` (HuggingFace: `poolside/Laguna-S-2.1`)

### 基本スペック
| 項目 | 値 |
|:---|---:|
| 開発元 | Poolside (旧 Poolside AI) |
| アーキテクチャ | MoE (256専門家, 1共有) |
| 総パラメータ | 117.6B |
| 活性パラメータ | 8.5B |
| レイヤー | 48層 (12 グローバル注意 + 36 SWA) |
| スライディングウィンドウ | 512 トークン |
| コンテキスト長 | 262,144 (ネイティブ1M対応) |
| ライセンス | OpenMDW-1.1 |
| 最適化手法 | Muon Optimizer |

### ベンチマークスコア（Poolside公式）

| ベンチマーク | スコア |
|:---|---:|
| **Terminal-Bench 2.1** | **70.2%** |
| **SWE-bench Multilingual** | **78.5%** |
| **SWE-Bench Pro** (Public Dataset) | **59.4%** |
| **DeepSWE** | 40.4% |
| **SWE Atlas (Codebase QnA)** | 46.2% |
| **Toolathlon Verified** | 49.7% |

（参考比較: DeepSeek-V4-Pro Max は Terminal-Bench 64.0%, SWE Multilingual 76.2%）

### 主な強み
- **エージェントコーディングのスペシャリスト**: SWE-bench Multilingual 78.5%は6モデル中トップ
- **驚異的な活性効率**: 8.5B活性でDeepSeek V4 Pro (49B活性) に迫るエージェント性能
- **ローカル運用可能**: NVFP4量子化=約71GB、Ollama/llama.cppサポート
- **ネイティブ推論サポート**: 思考とツール呼び出しのインターリーブ
- **DFlash 投機的復号**: 最大3 tok/sの高速化

### 制限事項
- **汎用知識ベンチマーク非公開**: MMLU-Pro, HumanEval などのスコアが未報告
- **エージェント以外のタスクでは比較データ不足**
- **メモリ要件が高い**: NVFP4でも71GB、FP16は235GB必要
- **OpenMDWライセンス**: MITより制限が多い場合あり
- **Poolside独自のツール呼び出しフォーマット**: 一部フレームワークとの互換性に注意

---

## 3. Ling 3.0 Flash

**モデルID**: `opencode/ling-3.0-flash-free` (HuggingFace: `inclusionAI/Ling-2.6-flash`)

> ⚠️ OpenCode上の「Ling 3.0 Flash」は、HuggingFaceでは **Ling-2.6-flash** として公開されているモデルと同一と推定される。

### 基本スペック
| 項目 | 値 |
|:---|---:|
| 開発元 | InclusionAI (蚂蚁集团/Alibaba Group傘下) |
| アーキテクチャ | MoE + ハイブリッド線形注意機構 (MLA + Lightning Linear, 1:7比率) |
| 総パラメータ | 104B |
| 活性パラメータ | 7.4B |
| コンテキスト長 | 262,144 |
| 推論速度 | 340 tok/s (4×H20) |
| ライセンス | MIT |

### ベンチマークスコア（InclusionAI公式、画像ベースのため一部推定含む）

| ベンチマーク | 性能評価 |
|:---|---:|
| **BFCL-V4** (Tool Calling) | 競合モデルに匹敵〜SOTOレベル |
| **TAU2-bench** (エージェント) | 強力 |
| **SWE-bench Verified** | 強力 |
| **Claw-Eval** | 強力 |
| **PinchBench** | 強力 |
| **IFBench** (指示追従) | GPT-OSS-120B/ GPT-5.4-mini と同等以上 |
| **AA評価スイート全体** | 15Mトークンで競合性能 |

### 主な強み
- **トークン効率最適化**: 全AA評価スイートをたった **15Mトークン** で完了。業界最小級
- **超高速推論**: 4×H20で **340 tok/s**、ピーク時は4倍高速
- **軽量設計**: 7.4B活性でDeepSeek V4 Flash (13B) よりさらに軽い
- **エージェントワークロード最適化**: BFCL-V4, TAU2-bench で競合モデルに匹敵
- **Envolutionary CoT / Linguistic Unit Policy Optimization**: 独自のトークン効率化手法
- **Claude Code, Kilo Code, Qwen Code, Hermes Agent 等との互換性**

### 制限事項
- **深い推論には非対応**: Ring-2.6 シリーズが深い推論向け
- **複雑シナリオでのツール幻覚**: 限られた推論深さに起因
- **中英バイリンガル切り替え**: 自然さに改善の余地
- **複雑な指示への従順性**: 高度な指示には改善の余地

---

## 4. MiMo v2.5

**モデルID**: `opencode/mimo-v2.5-free` (HuggingFace: `XiaomiMiMo/MiMo-V2.5`)

### 基本スペック
| 項目 | 値 |
|:---|---:|
| 開発元 | Xiaomi (小米) |
| アーキテクチャ | Sparse MoE + ハイブリッドSWA/GA注意 |
| 総パラメータ | 310B (MiMo-V2.5) |
| 活性パラメータ | 15B |
| コンテキスト長 | 1,000,000 トークン |
| 対応モダリティ | テキスト, 画像, 動画, 音声 |
| 視覚エンコーダー | 729Mパラメータ ViT (28層: 24 SWA + 4 Full) |
| 音声エンコーダー | 261Mパラメータ Audio Transformer (24層: 12 SWA + 12 Full) |
| MTP層 | 3層, 329Mパラメータ |
| 学習データ | 約48Tトークン |
| ライセンス | MIT |

### ベンチマーク（公式 README より、画像参照のため主要評価のみ）

**マルチモーダルベンチマーク**: 強力なマルチモーダル性能を達成（README画像参照）

**コーディング＆エージェントベンチマーク**: 画像参照のため数値は非公開だが、エージェント性能に優れる

### 主な強み
- **唯一のネイティブマルチモーダルモデル**: テキスト + 画像 + 動画 + 音声を統合アーキテクチャで処理
- **超長文対応**: 100万トークン対応（MiMo-V2.5版）
- **効率的な注意機構**: SWA:GA = 5:1 比でKVキャッシュを約6分の1に削減
- **MTP (Multi-Token Prediction)**: 投機的復号による高速推論とRL訓練効率向上
- **強力なエージェント訓練**: SFT + 大規模エージェントRL + MOPD (Multi-Teacher On-Policy Distillation)
- **大規模Pro版**: 1.02T総/42B活性のPro版も存在

### 制限事項
- **コーディング特化モデルと比べるとコード性能は未知数**: 具体的なコーディングベンチマーク数値が公開されていない
- **MiMo-V2-Flashベース**: V2アーキテクチャからのアップグレードであり、完全新規設計ではない
- **310Bと大規模**: ローカル実行には高性能GPUが必要
- **マルチモーダルがメイン**: テキストのみのタスクではより軽量なモデルが効率的かもしれない

---

## 5. Nemotron 3 Ultra

**モデルID**: `opencode/nemotron-3-ultra-free` (HuggingFace: `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B`)

### 基本スペック
| 項目 | 値 |
|:---|---:|
| 開発元 | NVIDIA |
| アーキテクチャ | LatentMoE (Mamba-2 + MoE + Attention ハイブリッド + MTP) |
| 総パラメータ | 550B |
| 活性パラメータ | 55B |
| コンテキスト長 | 1,000,000 トークン |
| 対応言語 | 英語, フランス語, スペイン語, イタリア語, ドイツ語, 日本語, ヒンディー語, 韓国語, ポルトガル語, 中国語 |
| 訓練データ | ~20T トークン (事前訓練) + SFT + RL + MOPD |
| ライセンス | OpenMDW-1.1 |
| リリース日 | 2026年6月4日 |

### ベンチマークスコア（NVIDIA公式）

| ベンチマーク | Nemotron 3 Ultra (550B-A55B) | DS-V4-Flash (284B-A13B) |
|:---|---:|---:|
| **MMLU-Pro** | **86.8** | 86.4 |
| **LiveCodeBench (v6)** | 89.0 | **90.9** |
| **GPQA Diamond (no tools)** | 87.0 | **88.5** |
| **SWE-Bench Verified** | 70.7 | **73.5** |
| **SWE-Bench Multilingual** | 67.7 | **75.0** |
| **Terminal Bench 2.1** | 56.4 | 54.2 |
| **PinchBench** | 90.0 | **91.3** |
| **BrowseComp** | 44.4 | 46.9 |
| **HLE (no tools)** | 26.7 | **32.2** |
| **IMOAnswerBench (no tools)** | 88.6 | **91.1** |
| **Apex-Shortlist (no tools)** | 74.9 | **82.4** |
| **IFBench (prompt loose)** | 81.7 | 82.0 |
| **AA-LCR (長文)** | **65.4** | 62.7 |
| **RULER (1M)** | **94.7** | 87.7 |
| **IOI 2025** | **570.0** | — |
| **MMLU-ProX (多言語平均)** | 83.0 | **84.3** |

### 主な強み
- **最大規模のモデル**: 550B総/55B活性で6モデル中最大
- **MMLU-Pro 86.8**: 6モデル中トップの汎用知識
- **長文コンテキスト性能**: RULER 1M 94.7% は全モデル中最高
- **競技プログラミング**: IOI 2025 で 570点
- **多言語対応**: 10言語サポート
- **先進的アーキテクチャ**: LatentMoE + Mamba-2 + MTP の独自ハイブリッド

### 制限事項
- **コード/エージェント性能はDS V4 Flashに劣る**: SWE-bench, LiveCodeBench で差をつけられている
- **GPU要件が非常に高い**: 最小 8×B200/B300、16×H100、8×H200 が必要
- **OpenMDW-1.1ライセンス**: 利用条件の確認が必要
- **550Bと非常に大規模**: 推論コストが高い
- **DS V4 Flashとの比較**: 多くのベンチマークでDS V4 Flashに及ばないケースが多い（パラメータが多いにも関わらず）

---

## 6. North Mini Code

**モデルID**: `opencode/north-mini-code-free` (HuggingFace: `CohereLabs/North-Mini-Code-1.0`)

### 基本スペック
| 項目 | 値 |
|:---|---:|
| 開発元 | Cohere / Cohere Labs |
| アーキテクチャ | デコーダー型 Transformer スパース MoE |
| 総パラメータ | 30B |
| 活性パラメータ | 3B |
| 専門家数 | 128 専門家 (8 活性化/トークン) |
| 注意機構 | SWA (RoPE) + グローバル注意 (位置なし) = 3:1 比率 |
| コンテキスト長 | 256K (入力) / 64K (出力) |
| ライセンス | Apache 2.0 |
| 訓練手法 | 2段階カスケードSFT → RLVR |

### ベンチマークスコア（Cohere公式、画像参照のため主要評価のみ）

| ベンチマーク | 評価 |
|:---|---:|
| **SWE-Bench Verified** | 強力 (3B活性で競合モデルに匹敵) |
| **SWE-Bench Pro** | 良好 |
| **Terminal-Bench v2** | 良好 |
| **Terminal-Bench Hard** | 良好 |
| **SciCode** | 良好 |
| **LiveCodeBench v6** | 良好 |
| **DeepSWE** | 良好 |

### 主な強み
- **驚異的な軽量性**: わずか **30B総/3B活性** でコードエージェントタスクに対応
- **コード特化**: コード生成・エージェントSEに最適化
- **インターリーブ思考**: 思考内容とツール呼び出しをインターリーブ可能
- **Apache 2.0ライセンス**: 最も制限の少ないオープンライセンス
- **OpenCodeとの親和性**: OpenCode内でローカルvLLMサーバー経由での使用ガイドあり
- **Cohere Melody**: ツール呼び出しパーサーによる正確なレスポンス解析

### 制限事項
- **コード以外の汎用タスクには不向き**: 汎用知識・推論のベンチマーク未報告
- **コンテキスト長が他モデルより短い**: 256K（他は1M）
- **粗い量子化での性能劣化の可能性**: GGUF等の軽量量子化時の評価データ不足
- **比較的新しいモデル**: エコシステムの成熟度が低い可能性
- **出力長制限**: 64Kの出力制限あり

---

## 総合比較チャート

### パラメータ効率（性能/活性パラメータ比の目安）

| モデル | 活性パラメータ | コード性能指標 | 効率性評価 |
|:---|---:|:---|:---|
| **North Mini Code** | **3B** | コードエージェント強力 | ⭐⭐⭐ 驚異的 |
| **Ling 3.0 Flash** | 7.4B | エージェント競合レベル | ⭐⭐⭐ 非常に高い |
| **Laguna S 2.1** | 8.5B | SWE-ML 78.5% | ⭐⭐⭐ 非常に高い |
| **DeepSeek V4 Flash** | 13B | LCB 88.4, SWE 78.6% | ⭐⭐⭐ 高い |
| **MiMo v2.5** | 15B | マルチモーダル強力 | ⭐⭐ 普通 |
| **Nemotron 3 Ultra** | 55B | MMLU-Pro 86.8 | ⭐⭐ 低い（大規模） |

### 用途別おすすめモデル

| 用途 | 推奨モデル | 理由 |
|:---|---:|:---|
| **汎用コード生成** | DeepSeek V4 Flash | LiveCodeBench 88.4, HumanEval 69.5% |
| **エージェントコーディング** | Laguna S 2.1 | SWE-bench Multilingual 78.5% (最高) |
| **軽量・高速エージェント** | Ling 3.0 Flash | 340 tok/s, 7.4B活性 |
| **マルチモーダル処理** | MiMo v2.5 | 唯一の画像+動画+音声対応 |
| **高難易度推論** | Nemotron 3 Ultra | 競プロIOI 570点, MMLU-Pro 86.8 |
| **超軽量コード/学習用** | North Mini Code | 3B活性でコードエージェント性能、Apache 2.0 |
| **コスパ最重視** | DeepSeek V4 Flash | 13B活性でフロンティア級性能、無料利用可能 |

---

## 参照ソース一覧

- DeepSeek V4 Flash: [HuggingFace Model Card](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash) — 確度高
- DeepSeek V4 技術報告書: [arXiv 2606.19348](https://arxiv.org/abs/2606.19348) — 確度高
- Laguna S 2.1: [HuggingFace Model Card](https://huggingface.co/poolside/Laguna-S-2.1-NVFP4) — 確度高
- Ling 2.6 Flash: [HuggingFace Model Card](https://huggingface.co/inclusionAI/Ling-2.6-flash) — 確度高
- Ling & Ring 2.6 技術報告書: [arXiv 2606.15079](https://arxiv.org/abs/2606.15079) — 確度高
- MiMo V2.5: [HuggingFace Model Card](https://huggingface.co/XiaomiMiMo/MiMo-V2.5) — 確度高
- Nemotron 3 Ultra: [HuggingFace Model Card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16) — 確度高
- North Mini Code: [HuggingFace Model Card](https://huggingface.co/CohereLabs/North-Mini-Code-1.0) — 確度高
- North Mini Code ブログ: [Cohere Blog](https://huggingface.co/blog/CohereLabs/introducing-north-mini-code) — 確度高

---

## 付録：調査プロセス

1. HuggingFace API で各モデルの実体を特定
2. 各モデルのHuggingFace READMEから公式ベンチマークデータを収集
3. DeepSeek V4とNemotron 3 Ultraは詳細な数値表が利用可能
4. MiMo V2.5, North Mini Code, Ling 2.6 Flash は画像ベースのチャートが中心で、一部数値はREADMEテキストからのみ抽出
5. 注: OpenCode上の「Ling 3.0 Flash」はHuggingFace上では Ling-2.6-flash として公開。バージョン番号の違いはマーケティング上の理由と推定
