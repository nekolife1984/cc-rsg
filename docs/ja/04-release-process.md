# リリース手順

## バージョニング

このプロジェクトは **Semantic Versioning**（`MAJOR.MINOR.PATCH`）に従います：

| 更新 | タイミング | 例 |
|------|-----------|----|
| **MAJOR** | 破壊的変更、安定版リリース（v1.0） | `v0.8.0` → `v1.0.0` |
| **MINOR** | 新機能、非破壊的拡張 | `v0.7.0` → `v0.8.0` |
| **PATCH** | バグ修正、ホットフィックス | `v0.8.0` → `v0.8.1` |

プレリリース接尾辞：`v0.8.0-alpha.1`、`v0.8.0-beta.1`

## 手順

### 1. CHANGELOGの準備

`CHANGELOG.md` が前回リリース以降の全変更を反映していることを確認します。形式は [Keep a Changelog](https://keepachangelog.com/ja/) に従います：

```markdown
## [v0.8.0] - 2026-07-29

### Added
- feat: Question Bank custom categories UI (#31)
- feat: Kotlin extractor for source_map_v2 (#28)

### Changed
- chore: upgrade pytest to 8.x
```

### 2. README Roadmapの更新

`README.md` の `## Status` セクションにある Roadmap で、完了した項目を `~~done~~` にします。次の予定項目を backlog から移動します。

### 3. Zenodoプレプリントの更新（該当時）

リリースに設計上の大きな変更や新しい研究内容が含まれる場合、Zenodo プレプリントを更新します：

- プレプリント： https://zenodo.org/records/20541685
- 更新タイミング：設計思想や実装判断が実質的に変わったとき
- 不要な場合：バグ修正、軽微な機能追加、ドキュメントのみの更新

### 4. タグ作成とプッシュ

```bash
# main上で、PRマージ後
git tag -a v0.8.0 -m "v0.8.0 — UI for custom categories"
git push origin v0.8.0
```

### 5. GitHub Release の作成

```bash
gh release create v0.8.0 \
  --title "v0.8.0 — UI for custom categories" \
  --notes "CHANGELOG.md を参照"
```

または手動で https://github.com/nekolife1984/specback/releases/new から作成します。

## ホットフィックスリリース

リリース済みバージョンへの緊急修正：

```bash
git checkout -b fix/hotfix-crash main
# 修正 → コミット → PR → squash merge → main
git tag -a v0.8.1 -m "v0.8.1 — crash fix"
git push origin v0.8.1
```

## リリース頻度

固定スケジュールはありません。以下のタイミングでリリースします：

- 意味のある機能マイルストーンに到達したとき
- 重要なバグが修正されたとき
- 破壊的変更の調整が必要なとき

現在の軌道：`v0.7.x` → `v0.8.x`（機能追加） → `v1.0`（実プロジェクト適用後の安定版）

## リリースチェックリスト

- [ ] CHANGELOG.md を更新した
- [ ] README Roadmap を更新した（完了項目に取り消し線）
- [ ] `skills/specback/SKILL.md` のバージョン文字列を更新した（該当時）
- [ ] Zenodo プレプリントを更新した（設計変更時のみ）
- [ ] タグを作成してプッシュした
- [ ] GitHub Release を作成した
