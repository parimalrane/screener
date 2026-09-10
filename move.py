import os, shutil
os.makedirs('docs', exist_ok=True)
os.makedirs('output', exist_ok=True)
moves = {
    '20260904_stocks.csv': 'data/20260904_stocks.csv',
    'ignored_tickers.txt': 'data/ignored_tickers.txt',
    'screener_results.csv': 'output/screener_results.csv',
    'screener_4h_BE_results.csv': 'output/screener_4h_BE_results.csv',
    'screener_4h_BU_results.csv': 'output/screener_4h_BU_results.csv',
    'ASTA_Taxonomy.md': 'docs/ASTA_Taxonomy.md',
    'HANDOVER.md': 'docs/HANDOVER.md'
}
for src, dst in moves.items():
    if os.path.exists(src):
        if os.path.exists(dst): os.remove(dst)
        shutil.move(src, dst)
