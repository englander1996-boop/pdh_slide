# このプロジェクトは和文（luatexja）のため LuaLaTeX 必須。
# latexmk / エディタ（LaTeX Workshop 等）がデフォルトの latex ルールで
# 走ると「This package requires Lua(HB)(La)TeX」で失敗するので、
# 常に LuaLaTeX を使うようここで固定する。
$pdf_mode = 4;          # 4 = lualatex で PDF を生成
$lualatex = 'lualatex -interaction=nonstopmode -synctex=1 %O %S';
$out_dir  = '.';
