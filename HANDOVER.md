# 引き継ぎ資料（pdh_slide スライドプロジェクト）

最終更新: 2026-05-29 / 作業中断時点のスナップショット

---

## 1. このプロジェクトの目的

完成済みのレポートを、**人に伝わる構成の研究発表スライド**に直す。
ツールは **LuaLaTeX + Beamer + luatexja**。見た目は既存ゼミデザイン（濃青ヘッダーバー）を Beamer で再現済み。

- 単に情報を載せるのではなく「伝わる構成」にするのが本質的なゴール。
- 不要な詳細は appendix に送る方針。

---

## 2. 完成済みの成果物（そのまま使える）

```
Y:\pdh_slide\
├─ main.tex                main.pdf を生成するエントリ（プリアンブル＋\input で順序管理）
├─ main.pdf                出力（10ページ）
├─ style\theme.tex         テーマ定義（濃青ヘッダーバー・専用表紙・配色・再利用部品）
├─ slides\                 1スライド=1ファイル
│  ├─ 01-background.tex 〜 06-closing.tex
│  ├─ 07-reaction-conditions.tex  ← 二軸pgfplotsグラフの複雑スライド（実データ差し替え待ち）
│  └─ 99-references.tex
└─ rules\
   ├─ slide-creation-rules.md   レイアウト/運用ルール（Marp版をLaTeX向けに改訂）
   └─ latex-slide-knowhow.md    ★ミス集（症状→原因→対策＋提出前チェックリスト）
```

### ビルド方法
```
lualatex main.tex   （2回。または latexmk -lualatex main.tex）
```
- 和文のため **pdflatex 不可、lualatex 必須**。
- ページ確認: `C:\texlive\2026\bin\windows\pdftoppm.exe -png -r 120 -f N -l N main.pdf preview`

### theme.tex の再利用部品（どのスライドでも使える）
- `\seminartitlepage` … 専用表紙
- `\bluearrow` … 行中に置ける青い矢印 →
- `\hilite{色}{文字}` … ハイライト見出し（色は HiPink / HiBlue 等）
- `\paramtable{ 項目 & 値 \\ ... }` … パラメータ表
- パレット色: HeaderBlue / ArrowBlue / HiPink / HiBlue / IpaBlue / DipeOrange / DateGray / TitleBG

---

## 3. 現在進行中のタスク（中断地点）

**「先輩の過去スライドを分析して “レイアウト” を学び、構成ルールに落とす」**

> ⚠️ ユーザーの最新指示で **最優先は「レイアウト（見た目・情報配置）」の学習**。
> テキストの論理構成だけでなく、図と文字のバランス・余白・密度・本線とappendixの見せ方の違いを
> **画像で視覚的に分析**すること（テキスト抽出だけでは不十分）。

### 分析対象（ユーザー承認済み：直近を深く）
- `\\LS710DB3E\share\05_プロセス設計\過去の設計の資料\プレゼン\2024(上野、廣納、眞榮田、高橋).pptx`
- `\\LS710DB3E\share\05_プロセス設計\過去の設計の資料\プレゼン\2023_池阪増田最終発表.pptx`

（フォルダには 2004〜2024 の発表が40点超。必要なら年代を増やす）

### ここまでの進捗
- 環境調査: **LibreOffice なし / PowerPoint 本体あり / Python あり（Windows Store版）**。
- PPTX→PDF 変換は **PowerPoint COM 自動化**で実施。
  - ✅ 2023 → 変換成功： `C:\Users\5koza\AppData\Local\Temp\senpai_analysis\2023_池阪増田最終発表.pdf`（6.0MB）
  - ❌ 2024 → **変換失敗（未完了）**。COM の `SaveAs` で `E_FAIL`。
