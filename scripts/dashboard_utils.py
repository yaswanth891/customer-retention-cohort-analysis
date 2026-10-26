"""Render single-file, offline Plotly dashboards."""
from pathlib import Path
import plotly.io as pio
CSS = """
:root{--bg:#0b1324;--card:#17223a;--line:#2a3953;--txt:#f2f6ff;--dim:#a9b9d4;--accent:#32d7bd}
*{box-sizing:border-box}body{font-family:Inter,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;background:var(--bg);color:var(--txt);margin:0;line-height:1.5}
main{max-width:1160px;margin:0 auto;padding:44px 28px 70px}.eyebrow{color:var(--accent);letter-spacing:.16em;text-transform:uppercase;font-size:12px;font-weight:800}
h1{font-size:34px;letter-spacing:-.03em;margin:9px 0}h2{font-size:19px;margin:0 0 12px}p{color:var(--dim);margin:5px 0 18px}.desc{max-width:900px}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;margin:32px 0}.metric{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px}
.metric strong{display:block;font-size:30px;margin-top:6px;color:var(--txt)}.metric span{font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--dim)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:15px;min-height:360px}
.panel.wide{grid-column:1/-1}.foot{border-top:1px solid var(--line);padding-top:20px;margin-top:30px;font-size:13px;color:var(--dim)}
.callout{background:#12332e;border:1px solid #286a60;color:#d4fff4;padding:20px;border-radius:16px;margin:18px 0}
@media(max-width:800px){main{padding:24px 12px}.grid{grid-template-columns:1fr}.panel.wide{grid-column:auto}h1{font-size:28px}}
"""

def dashboard(output, name, subtitle, kpis, charts, finding, footnote):
    embeds = []
    for i, (title, fig) in enumerate(charts):
        fig.update_layout(template='plotly_dark',paper_bgcolor='#17223a',plot_bgcolor='#17223a',
                          font=dict(color='#dce6f9',size=12),margin=dict(l=50,r=25,t=30,b=55),
                          height=330,legend=dict(orientation='h',y=-.25))
        html = pio.to_html(fig, full_html=False,include_plotlyjs='inline' if i == 0 else False,
                           config={'displayModeBar': False,'responsive':True})
        klass = 'panel wide' if len(charts)%2==1 and i==len(charts)-1 else 'panel'
        embeds.append(f'<section class="{klass}"><h2>{title}</h2>{html}</section>')
    metric_html = ''.join(f'<div class="metric"><span>{lab}</span><strong>{val}</strong></div>' for lab,val in kpis)
    content = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
    <title>{name}</title><style>{CSS}</style></head><body><main>
    <div class="eyebrow">Product analytics portfolio</div><h1>{name}</h1><p class="desc">{subtitle}</p>
    <div class="metrics">{metric_html}</div><div class="grid">{''.join(embeds)}</div>
    <div class="callout"><b>Product decision / next step</b><div>{finding}</div></div>
    <div class="foot">{footnote}</div></main></body></html>'''
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(content,encoding='utf-8')