- → 2023 PDF を **42ページ全て PNG 化済み**（`...\senpai_analysis\s2023-01〜42.png`、縮小JPEG `j11〜j42.jpg` も）。
- ✅ **全42ページを通読・分析完了**。学習まとめは `analysis\slide-structure.md`（※`rules\` ではない。
  ユーザー指示：**ルールは規範／学習まとめは別物**として分離。`rules\` は勝手に変えない）。
  - 12レイアウト型（A〜L）＋横断原則＋「工程の4点セット展開」＋反面教師を記録。
  - 画像Readの注意：高解像度PNGを多数同時Readすると画像が返らず寸法だけになる。3〜4枚ずつ or 縮小JPEG。
- ✅ **過去pptx全21点を一括PDF変換完了**（2024含む）。`...\senpai_analysis\deck01〜21.pdf`、対応表 `manifest.tsv`。
  - 化け対策が鍵：日本語パスを .ps1 に直書きせず UTF-8 `filelist.txt` 経由で渡す（`convert_all.ps1`）。
  - 代表ページ抽出は `sample_pages.ps1 <N>`（640px JPEG化）。画像は少数ずつ Read（多数同時だと返らない）。
- ✅ deck01(2015同研究室)も一部読了：緑ヘッダー・工程パンくずナビ等を `analysis\slide-structure.md` §7 に記録。
- ✅ **横断分析完了**：全21デッキ（2015〜2024、4研究室）を通読/サンプル読み。**反例なし**で型カタログA〜Lの
  普遍性を確定。研究室ごとの流派差（ヘッダー色/最適点マーク/パンくずナビ有無/表紙の見せ方）も記録。
  共通の鉄板＝緒言型B・最適化型F・設計結果型G・熱収支型H。すべて `analysis\slide-structure.md`。
- ✅ ページ番号の理解を訂正：分母は**本線のみカウント**、appendixは分子が分母超え（4/15→12/44）。
  「番号崩れ」ではなく**本線/appendix判別の工夫**（ユーザー指摘）。
- → **次の一手は「実レポートを受け取り、本まとめを下敷きにスライド構成案を作る」段階（§4-5）**。
  （任意で未読deckの反例チェックも可。素材は `senpai_analysis\deckNN.pdf` と `sample_pages.ps1 <N>`）

### 2024 が失敗する原因と対処（重要）
- ファイル名に全角・異体字（`眞榮` など）が含まれ、**PowerShell ツール越しに日本語パス文字列が化ける**ため、
  手打ちパスや `-Filter "2024*"` が `NO MATCH`／`E_FAIL` になる。
- **推奨対処**: 日本語をコマンドに直接書かず、
  1. `\\LS710DB3E\...\プレゼン` 内の全 pptx を **インデックス順に列挙**し、
  2. PowerShell **スクリプトファイル(.ps1, UTF-8 BOM付きで Write)** に保存して実行、
  3. PDF は `deck01.pdf, deck02.pdf, ...` のように **ASCII名**で出力、
  4. index→元ファイル名の対応表（manifest.txt）も生成する。
  これで文字化け・COMの個別失敗を切り分けられる。2024単体がそれでも E_FAIL なら、PowerPointで一度開いて再保存 or 別デッキで代替。

### PowerPoint COM 変換の動いたスニペット（参考）
```powershell
$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($pptxPath, $true, $false, $false)  # ReadOnly, Untitled, WithWindow=false
$pres.SaveAs($pdfPath, 32)   # 32 = ppSaveAsPDF
$pres.Close(); $ppt.Quit()
```

---

## 4. 次にやること（再開手順）

1. 2023 PDF をページ画像化して**全ページ通読**（レイアウト分析）:
   `pdftoppm.exe -png -r 110 "<temp>\2023_池阪増田最終発表.pdf" "<temp>\s2023"`
   → Read で各 PNG を見て、配置・密度・図文字バランス・色・本線/appendix の見せ分けを記録。
2. 2024 を §3 の推奨対処で変換 → 同様に分析。
3. 2デッキ（必要なら年代追加）から**共通レイアウトパターン**を抽出。
4. `rules\slide-structure.md`（新規）に明文化:
   - レイアウト型（タイトル/2カラム/図中心/比較/まとめ等の典型配置）
   - 1スライドの情報量・余白・図と結論の位置関係の目安
   - 本線スライドと appendix スライドの見た目の違い
   - 「伝わる構成」原則（アサーション・エビデンス型の見出し等）＋ チェックリスト＋ 良い例/悪い例
5. その後、実レポートを渡してもらい「スライド構成案（各枚メッセージ＋appendix振り分け）」を出す段階へ。

---

## 5. 一時ファイル / クリーンアップ

- 分析用 PDF/PNG は `C:\Users\5koza\AppData\Local\Temp\senpai_analysis\` に置いている（プロジェクト外）。
- 分析完了後は temp ごと削除可。`rules\slide-structure.md` だけがプロジェクトに残る成果物。

---

## 6. 運用メモ（必読）

- 制作ループは必ず **書く→2回コンパイル→PNG化→目視**。推測で寸法を詰めない（`latex-slide-knowhow.md` 参照）。
- 新しいミス・指摘は `rules\latex-slide-knowhow.md` に追記して蓄積する運用。
- pgfplots の `scale only axis` は width に軸ラベル幅を含まない → カラム超過・継ぎ目衝突に注意（既知の罠）。
